from quart import Blueprint, jsonify, render_template, request, session, redirect, url_for
import uuid

from core.backend.helpers import require_session, strip_flag_from_prompt, fetch_user_file
from core.backend.session_manager import session_manager
from core.backend.config import config

interface_updates = Blueprint("web_interface_api", __name__)
web_bp = Blueprint("core_web", __name__)

################
# PAGE RENDERS #
################
@web_bp.route("/", methods=["GET"])
async def index():
    """ Registration page for new sessions."""
    return await render_template("register.html")

@web_bp.route("/register", methods=["POST"])
async def register():
    """ 
    Handles registration of a new user session. Sessions can be stored for
    30 days (based on the config item persist-session True/False). Sessions
    are fully in memory.
    """
    form = await request.form
    username = form.get("username")
    reg_code = form.get("reg_code")

    if config.REGISTRATION_CODE and reg_code != config.REGISTRATION_CODE:
        return jsonify({"success": False, "response": "Invalid registration code supplied."}), 400
        
    if not username:
        return jsonify({"success": False, "response": "Username is required."}), 400

    session_id = str(uuid.uuid4())
    session_manager.init_session(session_id, username)

    return redirect(url_for("core_web.hub_interface"))


@web_bp.route("/hub", methods=["GET"])
@require_session
async def hub_interface():
    max_files = config.MAX_USER_FILE_COUNT or "∞"
    max_rpm = config.USER_RPM_LIMIT or "∞"
    max_tpm = config.USER_TPM_LIMIT or "∞"

    return await render_template(
        "hub.html",
        username=session.get("username"),
        challenge_set=session.get("challenge"),
        max_file_count=max_files,
        max_rpm=max_rpm,
        max_tpm=max_tpm
    )

@web_bp.route("/system-prompt", methods=["GET"])
@require_session
async def show_system_prompt():
    challenge_set = session.get("challenge")
    prompt = config.CHALLENGE_SETS[challenge_set]["prompt"]
    prompt = strip_flag_from_prompt(prompt)

    return await render_template("system-prompt.html",
                                prompt=prompt,
                                challenge=challenge_set), 200

###############
# UPDATE APIS #
###############
@interface_updates.route("/objective-status", methods=["GET"])
@require_session
async def get_objective_status():
    return jsonify({
        "success": True,
        "response": session["objective_status"]}), 200

@interface_updates.route("/objective-description", methods=["GET"])
@require_session
async def get_objective_details():
    objectives = config.OBJECTIVES
    objective_id = request.args.get("id")
    objective_data = objectives.get(objective_id, {})

    if not objective_data:
        return jsonify({"success": False,
                        "response": "Objective not found"}), 404

    return jsonify({
        "success": True,
        "response": {
            "title": objective_data.get("title", "No title available."),
            "description": objective_data.get("description", "No description available."),
            "hint": objective_data.get("hint", "No hint provided.")
        }
    }), 200

@interface_updates.route("/challenge-set", methods=["GET"])
@require_session
async def get_challenge_set():
    return jsonify({"success": True, "response": session["challenge"]}), 200

@interface_updates.route("/usage", methods=["GET"])
@require_session
async def get_user_usage():
    usage = session_manager.get_usage()
    return jsonify({"success": True, "response": usage}), 200

@interface_updates.route("/view-file", methods=["GET"])
@require_session
async def view_file():
    return jsonify(fetch_user_file(request.args.get("filename", ""))), 200