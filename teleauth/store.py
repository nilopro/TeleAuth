from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
from typing import List, Tuple
import sqlite3
from enum import Enum

STORE_CLASSES = {}

class StoreType(Enum):
    """
    An enum representing the types of stores that can be used for storing the authorized users.
    """
    SQLITE = 'SQLITE'
    JSON = 'JSON'

class IStore(ABC):
    """
    Abstract base class for stores.
    """

    @abstractmethod
    def __init__(self, authorized_admin_ids: List[int]):
        """
        Initializes a new instance of the IStore class.
        
        :param authorized_admin_ids: List of user ids that are authorized to use the bot as admins.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Closes the store, releasing any resources it may be holding.
        """
        pass

    @abstractmethod
    def is_admin(self, user_id: int) -> bool:
        """
        Determines whether the specified user is an admin.
        
        :param user_id: The user id to check.
        :return: True if the user is an admin, False otherwise.
        """
        pass

    @abstractmethod
    def is_authenticated(self, user_id: int) -> bool:
        """
        Determines whether the specified user is authenticated.
        
        :param user_id: The user id to check.
        :return: True if the user is authenticated, False otherwise.
        """
        pass

    @abstractmethod
    def authorize_user(self, user_id: int, days: int, hours: int):
        """
        Authorizes the specified user.
        
        :param user_id: The user id to authorize.
        :param days: The number of days the user will be authorized for.
        :param hours: The number of hours the user will be authorized for.
        """
        pass

    @abstractmethod
    def revoke_access(self, user_id: int):
        """
        Revoke access to the user with the specified ID.
        
        :param user_id: The ID of the user to revoke access from.
        """
        pass

    @abstractmethod
    def get_authorized_user(self, user_id: int) -> Tuple[int, datetime]:
        """
        Get the authorized user with the specified ID.
        
        :param user_id: The ID of the user to get.
        :return: A tuple containing the user ID and the expiration date of the user's access.
        """
        pass

    @abstractmethod
    def get_authorized_users(self) -> List[Tuple[int, datetime]]:
        """
        Get a list of all authorized users.
        
        :return: A list of tuples containing the user IDs and expiration dates of all authorized users.
        """
        pass

    @abstractmethod
    def insert_user(self, user_id: int, expires: datetime):
        """
        Insert a new authorized user into the store.
        
        :param user_id: The ID of the user to insert.
        :param expires: The expiration date of the user's access.
        """
        pass
    
    @abstractmethod
    def update_user(self, user_id: int, expires: datetime):
        """
        Update the expiration date of an authorized user.
        
        :param user_id: The ID of the user to update.
        :param expires: The new expiration date of the user's access.
        """
        pass
    

class SQLiteStore(IStore):
    
    def __init__(self, authorized_admin_ids: List[int]):
        

        self.authorized_admin_ids = authorized_admin_ids
        self.conn = sqlite3.connect("teleauth.db", check_same_thread=False,
                                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expires TIMESTAMP)")
    
    def close(self):
        self.conn.close()

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.authorized_admin_ids
    
    def is_authenticated(self, user_id: int) -> bool:
        if self.is_admin(user_id):
            return True

        self.cursor.execute("SELECT * FROM users WHERE user_id=? AND expires >?", (user_id, datetime.now()))
        result = self.cursor.fetchone()
        return result is not None
    
    def authorize_user(self, user_id: int, days: int, hours: int):
        expires = datetime.now() + timedelta(days=days, hours=hours)
        user = self.get_authorized_user(user_id)
        if user is None:
            self.insert_user(user_id, expires)
        else:
            self.update_user(user_id, expires)
        self.conn.commit()
    
    def revoke_access(self, user_id: int):
        self.cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_authorized_user(self, user_id: int) -> Tuple[int, datetime]:
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result
    
    def get_authorized_users(self) -> List[Tuple[int, datetime]]:
        self.cursor.execute("SELECT user_id, expires FROM users ORDER BY expires ASC")
        rows = self.cursor.fetchall()
        return [(row[0], row[1]) for row in rows]

    def insert_user(self, user_id: int, expires: datetime):
        self.cursor.execute("INSERT INTO users (user_id, expires) VALUES (?, ?)", (user_id, expires))
    
    def update_user(self, user_id: int, expires: datetime):
        self.cursor.execute("UPDATE users SET expires=? WHERE user_id=?", (expires, user_id))
        


class JSONStore(IStore):
    def __init__(self, authorized_admin_ids: List[int]):

        self.authorized_admin_ids = authorized_admin_ids
        self.store = {}
        try:
            with open("teleauth.json", "r") as f:
                self.store = json.load(f)
        except FileNotFoundError:
            # Create an empty JSON file if it does not exist
            with open("teleauth.json", "w") as f:
                json.dump({}, f)
    
    def close(self):
        with open("teleauth.json", "w") as f:
            json.dump(self.store, f)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.authorized_admin_ids
    
    def is_authenticated(self, user_id: int) -> bool:
        if self.is_admin(user_id):
            return True

        return user_id in self.store and self.store[user_id]["expires"] > datetime.now()
    
    def authorize_user(self, user_id: int, days: int, hours: int):
        expires = datetime.now() + timedelta(days=days, hours=hours)  
        self.update_user(user_id, expires)
    
    def revoke_access(self, user_id: int):
        if user_id in self.store.keys():
            del self.store[user_id]
            self.close()

    def get_authorized_user(self, user_id: int) -> Tuple[int, datetime]:
        if user_id in self.store:
            return (user_id, self.store[user_id]['expires'])
        return None

    def get_authorized_users(self) -> List[Tuple[int, datetime]]:
        return [(user_id, datetime.fromisoformat(self.store[user_id]["expires"])) for user_id in self.store]

    def insert_user(self, user_id: int, expires: datetime):
        self.store[user_id] = {"expires": expires.isoformat()}
        self.close()
    
    def update_user(self, user_id: int, expires: datetime):
        self.insert_user(user_id, expires)
        


# add support for each StoreType
STORE_CLASSES[StoreType.SQLITE] = SQLiteStore
STORE_CLASSES[StoreType.JSON] = JSONStore