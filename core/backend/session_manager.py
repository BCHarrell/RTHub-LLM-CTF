import os
from quart import session
from collections import deque
import time
from pydantic_ai.messages import ModelResponse, ModelRequest

from core.backend.config import config
from core.backend.helpers import get_initial_objective_status


class TokenLimitedHistory:
    """
    A class to manage chat history with a token limit to avoid situations where
    the user's rate limit is hit due to excessive history size. For multiple
    people this may be important, for a single player you can set this to 
    something much higher in config.yaml
    """
    def __init__(self, max_history_tokens=128000, model="gpt-4"):
        self.max_tokens = max_history_tokens
        self.history = deque()
        self.total_tokens = 0

    def _count_tokens(self, messages: list):
        """ Counts the tokens per run (requires Pydantic ModelResponse)"""
        return sum(msg.usage.total_tokens for msg in messages 
                   if isinstance(msg, ModelResponse))
    
    def _strip_instructions(self, messages: list):
        """ 
        Removes the instructions (system prompt) from the messages to save on 
        local memory if you have a long chat history. Pydantic still sends the 
        instructions to the model with each request.
        """
        cleaned_messages = []
        for msg in messages:
            if isinstance(msg, ModelRequest):
                msg.instructions = None
            cleaned_messages.append(msg)
        return cleaned_messages

    def add_message(self, new_messages: list):
        """
        Adds messages from a run to the history, counting their tokens and 
        ensuring the total

        Messages are added as batches (request, response, tool calls) because 
        Pydantic only includes token usage for responses. This also helps keep 
        consistency if a tool call was made for OpenAI-compatible models, where 
        the history cannot start with a tool response. The entire exchange will 
        be popped off the history when the limit is reached.
        """
        cleaned_messages = self._strip_instructions(new_messages)
        tokens = self._count_tokens(cleaned_messages)
        self.history.append((new_messages, tokens))
        self.total_tokens += tokens

        # Trim old messages until within token limit
        while self.total_tokens > self.max_tokens and self.history:
            self._pop_message()
        
    def _pop_message(self):
        """ Pops the oldest run messages to stay below history limits """
        _, removed_tokens = self.history.popleft()
        self.total_tokens -= removed_tokens

    def get_history(self):
        hx = []
        for msg, _ in self.history:
            hx.extend(msg)
        return hx

    def reset(self):
        """Resets the history and history token count (user action)."""
        self.history.clear()
        self.total_tokens = 0

class SessionManager:
    """
    Manages the user's session, which tracks history and ojectives.
    Histories are lost on server shutdown, objective status is stored
    as a session cookie.
    """
    def __init__(self):
        self.HISTORIES = {}  # dictionary to store session histories
        # {session_id: {"requests": deque([timestamp, ...]), 
        #  "tokens": deque([(timestamp, token_count), ...])}}
        self.RATE_LIMITS = {}

    def init_session(self, session_id: str, username: str):
        """
        Initializes a user session by creating a directory for the user and 
        setting up initial session data. If the user_data file is cleared, the 
        session is no longer valid.
        """
        user_dir = os.path.join(config.USER_DATA_DIR, session_id)
        os.makedirs(user_dir, exist_ok=True)

        # Get the objectives
        objective_status = get_initial_objective_status()

        session["session_id"] = session_id
        session["username"] = username
        session["challenge"] = "set-1"
        session["objective_status"] = objective_status

        session.permanent = config.PERSIST_SESSION

        self.HISTORIES[session_id] = {
            "set-1": TokenLimitedHistory(config.USER_MAX_HISTORY_LENGTH),
            "set-2": TokenLimitedHistory(config.USER_MAX_HISTORY_LENGTH),
            "set-3": TokenLimitedHistory(config.USER_MAX_HISTORY_LENGTH)
        }

    ###########
    # HISTORY #
    ###########
    def get_session_history(self) -> dict:
        if session["session_id"] not in self.HISTORIES:
            return []

        return self.HISTORIES[session["session_id"]][session["challenge"]].get_history()

    def update_session_history(self, message: dict):
        self.HISTORIES[session["session_id"]][session["challenge"]].add_message(message)

    def clear_session_history(self) -> dict:
        self.HISTORIES[session["session_id"]][session["challenge"]].reset()
        return self.HISTORIES[session["session_id"]]
    
    def get_history_length(self) -> int:
        if session["session_id"] not in self.HISTORIES:
            return 0

        return self.HISTORIES[session["session_id"]][session["challenge"]].total_tokens

    ###############
    # OBJECTIVES #
    ###############
    def update_session_challenge_set(self, challenge: str):
        session["challenge"] = challenge

    def mark_objective_complete(self, objective_id: str, challenge: str):
        for obj in session["objective_status"].get(challenge, []):
            if obj.get("id") == objective_id:
                obj["completed"] = True
                session.modified = True
                break

    ##########
    # LIMITS #
    ##########
    def check_limits(self) -> dict:
        """ 
        Checks whether the user has hit their defined rate limits 
        (requests and tokens per minute)
        """
        session_id = session["session_id"]
        limits = self.RATE_LIMITS.get(session_id, {
            "requests": deque(),
            "tokens": deque()
        })

        # Clear old entries
        self._clear_limits(limits)

        # Count within window
        request_count = len(limits["requests"])
        token_count = sum(count for _, count in limits["tokens"])

        # Save cleaned version
        self.RATE_LIMITS[session_id] = limits

        # check if limits exist
        max_req = config.USER_RPM_LIMIT if config.USER_RPM_LIMIT is not None else 10000000
        max_tokens = config.USER_TPM_LIMIT if config.USER_TPM_LIMIT is not None else 100000000

        return {
            "requests_exceeded": request_count >= max_req,
            "tokens_exceeded": token_count >= max_tokens,
            "tokens_remaining": max_tokens - token_count
        }

    def increment_usage(self,token_count: int):
        now = time.time()
        limits = self.RATE_LIMITS.setdefault(session["session_id"], {
            "requests": deque(),
            "tokens": deque()
        })

        limits["requests"].append(now)
        limits["tokens"].append((now, token_count))

    def _clear_limits(self, limits: dict):
        """ Removes requests and tokens on a rolling 60 second window"""
        now = time.time()
        
        # Remove entries older than the rolling window
        while limits["requests"] and now - limits["requests"][0] > 60:
            limits["requests"].popleft()

        while limits["tokens"] and now - limits["tokens"][0][0] > 60:
            limits["tokens"].popleft()


    def get_usage(self) -> dict:
        """
        Returns the current usage for the user session.
        """
        # refresh limits
        self.check_limits()

        limits = self.RATE_LIMITS.get(session["session_id"], {
            "requests": deque(),
            "tokens": deque()
        })

        return {
            "requests": len(limits["requests"]),
            "tokens": sum(count for _, count in limits["tokens"])
        }
    
session_manager = SessionManager()