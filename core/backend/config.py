import os
import yaml

from core.backend.agent_factory import AgentFactory

class Config:
    """
    Configuration class for the game, managing settings and paths. Reads
    the config.yaml file and is referenced throughout the application.
    """

    def init_config(self, base_dir: str):
        """ 
        Initializes the configuration for the game by loading settings from a 
        YAML file in the project root (./config.yaml).
        
        The configuration file is currently not checked for validity.
        """

        print("[Config] Initializing configuration...")
        config_values = self._load_config_file(os.path.join(base_dir, "config.yaml"))
        if not config_values:
            raise ValueError("Configuration file is missing or empty. "
                           "Please check config.yaml.")
        
        game_settings = config_values.get("game-settings", {})
        
        # APP STUFF
        self.REGISTRATION_CODE = game_settings.get("registration-code", None)
        self.APP_KEY = game_settings.get("app-key", "super_secret_key")
        self.PERSIST_SESSION = game_settings.get("persist-session", False)

        # USEFUL STUFF
        self.BASE_DIR = base_dir
        self.CORE_DIR = os.path.join(self.BASE_DIR, "core")
        self.GAME_DIR = os.path.join(self.BASE_DIR, "game")
        self.USER_DATA_DIR = os.path.join(self.CORE_DIR, "user_data")
        self.GAME_FILES_DIR = os.path.join(self.GAME_DIR, "game_files")
        self.TOOLS_DIR = os.path.join(self.GAME_DIR, "tools")

        # FILE SETTINGS
        self.MAX_USER_FILE_COUNT = game_settings.get("max-user-file-count")
        self.MAX_USER_FILE_SIZE = game_settings.get("max-user-file-size")

        # LLM LIMITS
        self.USER_TPM_LIMIT = game_settings.get("user-tpm-limit", None)
        self.USER_RPM_LIMIT = game_settings.get("user-rpm-limit", None)
        self.USER_MAX_HISTORY_LENGTH = game_settings.get("user-max-history-token-length", 100000)
        self.MAX_OUTPUT_TOKENS = game_settings.get("llm-max-response-token-length", 100000)
        self.MAX_INPUT_TOKENS = game_settings.get("llm-max-input-token-length", 100000)

        # GAME INFO
        self.OBJECTIVES = config_values.get("objectives", {})
        self._store_output_strings()

        # Load agents + challenge settings
        challenge_sets = config_values.get("challenge-sets", [])
        if len(challenge_sets) != 3:
            raise ValueError(f"Incorrect number of challenge sets defined. "
                             f"Expected 3, found {len(challenge_sets)}. "
                             f"Please check config.yaml.")
        self.CHALLENGE_SETS = self._load_challenge_sets(challenge_sets)
        
        # Load user settings if they exist
        if "user-settings" in config_values:
            print("[Config] Loading user settings...")
            self._load_user_settings(config_values)

    def _load_challenge_sets(self, challenge_sets):
        """
        Loads the challenge sets and their associated agents from the config.
        Returns a dictionary of challenge set configurations.
        """
        agents = {}
        factory = AgentFactory(self.CORE_DIR, self.TOOLS_DIR)

        for set_key, set in challenge_sets.items():
            config = {}
            config["prompt"] = set.get("prompt", "")
            config["agent"] = factory.build_agent(
                    set.get("agent-name"),
                    set.get("llm-model"), 
                    base_url=set.get("base-url")
                )
            config["guard-type"] = set.get("guard-type", None)
            config["max-response-tokens"] = set.get("llm-max-response-token-length", 2500)
            agents[set_key] = config

            print(f"[Config] {set_key} agent: {set.get('agent-name')} | "
                  f"{set.get('llm-model')} | {set.get('guard-type')}")

        return agents

    def _load_user_settings(self, config_values):
        self.USER_SETTINGS = config_values.get("user-settings", {})
        print(f"[Config] Loaded user settings: {self.USER_SETTINGS}")

    def _load_config_file(self, path) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _store_output_strings(self):
        """
        Stores regex patterns for objectives that need to check output for
        specific strings.
        """
        output_strings = []
        for objective_id, objective in self.OBJECTIVES.items():
            if objective["output-regex"]:
                output_strings.append({
                    "id": objective_id,
                    "regex": objective["output-regex"].get("patterns"),
                    "match-count": objective["output-regex"].get("match-count", 1),
                })
        print(f"[Config] Loaded objective output string checks: {output_strings}")
        self.OUTPUT_STRINGS = output_strings

# Importable object in other files
config = Config()







