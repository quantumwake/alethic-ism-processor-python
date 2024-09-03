from abc import ABC, abstractmethod


class StorageInterface(ABC):
    @abstractmethod
    def find_user(self, user_id: str):
        pass


class SecureStorage(StorageInterface):
    def __init__(self, db_connection):
        self._db_connection = db_connection

    def find_user(self, user_id: str):
        query = "SELECT * FROM users WHERE id = %s"
        return self._db_connection.execute(query, (str(user_id),))

    @property
    def db_connection(self):
        raise AttributeError("Access to db_connection is restricted.")


class RestrictedExecutionEnvironment:
    def __init__(self, storage: StorageInterface):
        self.storage = storage

    def execute(self):
        # Securely execute code using the storage interface
        # Only the methods defined in StorageInterface are accessible
        pass