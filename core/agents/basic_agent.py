from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits
from quart import session

from core.backend.models import RTHubAgent
from core.backend.config import config
from core.backend.session_manager import session_manager
from core.guards.basic_llm_guard import basic_guard as guard
from core.guards.basic_firewall import basic_firewall as firewall
from core.backend.helpers import process_output_for_flags


class BasicAgent(RTHubAgent):

    def __init__(self, model: str, tools=[], base_url: str = None):
        # One of the remote Pydantic-compatible providers
        if not base_url:
            agent = Agent(model=model, tools=tools)
        # Local Ollama (presumes no API key is needed)
        else:
            pydantic_model = OpenAIModel(
                model_name=model,
                provider=OpenAIProvider(base_url=base_url),
            )
            agent = Agent(model=pydantic_model, tools=tools)

        # This allows changing the prompt based on the session challenge set
        # vs. defining at agent creation. 'instructions' are always sent - don't
        # use 'system_prompt'. After a redesign where each challenge set gets its
        # own agent, this isn't as useful, but if I add a settings page it will
        # be relevant again.
        @agent.instructions
        def add_challenge_prompt() -> str:
            challenge_set = session.get("challenge")
            return config.CHALLENGE_SETS[challenge_set]["prompt"]
        
        self.agent = agent
    
    async def handle_chat(self, user_msg: str) -> str:
        limits = session_manager.check_limits()
        # Don't allow the chat to go through if the limit has been hit or there
        # aren't enough tokens to cover the history length. This is a rough check
        if (limits["requests_exceeded"] or 
            limits["tokens_exceeded"] or 
            limits["tokens_remaining"] < (session_manager.get_history_length() + 
                                          config.MAX_OUTPUT_TOKENS)):
            return ("Not enough tokens or requests remaining. Please wait 15-20s "
                    "before trying again. You can also clear your chat history "
                    "to free up tokens for the future.")

        # Check the input against the guard, if applicable
        if config.CHALLENGE_SETS[session["challenge"]]["guard-type"]:
            guard_check = self.process_message(direction="input", prompt=user_msg)
            if not guard_check["is_allowed"]:
                return guard_check["message"]

        # Handle the chat + update history/usage
        result = await self.agent.run(
            user_msg,
            message_history=session_manager.get_session_history(),
            usage_limits=UsageLimits(
                response_tokens_limit=config.MAX_OUTPUT_TOKENS))
        session_manager.update_session_history(result.new_messages())
        session_manager.increment_usage(result.usage().total_tokens)

        # Check the output against the guard
        if config.CHALLENGE_SETS[session["challenge"]]["guard-type"]:
            guard_check = self.process_message(direction="output", 
                                               model_response=result.output)
            if not guard_check["is_allowed"]:
                return guard_check["message"]

        # Process the output to add flags if relevant
        return process_output_for_flags(result.output)


    def process_message(self, direction: str = "input", prompt: str = "", 
                        model_response: str = "") -> dict:
        """
        Uses the configured guard to check the input or output against
        the rules defined in the guard.
        """
        guard_type = config.CHALLENGE_SETS[session['challenge']]['guard-type']
        match config.CHALLENGE_SETS[session["challenge"]]["guard-type"]:
            case "llm-guard":
                if not guard.is_allowed(prompt=prompt,
                                            model_response=model_response,
                                            direction=direction):
                    return {"is_allowed": False,
                            "message": guard.get_rejection_message(direction)}
            case "firewall":
                if direction == "input":
                    if not firewall.is_allowed(message=prompt,
                                                    direction=direction):
                        return {"is_allowed": False,
                                "message": firewall.get_rejection_message(direction)}
                else:
                    if not firewall.is_allowed(message=model_response,
                                                    direction=direction):
                        return {"is_allowed": False,
                                "message": firewall.get_rejection_message(direction)}

        return {"is_allowed": True}

    # Pass everything else through to the base Pydantic agent
    def __getattr__(self, name):
        return getattr(self.agent, name)