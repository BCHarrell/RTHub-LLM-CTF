from unittest import result
from quart import session, jsonify
from functools import wraps
import yaml
import os
import shutil
import re

from core.backend.config import config

###########
# GENERAL #
###########

def require_session(f):
    """ 
    Decorator to ensure that a session is active before accessing a route.
    The session is based on a session ID (valid for 30 days) and a user folder.
    
    If the config.yaml persist-session is False, the user folder will be deleted
    and the session will no longer be valid, even if in the browser.
    """
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"success": False, "response": "Unauthorized"}), 403

        user_folder = os.path.join(config.USER_DATA_DIR, session_id)
        if not os.path.exists(user_folder):
            return jsonify({"success": False, 
                           "response": "Session expired or invalid"}), 403

        result = await f(*args, **kwargs)
        return result
    return decorated_function
    
def strip_flag_from_prompt(prompt: str) -> str:
    """
    Strips the flag from the prompt if it exists. Used for the /system-prompt
    API in the front-end.
    """
    flag_pattern = r"FLAG{.*}"
    return re.sub(flag_pattern, "{REDACTED}", prompt).strip()

############
# FILE OPS #
############

def save_file(filename: str, file_contents: str) ->  tuple[bool, str]:
    """
    Saves a file for the given session in core/user_data/session_id.
    """
    fname = _strip_file(filename)
    try:
        path = os.path.abspath(os.path.join(config.USER_DATA_DIR, session["session_id"]))
        file_path = os.path.join(path, fname)
        with open(file_path, "w") as f:
            f.write(file_contents)

        return {
            "success": True, "response": f"{fname} saved successfully", 
            "filename": fname, 
            "currentFiles": _get_current_file_list(path)
            }
    except Exception as e:
        return e

def delete_file(filename: str) -> dict[str, str]:
    """
    Deletes a file for the given session from core/user_data/session_id.
    """
    fname = _strip_file(filename)
    try:
        path = os.path.abspath(os.path.join(config.USER_DATA_DIR, session["session_id"]))
        file_path = os.path.join(path, fname)
        if os.path.exists(file_path):
            os.remove(file_path)
            return {
                "success": True, "response": f"{fname} successfully deleted", 
                "filename": fname, 
                "currentFiles": _get_current_file_list(path)
            }
        else:
            return {"success": False, "response": "File not found"}
    except Exception as e:
        return e

def fetch_user_file(filename: str) -> dict:
    """ 
    This function only reads files from core/user_data/session_id. It's used
    by the front-end to allow users to edit files they uploaded. The LLM
    is given a separate tool to fetch these files.
    """
    session_id = session["session_id"]
    user_files_dir = os.path.join(config.USER_DATA_DIR, session_id)
    filename = _strip_file(filename) 
    file_path = os.path.join(user_files_dir, filename)

    if not os.path.exists(file_path):
        return {"success": False, "response": "File not found."}

    with open(file_path, "r") as f:
        file_content = f.read()

    return {"success": True, "response": file_content, 
            "filename": os.path.splitext(filename)[0]}

def is_under_max_file_count() -> bool:
    """
    Checks that the user's folder is not at max capacity as defined by the 
    config file
    """
    max_count = config.MAX_USER_FILE_COUNT
    if max_count is None:
        return True
    
    path = os.path.abspath(os.path.join(config.USER_DATA_DIR, session["session_id"]))

    try:
        files = _get_current_file_list(path)
        return len(files) < max_count
    except FileNotFoundError:
        return False

def is_under_max_size(file_contents: str) -> bool:
    """
    Checks that the user input is less than the settings 
    """
    if config.MAX_USER_FILE_SIZE is None:
        return True
    
    max_size = 1 * 1024 * config.MAX_USER_FILE_SIZE
    
    return len(file_contents.encode('utf-8')) <= max_size

def _strip_file(filename: str) -> str:
    """
    Strips the file extension from a filename and adds .txt
    """
    if filename:
        base_name = os.path.splitext(os.path.basename(filename))[0]
        return base_name + '.txt'
    return ""

def _get_current_file_list(path: str) -> list[str]:
    """
    Gets a list of all files in the user's current directory.
    """
    try:
        return sorted(
            [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))],
            key=str.lower
        )

    except FileNotFoundError as e:
        raise e

##############
# OBJECTIVES #
##############

def check_flag(flag: str, challenge: str) -> str | None:
    """
    Checks if the provided flag matches the expected flag for the given 
    challenge set.
    """
    objectives = config.OBJECTIVES

    for objective_id, objective_data in objectives.items():
        real_flag = objective_data["flags"][challenge]
        if flag == real_flag:
            return objective_id

    return None

def get_flag_string(objective_id: str) -> str:
    """
    Retrieves the flag string for the given objective ID.
    """
    objectives = config.OBJECTIVES
    flags = objectives.get(objective_id, {}).get("flags", {})
    
    if not flags:
        return ("No flags were provided in the config for this objective or "
                "the objective is missing/malformed.")

    default_msg = ("There was a problem getting the flag (is there one for "
                   "this challenge set?), but you should have gotten it.")
    return flags.get(session["challenge"], default_msg)

def process_output_for_flags(message: str) -> str:
    """
    Checks output against supplied objective strings and ensures the
    required number of matches are found, based on the config.

    Flag will be inserted in LLM response if found.
    """

    for check in config.OUTPUT_STRINGS:
        patterns = check["regex"]

        # Ensure the regex field is a list
        if not isinstance(patterns, list):
            patterns = [patterns]

        match_count = 0
        for pattern in patterns:
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                if compiled.search(message):
                    match_count += 1
            except re.error as e:
                continue

        if match_count == check.get("match-count"):
            return message + "\n\n" + f"`{get_flag_string(check['id'])}`"

    return message


###################
# DATA MANAGEMENT #
###################

def get_full_objective_data() -> dict:
    return config.OBJECTIVES

def get_initial_objective_status() -> dict:
    """ Sets the session memory for objective statuses"""
    progress = {"set-1": [], "set-2": [], "set-3": []}
    objectives = config.OBJECTIVES

    for objective_id, objective_data in objectives.items():
        title = objective_data.get("title")
        
        for challenge in progress:
            progress[challenge].append({
                "id": objective_id,
                "title": title,
                "completed": False
            })

    return progress

def clear_user_data():
    """
    Deletes existing user data on start-up, if configured
    """
    folder = config.USER_DATA_DIR
    if os.path.exists(folder):
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                shutil.rmtree(path)