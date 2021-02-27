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
import ipdb
from dotenv import load_dotenv
import os
import yaml

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackContext
from telegram.ext import ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import PicklePersistence
from telegram.utils.helpers import escape_markdown

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
HEAD = {'Authorization': "Bearer " + API_TOKEN}

# Other useful variables
BASE_URL = "https://www.dequa.it/"
API_ADDRESS = "https://www.dequa.it/api/address"

# Steps for conversation handler
ADDRESS = range(1)

SETTINGS_MENU, SETTINGS_LANGUAGE = range(2)
SETTINGS_BASE, SETTINGS_END, LANGUAGE_MENU = range(3)
LANGUAGE_IT = 'it'
LANGUAGE_EN = 'en'

# Languages
localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
LOCALES = {
    LANGUAGE_IT: {
        "name": "italiano",
        "code": "it",
        "symbol": "\U0001F1EE\U0001F1F9",
        "file": "dequa_bot-it.yaml",
    },
    LANGUAGE_EN: {
        "name": "english",
        "code": "en",
        "symbol": "\U0001F1EC\U0001F1E7",
        "file": "dequa_bot-en.yaml",
    }
}
for lang in LOCALES.keys():
    with open(os.path.join(localedir, LOCALES[lang]["file"])) as stream:
        LOCALES[lang]["text"] = yaml.load(stream, Loader=yaml.FullLoader)
DEFAULT_LANG = str(LANGUAGE_EN)


def translate(string, lang=DEFAULT_LANG):
    """Translate a string in the required language"""
    # If the requested language is not available use the default one
    if lang not in LOCALES.keys():
        lang = DEFAULT_LANG

    # Check if the string is present in the current language
    if string in LOCALES[lang]["text"].keys():
        translation = LOCALES[lang]["text"][string]
    # Otherwise look for the string in the default language
    elif (lang != DEFAULT_LANG) and (string in LOCALES[DEFAULT_LANG]["text"].keys()):
        translation = LOCALES[DEFAULT_LANG]["text"][string]
    # Worst case: we use the input as output
    else:
        translation = string

    return translation


# Define the function translate with the alias _
_ = translate


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Make the bot persistent
my_persistence = PicklePersistence(filename='dequa-persistence.ptb')


def set_chat_language(update: Update, context: CallbackContext, language=None) -> None:
    """
    Set the language of a chat
    """
    if not language:
        language = update.effective_user.language_code

    if language in LOCALES.keys():
        selected_language = language
    else:
        selected_language = DEFAULT_LANG

    context.chat_data['lang'] = selected_language
    return


def get_lang(context: CallbackContext) -> str:
    """
    Get the current language
    """
    return context.chat_data.get('lang', DEFAULT_LANG)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    set_chat_language(update, context)
    lang = get_lang(context)
    update.message.reply_text(_('Ciao!', lang))


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    lang = get_lang(context)
    update.message.reply_text(_("help", lang))


def command_search_address(update: Update, context: CallbackContext) -> int:
    """Send the command /address optionally followed by the address"""
    lang = get_lang(context)
    address2search = ' '.join(context.args)
    if not address2search.strip():
        update.message.reply_text(_("search address", lang))
        return ADDRESS
    else:
        return search_address(update, context, address2search)


def conversation_search_address(update: Update, context: CallbackContext) -> int:
    """Find an address after sending the command /address"""
    address2search = update.message.text
    return search_address(update, context, address2search)


def search_address(update: Update, context: CallbackContext, address2search) -> int:
    """Find an address in venice."""
    lang = get_lang(context)
    r = requests.get(API_ADDRESS, headers=HEAD, data={"address": address2search})
    if r.status_code != 200:
        update.message.reply_text(_("Address not found :(", lang))
        return ConversationHandler.END
    response = json.loads(r.text)
    if response['ResponseCode'] != 0:
        update.message.reply_text(_("Address not found :(", lang))
        return ConversationHandler.END
    else:
        url_button = [
            [InlineKeyboardButton(text=_("Open on DeQua", lang), url=f"{BASE_URL}?partenza={address2search}")]
        ]

        reply_markup = InlineKeyboardMarkup(url_button)
        data = response['ResponseData']
        update.message.reply_location(latitude=data['latitude'],
                                      longitude=data['longitude'],
                                      reply_markup=reply_markup)
        return ConversationHandler.END


def settings(update: Update, context: CallbackContext) -> int:
    """Settings view"""
    lang = get_lang(context)
    keyboard = [
        [
            InlineKeyboardButton(text="\N{globe with meridians}", callback_data=str(LANGUAGE_MENU))
        ],
        [
            InlineKeyboardButton(text=_("Done!", lang), callback_data=str(SETTINGS_END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(_("settings", lang),
                              reply_markup=reply_markup)
    return SETTINGS_MENU


def settings_menu(update: Update, context: CallbackContext) -> int:
    """The same as settings but not as new message"""
    lang = get_lang(context)
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton(text="\N{globe with meridians}", callback_data=str(LANGUAGE_MENU))
        ],
        [
            InlineKeyboardButton(text=_("Done!", lang), callback_data=str(SETTINGS_END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(_("settings", lang),
                            reply_markup=reply_markup)
    return SETTINGS_MENU


def settings_end(update: Update, context: CallbackContext) -> int:
    """Close the settings conversation"""
    lang = get_lang(context)
    query = update.callback_query
    query.answer
    query.edit_message_text(_("New settings are saved! Bye!", lang))
    return ConversationHandler.END


def settings_language(update: Update, context: CallbackContext) -> int:
    """ Show language buttons """
    lang = get_lang(context)
    # Get CallbackQuery from Update
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton(text=LOCALES[str(LANGUAGE_IT)]['symbol'], callback_data=str(LANGUAGE_IT)),
            InlineKeyboardButton(text=LOCALES[str(LANGUAGE_EN)]['symbol'], callback_data=str(LANGUAGE_EN)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_lang = context.chat_data.get('lang', None)
    if not user_lang:
        curr_lang = _("not set", lang)
    else:
        curr_lang = LOCALES[user_lang]['name']

    query.edit_message_text(_("current language", lang).format(curr_lang), reply_markup=reply_markup)
    return SETTINGS_LANGUAGE


def choose_language(update: Update, context: CallbackContext) -> int:
    """ Choose the selected language """
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    lang = LOCALES.get(query.data, DEFAULT_LANG)

    set_chat_language(update, context, lang['code'])

    lang_txt = get_lang(context)

    keyboard = [
        [
            InlineKeyboardButton(text=_("« Back to settings", lang_txt), callback_data=str(SETTINGS_BASE))
        ],
        [
            InlineKeyboardButton(text=_("Done!", lang_txt), callback_data=str(SETTINGS_END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(_("language updated", lang_txt).format(lang['name']), reply_markup=reply_markup)
    return SETTINGS_MENU


def cancel(update: Update, context: CallbackContext) -> int:
    """Abort the search of an address"""
    lang = get_lang(context)
    update.message.reply_text(_("No problem, bye!", lang))
    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, persistence=my_persistence)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    #dispatcher.add_handler(CommandHandler("settings", settings))
    # dispatcher.add_handler(CommandHandler("address", start_search_address))

    address_handler = ConversationHandler(
        entry_points=[CommandHandler('address', command_search_address)],
        states={
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, conversation_search_address)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(address_handler)

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler('settings', settings)],
        states={
            SETTINGS_MENU: [
                CallbackQueryHandler(settings_menu, pattern='^' + str(SETTINGS_BASE) + '$'),
                CallbackQueryHandler(settings_end, pattern='^' + str(SETTINGS_END) + '$'),
                CallbackQueryHandler(settings_language, pattern='^' + str(LANGUAGE_MENU) + '$')
            ],
            SETTINGS_LANGUAGE: [
                CallbackQueryHandler(choose_language)
            ]
        },
        fallbacks=[CommandHandler('cancel', settings_end)]
    )
    dispatcher.add_handler(settings_handler)

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
