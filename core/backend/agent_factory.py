import importlib
import os
import inspect

from core.backend.tool_manager import tool_manager

class AgentFactory:

    def __init__(self, core_dir: str, tools_dir: str):
        """
        Initialization requires the core and tools directories to avoid
        a circular import of config.
        """
        self.CORE_DIR = core_dir
        self.TOOLS_DIR = tools_dir
        self._load_agents()
        self._load_tools()

    def _load_agents(self):
        """
        Loads all agents from core/agents based on the provided
        class name (e.g. core/agents/basic_agent.py --> BasicAgent)
        """
        agents_dir = os.path.join(self.CORE_DIR, "agents")
        agents = {}

        for filename in os.listdir(agents_dir):
            if filename == "__init__.py" or not filename.endswith(".py"):
                continue

            module_name = f"core.agents.{filename[:-3]}"

            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"[AgentLoader] Skipping {module_name}: {e}")
                continue

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module.__name__:  # exclude imported classes
                    agents[name] = obj  # store class reference

        print(f"[Config] Loaded agents: {list(agents.keys())}")
        self.AGENTS = agents

    def _load_tools(self):
        """
        Stores the available tool references for building agents later.
        """
        tool_manager.load_all_tools(self.TOOLS_DIR)
        self.tools = tool_manager.get_tools()
        print("[Config] Loaded tools:", [tool.__name__ for tool in self.tools])

    def build_agent(self, agent_name: str, model: str, base_url: str = None) -> object:
        """
        Builds an agent instance by name.
        """
        if agent_name not in self.AGENTS:
            print(f"Agent {agent_name} is not registered. Using BasicAgent instead.")
            agent = self.AGENTS["BasicAgent"]
        else:
            agent = self.AGENTS[agent_name]

        return agent(model, self.tools, base_url=base_url)