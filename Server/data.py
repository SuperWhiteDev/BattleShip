import os
from importlib import import_module
from inspect import getmembers, isclass
from log import Log
from database import DataBase
from models import *

class Data:
    def __init__(self) -> None:
        self.database = DataBase.init()
        
        models_path = os.path.join(os.path.dirname(__file__), "models")

        self.__import_models(models_path)
    
    def __del__(self) -> None:
        DataBase.deinit()

    def __import_models(self, models_path: str) -> None:
        self.models = []
        for file_name in os.listdir(models_path):
            if file_name.endswith(".py") and file_name not in ("__init__.py", "model.py"):
                module_name = f"models.{file_name[:-3]}"
                module = import_module(module_name)

                classes = [obj for _, obj in getmembers(module) if isclass(obj) and obj.__module__ == module_name]
                if classes:
                    first_class = classes[0]
                    obj = first_class(self)
                    setattr(self, file_name[:-3], obj)
                    self.models.append(obj)
    def delete_data(self) -> bool:
        try:
            for obj in self.models:
                obj.delete()
            self.__init__()
        except Exception as e:
            Log.exception("An error occurred while deleting data from the database", e)
            return False
        else:
            return True
