from abc import ABC, abstractmethod

class DataModel(ABC):
    @abstractmethod
    def _create_table(self) -> None:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass

    @abstractmethod
    def get(self) -> dict:
        pass

    @abstractmethod
    def add(self, user_name: str, user_id: str) -> None:
        pass

    @abstractmethod
    def remove(self, user_name: str) -> bool:
        pass
