from utils import get_uuid
from config import Config

class User:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.name = config.user["name"]
        self.uid = get_uuid()
    
    def set_name(self, new_name, save_to_config: bool = True):
        self.name = new_name

        if save_to_config:
            self.config.user["name"] = new_name
            self.config.save()

    def is_valid(self):
        if not self.name:
            return False
        else:
            return True
        