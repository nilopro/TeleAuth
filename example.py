from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update, ParseMode
from dotenv import load_dotenv
from teleauth import Auth
import os
import logging


def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi! I'm a simple Telegram bot that demonstrates user authentication.Type /auth to authorize a user, /unauth to revoke access, or /authorized_users to see a list of authorized users.")
    
    user_id = update.effective_user.id
    
    if not auth.is_authenticated(user_id):
        update.message.reply_text("You are not authenticated.")
        return

    remaining = auth.remaining_time(user_id)

    days, hours, minutes = remaining
    text = (
        "You are authenticated!\n"
        f"{days} days, {hours} hours, and {minutes} minutes remaining"
    )
    update.message.reply_text(text)

        
def auth_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not auth.is_admin(user_id):
        update.message.reply_text("You are not authorized to use this command.")
        return

    # Get the number of days and hours from the command arguments
    try:
        days = int(context.args[0])
        hours = int(context.args[1])
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /auth <days> <hours> <user_id>")
        return

    # Authorize the user specified in the command
    try:
        target_user_id = int(context.args[2])
        auth.authorize_user(target_user_id, days, hours)
        update.message.reply_text(f"User {target_user_id} has been authorized for {days} days and {hours} hours.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /auth <days> <hours> <user_id>")
        return


def unauth_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not auth.is_admin(user_id):
        update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        target_user_id = int(context.args[0])
        auth.revoke_access(target_user_id)
        update.message.reply_text(f"Access for user {target_user_id} has been revoked.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /unauth <user_id>")
        return


def authorized_users(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not auth.is_admin(user_id):
        update.message.reply_text("You are not authorized to use this command.")
        return

    table = auth.get_authorized_users_table()
    update.message.reply_text(f"Authorized users:\n<pre>{table}</pre>", parse_mode=ParseMode.HTML)

    

def echo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not auth.is_authenticated(user_id):
        update.message.reply_text("You are not authorized to use this bot.")
        return

    update.message.reply_text(update.message.text)

        

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.environ["ADMINS"].split(",")))

auth = Auth(ADMINS)

# Set up the updater and the dispatcher
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Add command handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("auth", auth_user))
dispatcher.add_handler(CommandHandler("unauth", unauth_user))
dispatcher.add_handler(CommandHandler("authorized_users", authorized_users))

# Add message handler
dispatcher.add_handler(MessageHandler(Filters.text, echo))

# Start the bot
updater.start_polling()

# Run the bot until the user interrupts the program
updater.idle()

# Close the database connection
auth.close()