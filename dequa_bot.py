"""
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging
from uuid import uuid4
import requests
import json
import pdb
from dotenv import load_dotenv
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
API_TOKEN = os.getenv("API_TOKEN")

# Other useful variables
BASE_URL = "https://www.dequa.it/"
API_ADDRESS = "https://www.dequa.it/api/address"

# Steps for conversation handler
ADDRESS = range(1)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Ciao!')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Search an address in venice, e.g. "/address San Marco 1"')


def command_search_address(update: Update, context: CallbackContext) -> int:
    """Send the command /address optionally followed by the address"""
    address2search = ' '.join(context.args)
    if not address2search.strip():
        update.message.reply_text("Write me an address in Venice and I will give you the location!\nOr type /cancel if you don't want to search an address anymore.")
        return ADDRESS
    else:
        return search_address(update, context, address2search)


def conversation_search_address(update: Update, context: CallbackContext) -> int:
    """Find an address after sending the command /address"""
    address2search = update.message.text
    return search_address(update, context, address2search)


def search_address(update: Update, context: CallbackContext, address2search) -> int:
    """Find an address in venice."""
    head = {'Authorization': "Bearer " + API_TOKEN}
    r = requests.get(API_ADDRESS, headers=head, data={"address": address2search})
    if r.status_code != 200:
        update.message.reply_text("Address not found :(")
        return ConversationHandler.END
    response = json.loads(r.text)
    if response['ResponseCode'] != 0:
        update.message.reply_text("Address not found :(")
        return ConversationHandler.END
    else:
        url_button = [
            [InlineKeyboardButton(text="Open on DeQua", url=f"{BASE_URL}?partenza={address2search}")]
        ]

        reply_markup = InlineKeyboardMarkup(url_button)
        data = response['ResponseData']
        update.message.reply_location(latitude=data['latitude'],
                                      longitude=data['longitude'],
                                      reply_markup=reply_markup)
        return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Abort the search of an address"""
    update.message.reply_text("No problem, bye!")
    return ConversationHandler.END

# def inlinequery(update: Update, context: CallbackContext) -> None:
#     """Handle the inline query."""
#     query = update.inline_query.query
#     results = [
#         InlineQueryResultArticle(
#             id=uuid4(), title="Caps", input_message_content=InputTextMessageContent(query.upper())
#         ),
#         InlineQueryResultArticle(
#             id=uuid4(),
#             title="Bold",
#             input_message_content=InputTextMessageContent(
#                 f"*{escape_markdown(query)}*", parse_mode=ParseMode.MARKDOWN
#             ),
#         ),
#         InlineQueryResultArticle(
#             id=uuid4(),
#             title="Italic",
#             input_message_content=InputTextMessageContent(
#                 f"_{escape_markdown(query)}_", parse_mode=ParseMode.MARKDOWN
#             ),
#         ),
#     ]
#
#     update.inline_query.answer(results)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    # dispatcher.add_handler(CommandHandler("address", start_search_address))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('address', command_search_address)],
        states={
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, conversation_search_address)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)

    # on noncommand i.e message - echo the message on Telegram
    # dispatcher.add_handler(InlineQueryHandler(inlinequery))

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
