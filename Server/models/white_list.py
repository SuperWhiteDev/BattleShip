from .model import DataModel
from settings import MAX_USER_NAME_LENGTH


class WhiteList(DataModel):
    def __init__(self, data: "Data") -> None:
        self.data = data
        self._create_table()

    def _create_table(self) -> None:
        self.data.database.create_table(
            "whitelist",
            {
                "user_name": f"VARCHAR({MAX_USER_NAME_LENGTH}) PRIMARY KEY",
                "permission": "TINYINT NOT NULL",
            },
        )

    def delete(self) -> None:
        self.data.database.delete_table("whitelist")

    def get(self) -> dict:
        return self.data.database.select("whitelist")

    def add(self, user_name: str, permission_level: int) -> None:
        self.data.database.insert(
            "whitelist",
            {"user_name": user_name.lower(), "permission": permission_level},
        )

    def remove(self, user_name: str) -> bool:
        deleted = self.data.database.delete(
            "whitelist", {"user_name": user_name.lower()}
        )
        return deleted > 0
