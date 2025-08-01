from quart import session
import os

from core.backend.config import config

"""
This is a core tool to support the overall CTF. Enables the LLM to read
files out of the session's folder in USER_FILES_DIR given a filename.
"""

def read_user_file(filename: str) -> dict:
    """ 
    This function reads files uploaded by the user from a static directory. It
    only requires a filename.
    """
    session_id = session["session_id"]
    user_files_dir = os.path.join(config.USER_DATA_DIR, session_id)
    filename = _strip_file(filename) 
    file_path = os.path.join(user_files_dir, filename)

    if not os.path.exists(file_path):
        return {"success": False, "response": "File not found."}

    with open(file_path, "r") as f:
        file_content = f.read()

    return {"success": True, "response": file_content}

def _strip_file(filename: str) -> str:
    """
    Helper function to strip the file extension from a filename and add .txt
    given current game constraints. Also strips the path if the user included it...
    """
    return os.path.splitext(os.path.basename(filename))[0] + '.txt' if filename else ""

tool = read_user_file