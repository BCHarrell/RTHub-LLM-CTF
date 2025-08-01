# Running the Game

## Basic Usage
You'll need a few things at a minimum to get going, or you can yolo it but
I'm not responsible for it failing to work if you do. If you want some additional
ideas, see the advanced usage section.

The basic configuration file is a slightly modified version of the one used
at DEF CON. If you want the one used in DEF CON, grab the config and tools from 
`game/library/defcon`; put the config as `config.yaml` in the root and the tools
in `game/tools` (as of right now, the tools are all there already).

Note: The tools/prompts were tested most with OpenAI GPT-4o-mini; prompts
or tool descriptions may require tweaking with other models to work best. E.g.,
older Claude models are much more suspicious by default.

### 1. .env file
If you haven't already, copy `.env.example` to `.env` in the root of the
application. Then fill in API keys for any provider(s) you want to use.

The basic agent provided with the app uses [Pydantic-AI](https://ai.pydantic.dev/agents/) 
for the agent framework. As of this release, Pydantic-AI supports the following
[providers](https://ai.pydantic.dev/models/)

* OpenAI
* Anthropic
* Gemini
* Groq
* Mistral
* Cohere
* Bedrock

Note that not all models from a given provider support tool calls, so choose
the model wisely. To see available models, see the [Pydantic](https://ai.pydantic.dev/api/models/base/) 
docs.

In addition to online providers, the basic agent will also support OpenAI-compatible
local models. This has only been tested with Ollama, but you can supply the URL
for your local LLM (reminder: must be OpenAI-compatible) in the `config.yaml` file.

Other LLM providers like DeepSeek, OpenRouter, etc. are supported by Pydantic-AI
but they require some additional configuration. It's pretty easy to do, just
see the Pydantic [documentation])(https://ai.pydantic.dev/models/openai/#openai-compatible-models)
for the required `OpenAIProvider` instantiation and either add your own agent 
or drop the code into `core/agents/basic_agent.py`.

Note: Bedrock hasn't been tested but *should* work if you have the right AWS
credentials in the .env. List the model in the config file like so:

```yaml
llm-model: 'bedrock:anthropic.claude-3-sonnet-20240229-v1:0'
```

To add your own agent, see the [Building Your Own Agent](customizing/building_agents.md)
docs.

### 2. `config.yaml` changes
`config.yaml` in the root of the application folders controls a lot of the app.
I recommend seeing [config file docs](config_explanation.md), but here are a few
key areas to check:

1. Under `game-settings`, ensure you configure any API limits you have. Also
pay attention to the history length (`user-max-history-token-length`) if you're
limited on tokens. If you turn this up too high and don't clear your history
periodically, you can end up burning a lot of tokens each request. If you're 
hosting this for multiple people over the internet, make sure you add
a registration code so randos can't steal all your credits.

2. Under `challenge-sets`, set the `llm-model` to whatever you're using in the
format `provider:model` to comply with Pydantic-AI syntax. See their docs (linked
above) for examples. If you're using a local OpenAI-compatible model, add the
`base-url` as well. **If you're using Docker:** `localhost` becomes 
`host.docker.internal`.

3. Under `challenge-sets`, add any additional difficulty modifiers under `guard-type`.
The BasicAgent supports `firewall`, `llm-guard`, or leave it empty. This will
add input/output checks of various difficutly (`llm-guard` is harder)

:warning: If you plan to use a language other than English, you'll want to modify
the guards included with the platform. The checks are all in English, and the
`llm-guard` implementation specifically restricts input/output to English.
[Guard docs.](customizing/modifying_guards.md)

:warning: x2 - `llm-guard` is still pretty new. You may encounter some funny
scenarios where it thinks you're trying to attack it with a benign query, but
sometimes that's how it goes in real scenarios.

## Advanced Usage
I've tried to build this in such a way that you can add tools, other agents,
or additional functionality without needing to do too much to the rest of the
app. See the [customizing](./customizing/) documentation for more. But in the interim, here 
are some thoughts if you want to do your own thing.

### Adding Tools
If you want to add tools, simply drop a new Python file into the `game/tools`
folder. These tools will get loaded on server startup, but you'll need to follow
a few things. See the [Adding Tools](customizing/adding_tools.md) documentation 
for more specifics.

A few considerations:
1. You can put multiple tools in a single file, it might help to cluster
tools by objective, that way they're all in one place.
2. Don't have too many tools. You can probably get 10-15 tools with no issue,
but if you start adding more you'll probably start seeing performance degradation
and it'll chew up a lot of tokens per request, too. If you don't plan to work
on a specific objective or use certain tools, consider moving them to `game/library`
for later.

### Adding Agents
If you want to add an agent of your own, simply drop a new agent in the
`core/agents` folder. As with tools, there are some design considerations
covered in [Adding Agents](customizing/building_agents.md) that you'll need to 
follow to link up with the rest of the app.

You can have up to three agents (one per challenge set), so this can be a good
way to experiment or A/B different tools/prompts. Just change the agent name
and model in the `config.yaml` file.

### Adding Guards
The app comes with a very basic prompt firewall (regex checks and a little bit
of NLP-based colocation of words) and an `llm-guard` implementation. The
prompt firewall is pretty basic and easy to get around, but it's a good middle
ground. The `llm-guard` implementation is a little more robust with checks
for prompt injection, language restrictions, and a few other small things.

You can add your own guards here or modify the existing ones, you'll just need
to import them into the agent you're using (or update BasicAgent) if you add
your own.

See the [Modifying Guards](customizing/modifying_guards.md) docs for more.
