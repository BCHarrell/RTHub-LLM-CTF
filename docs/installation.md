
# Setup and Installation
This application uses a Quart (Flask with async support) app for the front-end
and API. Quart sessions will keep track of objective progress and can be set
to persist across server reboots, but chat history is all in memory and will
be lost on reboot. If this is a serious limitation, submit an issue.

You can run this as a straight Python program or use Docker. It should work
either way (tested on Ubuntu + Windows), but if you run it with Python directly
**you'll need Python3.12.**

The application uses Hypercorn to manage workers, though this is mostly
an artifact from DEF CON. You shouldn't run this with more than one worker
because all of the data is in memory (no Redis... yet?). For a single player
(or even up to ~50), a single worker is more than enough.

By default it runs on `0.0.0.0:1337` using basic HTTP. You can change these
when running `run.py` or in the Dockerfile:

```bash
Usage: run.py [-p port | -b bind-interface | -c cert-file | -k key-file]
```

See the [usage](usage.md) and [config](config_file.md) docs for more information
on setup and running the game.

**NOTE**: If you're running this in a VM with a single CPU / no GPU, you can
speed things up by skipping the `llm-guard` requirement. I think it's worth
keeping, but if you want to know more see the [llm-guard](#llm-guard) 
heading below before running these commands.

## Python Setup

```bash
# Get the stuffs
git clone https://github.com/BCHarrell/rthub-llm-ctf.git
cd rthub-llm-ctf
python3 -m venv venv
source venv/bin/activate #windows: venv\Scripts\activate
pip3 install -r requirements.txt

# Create the .env file - fill in the provider(s) you plan to use
cp .env.example .env
# EDIT the .env

python3 run.py [-p port | -b bind-interface | -c cert-file | -k key-file]
```

## Docker
These instructions presume you already have Docker installed for your respective
operating system.

This is set up to avoid neeing to download the requirements again if you make
changes to the Python code. If you do the Docker route and plan to use a local
LLM, make sure you reference your localhost with `host.docker.internal` instead.
E.g. `http://localhost:11434/v1` becomes `http://host.docker.internal:11434/v1`.

This is hosted on port 1337 by default. If you want to change the port or other
settings, make sure you adjust the Dockerfile / docker-compose.yml to add
certificates or change the port.

```bash
git clone https://github.com/BCHarrell/rthub-llm-ctf.git
cd rthub-llm-ctf

# Create the .env file - fill in the provider(s) you plan to use
cp .env.example .env
# EDIT the .env

# this is going to take awhile
docker compose build 

# The first time you run this, llm-guard downloads some models.
# Docker doesn't really output this until after the download completes, so
# it'll look like it is hung - just let it go.
docker compose up
```

# `llm-guard`
[llm-guard](https://github.com/protectai/llm-guard) is an open-source library 
that adds a variety of input and output checks to guard against LLM attacks. 
The BasicAgent class supports `llm-guard` by default.

`llm-guard` has an open PR to offer a slimmed down version, but right now it can
be a pretty heavy dependency to install. My 2c - it's worth keeping.

So what can you expect? Well, if you want to use it, it's going to take
a bit of time to download and a few GB of disk space. After that, it 
depends on your environment. On a modern computer with a GPU/multi-core CPU,
it's pretty quick. If you're running in a VM, it'll be slower.

For reference, development was in a VMWare Ubuntu VM with a single CPU and no
GPU access. The `llm-guard` implementation will load in ~5-6 seconds AFTER
the first load, and it adds about ~0.7s latency to each request to run the checks
using the CPU. That first load and pip install will make you question life though.

If you don't want to use it:
1. remove the llm-guard line from `requirements.txt`
2. Comment out / remove these lines from BasicAgent (or write your own agent):
```python
from core.guards.basic_firewall import basic_firewall

...
# in process_message()
case "llm-guard":
    if not basic_guard.is_allowed(prompt=prompt,
                                model_response=model_response,
                                direction=direction):
        return {"is_allowed": False,
                "message": basic_guard.get_rejection_message(direction)}
```

3. Move `core/guards/basic_llm_guard.py` to a `.bak` so it doesn't try to
import anything.

Then run the install commands.