"""
The `teleauth` package provides a flexible and easy-to-use authorization system for Telegram bots.

It allows you to authenticate users, authorize access for a certain amount of time, and check if a user is an admin. 

The package also allows you to choose between using SQLite or JSON to store the authorization data.

Examples
--------

Creating a simple Telegram bot using the teleauth package:

```python
from telegram.ext import Updater, CommandHandler
from teleauth import Auth

# Initialize the authorization system with a list of authorized admin IDs
auth = Auth([123456789])

def start(update, context):
    user_id = update.message.from_user.id
    if auth.is_authenticated(user_id):
        update.message.reply_text("You are authenticated.")
    else:
        update.message.reply_text("You are not authenticated.")

def authorize(update, context):
    user_id = update.message.from_user.id
    auth.authorize_user(user_id, days=1, hours=2)
    update.message.reply_text("Access granted for 1 day and 2 hours.")

def revoke(update, context):
    user_id = update.message.from_user.id
    auth.revoke_access(user_id)
    update.message.reply_text("Access revoked.")

def authorized_users(update, context):
    table = auth.get_authorized_users_table()
    update.message.reply_text(f"Authorized users:\n{table}")

updater = Updater("TOKEN", use_context=True)

updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("authorize", authorize))
updater.dispatcher.add_handler(CommandHandler("revoke", revoke))
updater.dispatcher.add_handler(CommandHandler("authorized_users", authorized_users))

updater.start_polling()
updater.idle()
"""


from .auth import Auth
from .store import IStore, StoreType

from .auth import *
from .store import *

__all__ = [
    # Expose classes and functions from auth module
    'Auth',
    # Expose classes and functions from store module
    'StoreType',
]