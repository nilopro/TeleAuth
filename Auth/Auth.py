from typing import List, Tuple
from prettytable import PrettyTable
from Auth.Store import IStore
from datetime import datetime

class Authentication:
    def __init__(self, store: IStore):
        self.store = store
    
    def close(self):
        self.store.close()

    def is_admin(self, user_id: int) -> bool:
        return self.store.is_admin(user_id)
    
    def is_authenticated(self, user_id: int) -> bool:
        return self.store.is_authenticated(user_id)
    
    def authorize_user(self, user_id: int, days: int, hours: int):
        self.store.authorize_user(user_id, days, hours)
    
    def revoke_access(self, user_id: int):
        self.store.revoke_access(user_id)
    
    def get_authorized_users_table(self, datetime_format:str="%d/%m/%Y %H:%M") -> str:
        users = self.store.get_authorized_users()
        table = PrettyTable(border=False, padding_width=0, preserve_internal_border=True)
        table.field_names = ["USER ID", "EXPIRA EM"]

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
        days, hours, minutes = 0, 0, 0
        
        user = self.store.get_authorized_user(user_id)

        if user is not None:
            user_id, expires = user
            remaining = expires - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60

        return days, hours, minutes
