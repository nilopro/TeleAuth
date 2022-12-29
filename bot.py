import logging
import os
import sqlite3
import datetime
from typing import List, Tuple
from prettytable import PrettyTable
from dotenv import load_dotenv
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ParseMode
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.environ["ADMINS"].split(",")))

class Authentication:
    def __init__(self, authorized_admin_ids: List[int]):
        self.authorized_admin_ids = authorized_admin_ids
        self.conn = sqlite3.connect("users.db", check_same_thread=False,
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

        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result is not None:
            user_id, expires = result
            if expires > datetime.now():
                return True

        return False

    def remaining_time(self, user_id: int) -> Tuple[int, int, int]:
        self.cursor.execute("SELECT expires FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        if result is not None:
            expires = result[0]
            remaining = expires - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            return days, hours, minutes
        else:
            return 0, 0, 0
    
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
    
    def get_authorized_users_table(self, datetime_format:str="%d/%m/%Y %H:%M") -> str:
        users = self.get_authorized_users()
        
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

        
# Constants
class AuthenticationCallbacks:
    MENU = "AUTHORIZATION"
    AUTHORIZE = "AUTHORIZE"
    AUTHORIZE_HOURS = "AUTHORIZE_HOURS"
    LIST = "LIST_USERS"
    REVOKE = "REVOKE"

 

# Define the /start command handler
def start(update: Update, context):
    # Get the user's ID
    user_id = update.effective_user.id
    
    # Check if the user is authenticated
    if auth.is_authenticated(user_id):
        # If the user is authenticated, show the main menu
        
        remaining = auth.remaining_time(user_id)
   
        days, hours, minutes = remaining
        text = (
            "✅ You are authenticated!\n"
            f"{days} days, {hours} hours, and {minutes} minutes remaining"
        )

        main_menu_keyboard = [[KeyboardButton("AUTH", callback_data=AuthenticationCallbacks.MENU)]] 
        keyboard = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True) if auth.is_admin(user_id) else None
        update.message.reply_text(text, reply_markup=keyboard)
    
    else:
        update.message.reply_text("You are not authenticated. Only authorized users can use this bot.")

# Define the /help command handler
def help(update: Update, context):
    update.message.reply_text("This is a simple authentication bot. Only authorized users can use it.")

# Define the message handler
def auth_menu(update: Update, context):
    # Auth menu keyboard
    keyboard = [
        [InlineKeyboardButton("Authorize user", callback_data=AuthenticationCallbacks.AUTHORIZE)],
        [InlineKeyboardButton("Authorize user for hours", callback_data=AuthenticationCallbacks.AUTHORIZE_HOURS)],
        [InlineKeyboardButton("List authorized users", callback_data=AuthenticationCallbacks.LIST)],
        [InlineKeyboardButton("Revoke access", callback_data=AuthenticationCallbacks.REVOKE)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Show the auth menu
    update.message.reply_text("AUTH:", reply_markup=reply_markup)

# Define the callback query handler
def auth_callback(update: Update, context):

    # Get the user's ID
    user_id = update.effective_user.id
    
    # Check if the user has admin privileges
    if user_id not in auth.authorized_admin_ids:
        # If the user does not have admin privileges, do nothing
        return
    
    # Get the callback data
    query = update.callback_query
    data = query.data
    
    if data == AuthenticationCallbacks.AUTHORIZE:
        # Ask the user for the user ID to authorize
        query.edit_message_text("Enter the user ID and number of days to authorize (separated by a space):")
    elif data == AuthenticationCallbacks.AUTHORIZE_HOURS:
        # Ask the user for the user ID and number of hours to authorize
        query.edit_message_text("Enter the user ID and number of hours to authorize (separated by a space):")
    elif data == AuthenticationCallbacks.LIST:
        # Get the table of authorized users
        table = auth.get_authorized_users_table()
        query.edit_message_text(f"<pre>{table}</pre>", parse_mode=ParseMode.HTML)
    elif data == AuthenticationCallbacks.REVOKE:
        # Ask the user for the user ID to revoke
        query.edit_message_text("Enter the user ID to revoke access:")

    context.user_data["state"] = data


# Define the message handler
def message(update: Update, context):
    # Get the user's ID
    user_id = update.effective_user.id
    
    # Check if the user has admin privileges
    if user_id not in auth.authorized_admin_ids:
        # If the user does not have admin privileges, do nothing
        return
    
    # Get the user's input
    input_str = update.message.text
    
    # Check the current state
    state = context.user_data.get("state")
    
    if state == AuthenticationCallbacks.AUTHORIZE:
        # Parse the input
        try:
            user_id, days = map(int, input_str.split())
        except ValueError:
            update.message.reply_text("Invalid input. Please try again.")
            return
        
        # Authorize the user for the specified number of days
        auth.authorize_user(user_id, days=days, hours=0)
        update.message.reply_text(f"User {user_id} has been authorized for {days} days.")
    elif state == AuthenticationCallbacks.AUTHORIZE_HOURS:
        # Parse the input
        try:
            user_id, hours = map(int, input_str.split())
        except ValueError:
            update.message.reply_text("Invalid input. Please try again.")
            return
        
        # Authorize the user for the specified number of hours
        auth.authorize_user(user_id, days=0, hours=hours)
        update.message.reply_text(f"User {user_id} has been authorized for {hours} hours.")
    elif state == AuthenticationCallbacks.REVOKE:
        # Parse the input
        try:
            user_id = int(input_str)
        except ValueError:
            update.message.reply_text("Invalid input. Please try again.")
            return
        
        # Revoke access from the user
        auth.revoke_access(user_id)
        update.message.reply_text(f"Access has been revoked for user {user_id}.")
    else:
        update.message.reply_text(f"Invalid state {state}. Please try again.")

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Set up the Updater
updater = Updater(BOT_TOKEN, use_context=True)

# Set up the authentication instance
auth = Authentication(ADMINS)

# Get the dispatcher
dispatcher = updater.dispatcher

# Add the command handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help))

# Add the callback query handler
pattern = f"^({AuthenticationCallbacks.AUTHORIZE}|{AuthenticationCallbacks.AUTHORIZE_HOURS}|{AuthenticationCallbacks.LIST}|{AuthenticationCallbacks.REVOKE})$"
dispatcher.add_handler(CallbackQueryHandler(auth_callback, pattern=pattern))

# Add message handlers
dispatcher.add_handler(MessageHandler(Filters.text("AUTH"), auth_menu))
dispatcher.add_handler(MessageHandler(Filters.text, message))

# Start the bot
updater.start_polling()

# Run the bot until the user interrupts the program
updater.idle()

# Close the database connection
auth.close()
