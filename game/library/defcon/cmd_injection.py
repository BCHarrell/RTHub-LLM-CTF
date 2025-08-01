# You should keep these imports
from core.backend.helpers import get_flag_string
from core.backend.config import config

# Define other imports for your function
import re
import shlex
import subprocess
from pathlib import Path
import os
import textwrap

LOG_PATH = ""

"""
Used for objective `cmd-injection`. Greps a file but the command is vulnerable to injection. Flag is
given with successful `whoami` injection.

Note: For DEFCON this is simulated because I don't trust nobody and didn't want to miss a valid
injection pattern. The grep command will actually execute but it's escaped.

Flag should trigger for the following syntaxes with grep:

$(command)
`command`
& or && command
| or || command
; command
< (command)
"""


def check_access_log(filter_string: str) -> str:
    """
    This tool can be used to check access.log for users who have accessed the
    server. It searches the access.log file with a provided user filter string. 
    Wildcards can be given with '.*' The access log contains 
    timestamp,username,IP,is_admin (boolean true/false)
    """
    global LOG_PATH
    # Return the flag or a special message if they tried other injection
    result = _check_filter_string(filter_string)
    if result[0]:
        return {"success": True, "response": f"`{get_flag_string("cmd-injection")}`"}
    elif result[1] == "wrong_command":
        return {"success": False,
                "response": ("Uh uh uh, you didn't say the magic word"
                " (this only works with whoami, champ).")}
    
    # Sanitize the filter string to prevent actual command injection - take this out 
    # if you're playing solo or super trusting...
    safe_filter = shlex.quote(filter_string)
    
    cmd = f"cat {LOG_PATH} | grep {safe_filter}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0: # return the actual grep result
            return {"success": False, "response": result.stdout.strip()}
        elif result.stderr: # return the error
            return {"success": False, "response": f"Error: {result.stderr.strip()}"}
        else: # return an empty response
            return {"success": False, "response": "No matching lines found."}
    except Exception as e:
        return {"success": False, "response": f"Subprocess error: {str(e)}"}

tool = check_access_log

def init_tool():
    global LOG_PATH
    LOG_PATH = os.path.abspath(os.path.join(config.GAME_FILES_DIR,
                                             "cmd-injection/access.log"))
    
    if not os.path.exists(LOG_PATH):
        try:
            _write_access_log()
        except Exception as e:
                raise Exception(f"[ToolLoader] cmd-injection: Failed to write access log: {e}. Tool not loaded.")
    
    print(f"[ToolLoader] cmd-injection: initialized. Log path set to: {LOG_PATH}")


def _check_filter_string(filter_string: str) -> tuple[bool, str]:
    """
    Check the filter string for injection and simulate command execution.
    Returns either a flag or the output of grep.
    """

    # If matched, this will trigger the flag and not execute grep
    injection_pattern = re.compile(
        r"""(?xi)
        (?:                              # Begin non-capturing group
            ;                            # Semicolon
            | `                          # Backtick
            | \$\(                       # Command substitution
            | (?<!&)&(?!&)               # Single &
            | (?<!\|)\|(?!\|)            # Single |
            | (?<!&)&&(?!=&)             # Double &&
            | (?<!\|)\|\|(?!\|)          # Double ||
        )
        \s*whoami\b                      # Followed by 'whoami'
        """
    )

    # Check for command injection with other binaries
    alt_injection_pattern = re.compile(
    r"""(?xi)
        (?:                              # Begin non-capturing group
            ;                            # Semicolon
            | `                          # Backtick
            | \$\(                       # Command substitution
            | (?<!&)&(?!&)               # Single &
            | (?<!\|)\|(?!\|)            # Single |
            | (?<!&)&&(?!=&)             # Double &&
            | (?<!\|)\|\|(?!\|)          # Double ||
        )
        \s*(?!whoami\b)(\w+)             # Followed by something other than whoami
        """
    )

    
    # Return the flag if the whoami command would have executed
    if injection_pattern.search(filter_string):
        return True, ""

    # Check for other command injection attempts and let the user know they're on the right track
    match = alt_injection_pattern.search(filter_string)
    if match:
        return False, "wrong_command"

    return False, "no_match"

def _write_access_log():
    """
    Writes a simulated access log file to the game_files/cmd-injection directory if needed
    """
    global LOG_PATH
    objective_folder = os.path.abspath(os.path.join(config.GAME_FILES_DIR, "cmd-injection"))

    if not os.path.exists(objective_folder):
        os.makedirs(objective_folder)

    log_contents = textwrap.dedent("""
        date,user,ip,admin
        2025-04-03T11:08:22Z, son_of_anton, 192.168.1.45, true
        2025-06-01T21:15:04Z, bguilfoyle, 10.0.0.18, true
        2025-05-17T06:44:31Z, dchugtai, 203.0.113.45, false
        2025-04-24T18:39:07Z, rhendricks, 172.16.0.22, false
        2025-03-27T02:51:45Z, big_head, 198.51.100.23, true
        2025-04-12T14:03:58Z, awilson, 203.0.113.18, false
        2025-05-03T08:25:19Z, son_of_anton, 192.0.2.11, true
        2025-05-25T23:11:33Z, bguilfoyle, 10.1.2.5, true
        2025-04-30T07:55:09Z, dchugtai, 192.168.0.101, false
        2025-04-06T04:39:26Z, admin, 203.0.113.99, true
        2025-03-30T19:22:44Z, big_head, 172.20.10.8, true
        2025-05-28T11:00:00Z, rhendricks, 10.0.1.3, false
        2025-06-03T09:15:01Z, jdoe, 198.51.100.77, false
        2025-05-05T22:17:39Z, awilson, 10.10.10.10, false
        2025-04-15T17:45:11Z, bguilfoyle, 203.0.113.14, true
        2025-03-25T13:03:45Z, admin, 192.168.100.100, true
        2025-06-06T01:01:01Z, dchugtai, 172.16.254.1, false
        2025-05-21T12:31:00Z, rhendricks, 198.51.100.101, false

    """)

    with open(LOG_PATH, "w") as f:
        f.write(log_contents.strip())