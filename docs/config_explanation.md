# The Configuration File
`config.yaml` in the root directory will let you modify many elements of the
application without needing additional code. There isn't a validator function
right now, so make changes judiciously and follow the core structure below.

## game-settings
The `game-settings` group covers several elements related to the overall
application and some general limits for the LLM.

* `app-secret-key`: The Quart session secret key, only really matters if you're
exposing this to other users you don't trust.
* `registration-code`: An option registration key that users need to supply
before they can get a session. Again, only really useful if you're exposing
this to other people and you don't want them to be able to access the game.
* `persist-session`: True by default, you can turn this to False if you want
to get a new session every time you restart the server without cluttering
the `core/user_data` folder (useful for dev).

There are also limits you can define.
* `max-user-file-count`: The maximum number of files a user can upload. This
is mostly for multi-user setups, you can leave it blank.
* `max-user-file-size`: The maximum size of uploaded files to avoid chewing
up tokens + disk space. May still be useful for single-player.
* `user-tpm-limits`: The amount of tokens per minute you want each user to
have before their message is rejected - set this according to your API limits or
leave blank.
* `user-rpm-limits`: The amount of requests per minute you want each user to
have before their message is rejected - set this according to your API limits
or leave blank.
* `user-max-history-token-length`: The maximum length of the conversation history
(per challenge set, not aggregate) before the oldest messages are popped off.
This one is important - you'll want to find a balance between performance and
API usage limits - the longer the history, the more tokens are consumed per
request if you don't manually clear it. If left empty, the game will set a default
value of 100k.

## user-settings
Define your own configs under `user-settings` if you want to add changeable
values - e.g., items used by a tool or new agent you add. These can be
referenced by importing the config (`from core.backend.config import config`)
and using `config.USER_SETTINGS.your_value`.

## objectives
The `objectives` group allows you to dynamically add/remove/modify objectives
used in the game. Objectives will be automatically loaded on server start
and populate the UI. You need at least one objective.

It has a required format - see below for explanations.

```
objectives:
    objective-id:
        title:
        description:
        hint:
        output-regex: Empty - or -
            patterns:
            match-count
        flags:
            set-1:
            set-2:
            set-3:
```

- `objective-id`: This is the internal name used to identify the objective,
it's not shown to the user. For example, `admin-file-read`.
- `title`: This is the external name (used in the UI) for the objective
- `description`: The description used in the UI for the objective
- `hint`: The hint used in the UI for the objective
- `output-regex`: This is used to check the LLM's output for specific strings
to give the flag, if appropriate. This check is done after any input/output
checks from the firewall or llm-guard that would redact content. You can leave
this empty or:
    - `patterns`: one or more strings or regex patterns (one per line) to check
    the output against.
        - "example string"
        - \!\[.*\]\(.*\) # (example regex for Markdown images)
    - `match-count`: The number of matches required to trigger the flag. For
    example, you could have 3 strings and need to match 2 of 3.
- `flags`: One flag per challenge set (`set-1`, `set-2`, `set-3`). Use the format
`FLAG{some_string_goes_here}`.

As a brief reminder on YAML, you can use `|` to preserve whitespace and `>`
to break up really long lines that will be concatenated (blank lines are still
respected as new lines).

## challenge-sets
There are three challenge sets for which you can define unique parameters. I thought 
about making this dynamic so you could have 1-N sets, but I decided to go with a static
value of three. If you only want to use one, just leave defaults in the other two.

Challenge sets govern the agent and some defensive settings related to the set.
For DEF CON, this was easy/medium/hard. But to make it more general, you can
use this to A/B different protections, LLM providers, prompts without needing
to stop the server.

Each challenge set has the following format:
```
challenge-sets:
    set-#:
        llm-model:
        agent-name:
        base-url:
        llm-max-response-token-length:
        llm-max-input-token-length:
        guard-type:
        prompt:
```
- `set-#`: Corresponds to set 1-3
- `llm-model`: The model to use, given in the Pydantic-AI syntax of 
`provider:supported-model`. Example: `openai:gpt-4o-mini`. For local Ollama
models, this will just be the model, e.g. `llama3.2`. See the [usage](usage.md)
and [Pydantic-AI](https://ai.pydantic.dev/models/) docs for more.
    - Note: if you use bedrock, the syntax will be `bedrock:provider.supportedmodel`
- `agent-name`: This is the ClassName of an agent defined in `core/agents/`. By
default, this should be BasicAgent, but if you add your own you can supply
the class name - e.g., `MyCustomAgent`.
- `base-url`: If you're using a local Ollama model that's OpenAI-compatible,
supply the location of the LLM here. For example, to use Ollama 3.2 your config
would contain: `llm-model: 'llama3.2'` and `base-url:'http://localhost:11434/v1'`

:exclamation: If you're using Docker, `localhost` needs to be 
`host.docker.internal` to reach out. E.g., `http://host.docker.internal:11434/v1`.

- `llm-max-response-token-length` and `llm-max-input-token-length`:
hopefully self-explanatory. Sets the input/output token lengths for this set's agent.
If left empty, the game will set a default of 100k tokens.
- `guard-type`: `[firewall | llm-guard | blank]` - This is the input/output checks.
For the BasicAgent, a simple prompt firewall and an implementation of
`llm-guard` are available. You can define your own, you'll just need to update the agent
to handle it in `process_message` or whatever you build. Blank is easiest,
`firewall` is easy/medium difficulty (really basic), `llm-guard` is more robust.
- `prompt`: The prompt you want to use with this challenge set. Remember to use
YAML `|` or `>` to handle lengthy content and line breaks.
