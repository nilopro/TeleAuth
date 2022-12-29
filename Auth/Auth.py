from typing import List, Tuple
from prettytable import PrettyTable
from Auth.store import IStore, SQLiteStore, JSONStore, StoreType, STORE_CLASSES
from datetime import datetime
from enum import Enum

def create_store(store_type: StoreType, authorized_admin_ids: List[int]) -> IStore:
    """
    Factory method that creates a store instance based on the specified store type.
    
    :param store_type: The store type to use (either `SQLITE` or `JSON`).
    :param authorized_admin_ids: A list of user IDs of authorized admins.
    :return: An instance of the store.
    """
    store_class = STORE_CLASSES.get(store_type)
    if store_class is None:
        raise ValueError(f"Invalid store type: {store_type}")
    return store_class(authorized_admin_ids)

class Auth:
    """
    Initializes the authentication system.
    
    :param authorized_admin_ids: A list of user IDs of authorized admins.
    :param store_type: The store type to use (either `SQLITE` or `JSON`). Defaults to `SQLITE`.
    """
    def __init__(self, authorized_admin_ids: List[int], store_type: StoreType=StoreType.SQLITE):
        self.store = create_store(store_type, authorized_admin_ids)
    
    def close(self):
        """
        Closes the connection to the store (if applicable).
        """
        self.store.close()

    def is_admin(self, user_id: int) -> bool:
        """
        Determines if the specified user is an authorized admin.
        
        :param user_id: The user ID to check.
        :return: True if the user is an authorized admin, False otherwise.
        """
        return self.store.is_admin(user_id)
    
    def is_authenticated(self, user_id: int) -> bool:
        """
        Determines if the specified user is authenticated (either an authorized admin or an authorized user with an unexpired access).
        
        :param user_id: The user ID to check.
        :return: True if the user is authenticated, False otherwise.
        """
        return self.store.is_authenticated(user_id)
    
    def authorize_user(self, user_id: int, days: int, hours: int):
        """
        Grants access to the specified user for the specified number of days and hours.
        
        :param user_id: The user ID to authorize.
        :param days: The number of days of access to grant.
        :param hours: The number of hours of access to grant.
        """
        self.store.authorize_user(user_id, days, hours)
    
    def revoke_access(self, user_id: int):
        """
        Revokes access to the specified user.
        
        :param user_id: The user ID to revoke access to.
        """
        self.store.revoke_access(user_id)
    
    def get_authorized_users_table(self, field_names:List[str]=["USER ID", "EXPIRES"], datetime_format:str="%d/%m/%Y %H:%M") -> str:
        """
        Returns a prettytable string with all authorized users and their expiration dates.
        Expired users will be highlighted with a warning symbol.
        
        :param field_names: The field names to be displayed in the table. Default: ["USER ID", "EXPIRES"]
        :param datetime_format: The format for the expiration date. Default: "%d/%m/%Y %H:%M"
        :return: The table as a string
        """

        users = self.store.get_authorized_users()
        table = PrettyTable(border=False, padding_width=0, preserve_internal_border=True)
        table.field_names = field_names

        for user in users:
            user_id, expires = user
            expires_str = expires.strftime(datetime_format)
            if expires < datetime.now():
                # Highlight expired users
                table.add_row([f"{user_id}", f"{expires_str} ⚠️"])
            else:
                table.add_row([user_id, expires_str])
        
        return str(table)
    
    def remaining_time(self, user_id: int) -> Tuple[int, int, int]:
        """
        Returns the number of days, hours, and minutes remaining for the specified user.
        
        :param user_id: The user's ID
        :return: A tuple containing the number of days, hours, and minutes remaining. 
                 If the user is not authorized or has expired, all values will be 0.
        """
        days, hours, minutes = 0, 0, 0
        
        user = self.store.get_authorized_user(user_id)

        if user is not None:
            user_id, expires = user
            remaining = expires - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60

        return days, hours, minutes

    def _insert_user(self, user_id: int, expires: datetime):
        """
        Inserts a new user in the store.
        
        :param user_id: The user's ID
        :param expires: The new expiration date for the user
        """
        self.store.insert_user(user_id, expires)
    
    def _update_user(self, user_id: int, expires: datetime):
        """
        Updates the expiration date for the specified user.
        
        :param user_id: The user's ID
        :param expires: The new expiration date for the user
        """
        self.store.update_user(user_id, expires)
