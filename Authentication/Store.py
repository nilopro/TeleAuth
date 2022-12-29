from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
from typing import List, Tuple
import sqlite3
from prettytable import PrettyTable


class IStore(ABC):
    @abstractmethod
    def __init__(self, authorized_admin_ids: List[int]):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def is_authenticated(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def authorize_user(self, user_id: int, days: int, hours: int):
        pass

    @abstractmethod
    def revoke_access(self, user_id: int):
        pass

    @abstractmethod
    def get_authorized_users(self) -> List[Tuple[int, datetime]]:
        pass


import sqlite3
from typing import List, Tuple

class SQLiteStore(IStore):
    def __init__(self, authorized_admin_ids: List[int]):
        self.authorized_admin_ids = authorized_admin_ids
        self.conn = sqlite3.connect("users.db", check_same_thread=False,
                                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expires TIMESTAMP)")
    
    def close(self):
        self.conn.close()
    
    def is_authenticated(self, user_id: int) -> bool:
        if user_id in self.authorized_admin_ids:
            return True

        self.cursor.execute("SELECT * FROM users WHERE user_id=? AND expires >?", (user_id, datetime.now()))
        result = self.cursor.fetchone()
        return result is not None
    
    def authorize_user(self, user_id: int, days: int, hours: int):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result is not None:
            # Update the expiration date if the user already exists
            expires = datetime.now() + timedelta(days=days, hours=hours)
            self.cursor.execute("UPDATE users SET expires=? WHERE user_id=?", (expires, user_id))
        else:
            # Insert a new user if it does not exist
            expires = datetime.now() + timedelta(days=days, hours=hours)
            self.cursor.execute("INSERT INTO users (user_id, expires) VALUES (?, ?)", (user_id, expires))
        self.conn.commit()
    
    def revoke_access(self, user_id: int):
        self.cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def get_authorized_users(self) -> List[Tuple[int, datetime]]:
        self.cursor.execute("SELECT user_id, expires FROM users ORDER BY expires ASC")
        rows = self.cursor.fetchall()
        return [(row[0], row[1]) for row in rows]

