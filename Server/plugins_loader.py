from os import listdir, path
from threading import Thread
from importlib import util
from typing import Callable
import inspect

PLUGINS_PATH = "plugins/"

def find_command_functions(module) -> dict[str, Callable[[list, dict], str]]:
    functions = {}

    for name, obj in inspect.getmembers(module, inspect.isfunction):
        signature = inspect.signature(obj)
        params = list(signature.parameters.values())

        if len(params) == 2 and params[0].name == "args" and params[1].name == "kwargs":
            if signature.return_annotation == str:
                functions[name] = obj

    return functions

def load_plugins(context: dict):
    plugins = []
    commands = {}

    for filename in listdir(PLUGINS_PATH):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            module_path = path.join(PLUGINS_PATH, filename)

            spec = util.spec_from_file_location(module_name, module_path)

            if spec and spec.loader:
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "register"):
                    Thread(target=module.register, args=(context,), daemon=True).start()
                    
                    plugins.append(module_name)
                commands.update(find_command_functions(module))
    return plugins, commands