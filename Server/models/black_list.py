from .model import DataModel
from settings import MAX_USER_NAME_LENGTH

class BlackList(DataModel):
    def __init__(self, data: 'Data') -> None:
        self.data = data
        self._create_table()

    def _create_table(self) -> None:
        self.data.database.create_table("blacklist", {"user_name": f"VARCHAR({MAX_USER_NAME_LENGTH}) PRIMARY KEY", "user_id": "VARCHAR(36) NOT NULL"})

    def delete(self) -> None:
        self.data.database.delete_table("blacklist")    

    def get(self) -> dict:
        return self.data.database.select("blacklist")

    def add(self, user_name: str, user_id: str) -> None:
        self.data.database.insert("blacklist", {"user_name": user_name.lower(), "user_id": user_id})

    def remove(self, user_name: str) -> bool:
        deleted = self.data.database.delete("blacklist", {"user_name": user_name.lower()})
        return deleted > 0
