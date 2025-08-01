from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from quart import session
from core.backend.config import config

class ChatRequest(BaseModel):
    message: str

class RTHubAgent(Agent):
    agent = Agent("test") # Placeholder for the base agent

    def __init__(self, model: str, tools=[], base_url: str = None):
        """ 
        This is a basic init using Pydantic-AI for their supported
        providers + local Ollama
        """

        # One of the remote Pydantic-compatible providers
        if not base_url:
            # Add system_prompt="foo" here if you don't want a dynamic prompt
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
        # use 'system_prompt'.
        @agent.instructions
        def add_challenge_prompt() -> str:
            challenge_set = session.get("challenge")
            return config.CHALLENGE_SETS[challenge_set]["prompt"]
        
        self.agent = agent

    def  handle_chat(self, user_msg: str) -> str:
        """
        Handles the chat message from the user.
        This method should be overridden by subclasses to implement specific agent behavior.
        """
        raise NotImplementedError("Subclasses must implement handle_chat method")

    # Pass everything else through to the base Pydantic agent
    def __getattr__(self, name):
        return getattr(self.agent, name)