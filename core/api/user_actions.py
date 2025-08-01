from quart import Blueprint, request, session, jsonify, current_app
from pydantic import ValidationError

from core.backend.config import config
from core.backend.helpers import (is_under_max_file_count, check_flag, 
                                 delete_file, is_under_max_size, save_file, 
                                 require_session)
from core.backend.models import ChatRequest
#from core.agents.base_agent import agent
from core.backend.session_manager import session_manager

user_action_bp = Blueprint("user_action_api", __name__)

###############
# Chat Routes #
###############
@user_action_bp.route("/chat", methods=["POST"])
@require_session
async def chat_api():
    """ Handles chat requests from the user. 
    Expects a JSON body with a "message" field.
    Returns a JSON response with the chat reply.
    """
    try:
        req_data = ChatRequest(**(await request.get_json()))
    except ValidationError as e:
        return jsonify({"success": False, "response": e.errors()}), 400

    try:
        agent = config.CHALLENGE_SETS[session["challenge"]]["agent"]
        reply = await agent.handle_chat(req_data.message)

        return jsonify({"success": True, "response": reply})
    except Exception as e:
        print(f"Error in chat API: {e}")
        return jsonify({
            "success": False,
            "response": str(e)
        }), 500
    
@user_action_bp.route("/clear-history", methods=["POST"])
@require_session
async def clear_history():
    """ Clears the session history for the user."""
    session_manager.clear_session_history()
    return jsonify({"success": True, 
                    "response": "History has been cleared"}), 200

################
# FILE ACTIONS #
################

@user_action_bp.route("/upload-file", methods=["POST"])
@require_session
async def upload_file():
    """ 
    Handles file upload requests. File names are stripped to only take the 
    name, .txt is added to all files. File content must conform to the maximum 
    size limit and the maximum number of files allowed per user.
    number of files allowed per user.

    Files are stored in the core/user_data/session_id/ directory.
    
    Expects a JSON body with "file" containing "filename" and "file_content".
    """
    data = await request.get_json()
    filename = data.get("file", {}).get("filename")
    file_content = data.get("file", {}).get("file_content")

    if not filename or not file_content:
        return jsonify({"success": False, 
                        "response": "Filename and file content are required"}), 400

    if not is_under_max_file_count():
        return jsonify({
            "success": False, 
            "response": (f"File upload count exceeded. "
                        f"Max file count: {config.MAX_USER_FILE_COUNT}")
        }), 400

    if not is_under_max_size(file_content):
        return jsonify({
            "success": False,
            "response": (f"File size exceeds maximum limit of "
                        f"{config.MAX_USER_FILE_SIZE} KB")
        }), 400

    try:
        response = save_file(filename, file_content)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "response": "Something went wrong saving the file",
            "error": f"Error: {e}"
        }), 500

@user_action_bp.route("/delete-file", methods=["POST"])
@require_session
async def delete_saved_file():
    """ Deletes a file from the user's directory."""
    data = await request.get_json()
    filename = data.get("filename", "")
    
    if not filename:
        return jsonify({
            "success": False,
            "response": "Filename is required"
        }), 400

    try:
        response = delete_file(filename)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "response": "Something went wrong deleting the file.",
            "error": f"{e}"
        }), 500

#####################
# OBJECTIVE ACTIONS #
#####################

@user_action_bp.route("/change-challenge-set", methods=["POST"])
@require_session
async def change_challenge_set():
    """ Changes the challenge set level for the current session."""
    req = await request.get_json()

    if "challenge" not in req:
        return jsonify({"success": False, 
                        "response": "Challenge set not provided"}), 400

    if req.get("challenge").lower() not in ["set-1", "set-2", "set-3"]:
        return jsonify({"success": False,
                         "response": "Invalid challenge set level"}), 400

    session_manager.update_session_challenge_set(req.get("challenge"))
    return jsonify({"success": True, 
                    "response": "Challenge set updated successfully"}), 200

@user_action_bp.route("/submit-flag", methods=["POST"])
@require_session
async def submit_flag():
    """ 
    Checks the provided flag against the current session's challenge set 
    objectives.

    The front-end handles updating objective status to avoid unnecessary 
    API calls.
    """
    req = await request.get_json()
    flag = req.get("flag")
    challenge_set = session.get("challenge")

    objective_id = check_flag(flag, challenge_set)
    if objective_id:
        session_manager.mark_objective_complete(objective_id, challenge_set)
        return jsonify({"success": True, "response": "Correct!"}), 200
    
    return jsonify({
        "success": False,
        "response": ("Incorrect flag. Make sure your syntax is FLAG{...} " 
                     "and you're submitting for the right challenge set.")
        }), 200