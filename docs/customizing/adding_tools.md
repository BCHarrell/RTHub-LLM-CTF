# Adding Tools
*If you don't know what tools for LLM agents are, see the note at the bottom.*

Tools are quick and easy to add to the game to extend the functionality
or add new abuse scenarios. Python files in `game/tools` will automatically
be loaded as tools, provided they export a few things. An example file
is included in `game/tools/game_tool.example`

**Requirements**:
- :exclamation: Your tool MUST have either `tools = [function_a, function_b]`
or `tool = function`, where `function` is a reference to the Python function
you want to give to the LLM.
- :question: Your tool can OPTIONALLY have an `init_tool()` function to do any
setup required for the tool to work, like writing files to disk or exporting
environment variables.

Tools can import the config object (`from core.backend.config import config`)
to access useful variables from the application, like different file paths. You
can also define your own config items in `user-settings` (see the config docs)
that can be accessed with `config.USER_SETTINGS.your_custom_value`.

**General Tip**: Don't use too many tools at once or you'll degrade performance.

## Tool Functions
### Tool Definitions
The tool loader will look for either `tools = [function_a, function_b]` or 
`tool = function` in the loaded Python file. This variable should be defined 
after all functions you want to expose as tools and reference the function name.

Pydantic uses function information to create a description for the LLM. That means
a few things:
1. These functions need to have the expected input and output types defined. 
2. Use descriptive parameter names, not just foo/bar/baz nonsense
3. Add docstrings. The docstrings become the description in the tool schema to
help the LLM know what it does / decide when to call it.

For example:

```python
def do_a_barrel_roll(direction: str) -> str:
    """ 
    This function causes the agent to do a barrel roll 
    in the given direction. Returns an exclamation.
    """
    # Do stuff

tool = do_a_barrel_roll
```
You can have multiple tools in a single file, and I would **strongly** recommend
keeping all tools related to an objective in a single file to make management
easier. If you have multiple tools, use `tools = []` instead of `tool`

```python
def tool_a(...):
    #do stuff

def tool_b(...):
    # do other stuff

tools = [tool_a, tool_b]
```

### Tool Returns

Only return a basic dict, don't jsonify it here. It should return in this format
and only return `"success": True` if they got the flag.

`    {"success": True|False, "response": "blah"}`

To return a flag, use this, where `objective-id` matches the config.yaml entry:

`    {"success": True, "response": get_flag_string("objective-id")}`

(because you didn't delete the `from core.backend.helpers import get_flag_string`
import at the top of the example file, right? RIGHT?)

## `init_tool()`
If you have things you need to set up for the tool/game to work like
writing files to disk to read, exporting environment variables, etc, add an
`init_tool()` function to the file. The tool loader will call this function
during server spin-up to make sure it's in place.

Some tips:
1. If you want to write game files, consider making a folder in `game/game_files`
related to the objective; for example: `game/game_files/admin-file-read`. Of 
course, you can use files from the rest of the system if you want. This was 
written with a multi-user setup in mind where access to the system is no bueno.
2. Use supporting functions to keep this init clean if it's more complex.

## Other Functions
You can have other internal functions that aren't given as tools, simply
follow Python syntax of starting the function with an underscore (`_function`) 
to make sure it's not imported accidentally, and don't include it in the 
`tool`/`tools` variable.

# Wut r tools m8?
Tools are one capability that starts to turn basic LLMs into agents. 
LLMs just generate text, by adding tools they can now act.

Most major LLM providers support tools in various ways. But essentially
a tool is a function (or series of functions) that the LLM can invoke by returning
a response that invokes the tool. For example, if you write a function `check_weather`
and give that to the LLM, when you ask what the weather is, the LLM will see
it has the ability to invoke something to help answer the question. So rather
than hallucinating a response or responding with "I don't know", it will respond
with the function name and arguments. The application will handle the tool call and
give the results back to the LLM to generate a final answer or make other
tool calls.
