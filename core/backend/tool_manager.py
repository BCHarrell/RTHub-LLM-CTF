import os
import importlib

class ToolManager:
    LOADED_TOOLS = []

    def load_all_tools(self, tools_dir):
        """
        Loads all tools from the specified directory and initializes them.
        If any cannot be initialized, they are skipped with an error message.
        Args:
        """
        self.LOADED_TOOLS.clear()

        if not os.path.exists(tools_dir):
            print(f"[ToolLoader] Tools directory does not exist: {tools_dir}")
            return
        
        tools = False
        for filename in os.listdir(tools_dir):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue

            module_name = f"game.tools.{filename[:-3]}"
            try:
                self._load_single_tool(module_name)
                tools = True
            except Exception as e:
                print(f"[ToolLoader] Error loading tool {module_name}: {e}")

        if not tools:
            print("[ToolLoader] No tools found in the tools directory. "
                  "Continuing without tools.")

    def _load_single_tool(self, module_name):
        """ 
        Loads a single tool module by its name and initializes it 
        (if init_tool() is found). 
        """
        try:
            tool_file = importlib.import_module(module_name)
            if hasattr(tool_file, "tools"):
                tools = getattr(tool_file, "tools")
            elif hasattr(tool_file, "tool"):
                tools = [getattr(tool_file, "tool")]
            else:
                msg = (f"[ToolLoader] {module_name} does not have the required "
                       "attributes (tool). Skipping.")
                print(msg)
                return

            if hasattr(tool_file, "init_tool"):
                try:
                    tool_file.init_tool()
                except Exception as e:
                    error_msg = (f"[ToolLoader] Error with initializing module "
                                f"{module_name}: {e}")
                    print(error_msg)
                    raise e
                
            self.LOADED_TOOLS.extend(tools)
            print(f"[ToolLoader] Loaded tool file: {module_name}")
        except Exception as e:
            print(f"[ToolLoader] Failed to load {module_name}: {e}")

    def get_tools(self):
        """
        Returns a list of loaded tools.
        """
        return self.LOADED_TOOLS

tool_manager = ToolManager()