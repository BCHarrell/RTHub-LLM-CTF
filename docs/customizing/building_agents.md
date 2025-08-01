# Adding / Modifying Agents
Similar to tools, you can add new agents by simply creating a new Python
file, put it in `core/agents/`. There's an example in `core/agents/agent.example`.

New agents should subclass the `RTHubAgent` class from `core.backend.models`,
which requires you implement a single function 
(`async def handle_chat(self, user_msg: str) -> str:`).

A basic init function is supplied in the parent class that covers Pydantic-AI
supported providers + local Ollama and pulls the system prompt from the config
file. If you want to add other instructions/define a different provider,
you'll need to add your own init.

An example where you want to do that is to use other remote OpenAI compatible
providers, where some additional setup (a specific Provider object) is required.
Again, this only applies to remote providers. Local is good to go.

[Pydantic-AI OpenAI-compatible model docs](https://ai.pydantic.dev/models/openai/#openai-compatible-models)

:warning: If you define your own custom agent + initialization function, make
sure you add the system prompt with the `@agent.instructions` decorator, not
`@agent.systemprompt`. Once the history token limit is reached, the oldest
message is going to be popped from the deque, which means you'll lose the
system prompt. `@agent.instructions` are always included when sending to the
LLM, so you'll ensure the system prompt is always present this way.

You can make an agent without the Pydantic-AI framework, but the backend uses
the ModelRequest/ModelResponse/Usage classes from Pydantic to track stuff,
so you'll need to modify other things on the backend if you do
(so it's not recommended :D).

Pydantic-AI supports most major LLM providers. See their docs for specific model
creation and calling.

[Pydantic-AI Docs](https://ai.pydantic.dev/agents/)
