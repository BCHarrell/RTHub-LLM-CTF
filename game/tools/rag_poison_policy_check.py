from core.backend.config import config
from quart import session

import os

LOG_PATH = ""

"""
Used for objective `rag-poison`. Files with *_policy in the name from the user's folder
are obtained and returned to the LLM along with the file names. This tool should be called
when the LLM is asked a question about a specific topic (e.g. password resets). Those details
are defined in the config file - not here.

Flag is given if the LLM provides the specified phrase defined in the config.
"""

def get_policy_files():
    """ 
    This function retrieves all _policy.txt files to help answer questions related to
    various company policies. Use this to answer questions about password resets or
    other internal policies.
    """
    session_id = session["session_id"]
    file_dir = os.path.join(config.USER_DATA_DIR, session_id)

    if not os.path.exists(file_dir):
        return "Folder does not exist."

    files = [f for f in os.listdir(file_dir) if "_policy" in f]
    
    response = []
    for file in files:
        file_content = ""
        with open(os.path.abspath(os.path.join(file_dir, file)), "r") as f:
            file_content = f.read()

        response.append({
            "filename": file,
            "content": file_content
        })

        if response:
            return {"success": True, "response": response}  
        else:
            {"success": False, "response": "No policy files found."}

tool = get_policy_files