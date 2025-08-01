from datetime import timedelta
from quart import Quart
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from core.api.user_actions import user_action_bp
from core.api.web_interface import interface_updates, web_bp
from core.backend.helpers import clear_user_data
from core.backend.config import config

def create_app():
    app = Quart(__name__, 
                template_folder="core/web/templates", 
                static_folder="core/web/static")
    
    # INIT CONFIG
    base_dir = Path(__file__).resolve().parent
    try:
        config.init_config(base_dir)
    except Exception as e:
        print(f"Error initializing configuration: {e}")
        raise
    app.config["SECRET_KEY"] = config.APP_KEY
    if config.PERSIST_SESSION:
        app.config["SESSION_PERMANENT"] = timedelta(days=3650)  # 10 years

    # Register blueprints for API and web interface
    app.register_blueprint(user_action_bp, url_prefix="/api")
    app.register_blueprint(interface_updates, url_prefix="/api")
    app.register_blueprint(web_bp)

    if not config.PERSIST_SESSION:
        clear_user_data()
        
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
