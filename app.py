import os
import json
import html
import logging
import requests
import traceback
import threading
from queue import Queue
from io import StringIO
from dotenv import load_dotenv
from youtube_search import YoutubeSearch
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ChatAction,
    BotCommand, BotCommandScopeChat, InlineQueryResultArticle, InputTextMessageContent
)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler,
    CallbackContext, InlineQueryHandler, ChosenInlineResultHandler
)
import telegram.error
import config
from utils import log_handling
from instagram_download import download_instagram_post
from youtube_download_inline import download_video
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

user_urls = {}
load_dotenv()

# Set up download queue
download_queue = Queue()

class APIException(Exception):
    pass

# Define the file path to store chat IDs
chat_ids_file = 'chat_ids.txt'

# Load existing chat IDs from the file
try:
    with open(chat_ids_file, 'r') as file:
        chat_ids = file.read().splitlines()
except FileNotFoundError:
    chat_ids = []


def debounce(delay, func):
    timer = None
    def wrapper(*args, **kwargs):
        nonlocal timer
        if timer is not None:
            timer.cancel()
        timer = threading.Timer(delay, func, args, kwargs)
        timer.start()
    return wrapper

def inline_search(update: Update, context: CallbackContext):
    query = update.inline_query.query
    search_results = YoutubeSearch(query).to_dict()
    log_handling(update, 'info', f'Searching for keyword: {query}')
    
    inline_results = []

    def format_views(views):
        if views >= 1000000:
            return f"{views // 1000000}m"
        elif views >= 1_000:
            return f"{views // 1000}k"
        return str(views)
    
    for video in search_results:
        video_title = video['title']
        video_duration = video['duration']
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        video_id = video['id']
        video_thumb = video['thumbnails'][0]
        video_views = format_views(int(re.sub(r'[^\d]', '', video['views'])))
        
        inline_result = InlineQueryResultArticle(
            id=video_id,
            title=video_title,
            description=f"{video_duration} - {video_views} views",
            thumb_url = video_thumb,
            input_message_content=InputTextMessageContent(video_url)
        )
        
        inline_results.append(inline_result)
    
    context.bot.answer_inline_query(update.inline_query.id, inline_results)
    log_handling(update, 'info', 'Displayed search results')
# Helper function to save chat IDs to the file
def save_chat_ids():
    with open(chat_ids_file, 'w') as file:
        for chat_id in chat_ids:
            file.write(str(chat_id) + '\n')

def broadcast_message(update: Update, context: CallbackContext) -> None:
    """Broadcast a message to all saved chat IDs."""
    if update.effective_user.id != config.DEVELOPER_ID:
        return

    message_text = update.message.text.split('/all ', 1)[1]

    for chat_id in chat_ids:
        try:
            chat_info = context.bot.get_chat(chat_id=int(chat_id))
            if chat_info.type in [telegram.Chat.PRIVATE, telegram.Chat.GROUP]:
                context.bot.send_message(chat_id=int(chat_id), text=message_text)
        except telegram.error.TelegramError:
            pass

def start_command(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    chat_id = update.effective_chat.id
    if str(chat_id) not in chat_ids:
        chat_ids.append(str(chat_id))
        save_chat_ids()

    start_message = (
        "*لینک ویدیو یوتیوب / اسم خواننده / اسم آهنگ /لینک پست / ریلز و استوری اینستاگرام رو واسم بفرست تا واست دانلود کنم*\n\n"
        "_Created by_ [AKB](https://github.com/Crusader-Strike/)"
    )
    context.bot.send_message(
        chat_id=chat_id,
        text=start_message,
        parse_mode=telegram.ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    username_message = context.bot.send_message(
        chat_id=chat_id,
        text=f"Hello! I'm `@{context.bot.username} `. You can copy my username by tapping on it.",
        parse_mode=telegram.ParseMode.MARKDOWN,
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle the /help command."""
    help_message = (
    "خوش آمدید به ربات دانلود موسیقی یوتیوب!\n\n"
    "برای دانلود موسیقی از یوتیوب، مراحل زیر را دنبال کنید:\n\n"
    "1. لینک ویدیوی یوتیوب را به ربات ارسال کنید.\n"
    "2. ربات دانلود موسیقی را شروع می‌کند و آن را برای شما ارسال می‌کند.\n\n"
    f"همچنین می‌توانید از ویژگی جستجوی درون خطی برای یافتن و دانلود موسیقی مستقیماً از ربات استفاده کنید. برای این کار، `@{context.bot.username}` را همراه با نام آهنگ یا نام هنرمند تایپ کنید و ربات لیست نتایج جستجو را نمایش می‌دهد.\n\n"
    f"`@{context.bot.username}`مثال:  آهنگ تولدت مبارک"

)
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_message, parse_mode=telegram.ParseMode.MARKDOWN)


def handle_private_messages(update: Update, context: CallbackContext):
    try:
        log_handling(update, 'info', 'Received message: ' + update.effective_message.text.replace("\n", ""))

        if update.effective_chat.type in ['private']:
            user_url = update.message.text if update.message else update.edited_message.text if update.edited_message else None
            if update.effective_message.via_bot is not None and update.effective_message.via_bot.is_bot and update.effective_message.text and not update.effective_message.caption:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)

        elif update.effective_chat.type == 'group':
            user_url = update.message.text if update.message else update.edited_message.text if update.edited_message else None
            if update.effective_message.via_bot is not None and update.effective_message.via_bot.is_bot and update.effective_message.text and not update.effective_message.caption:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
        
        elif update.effective_chat.type == 'supergroup':
            user_url = update.message.text if update.message else update.edited_message.text if update.edited_message else None
            if update.effective_message.via_bot is not None and update.effective_message.via_bot.is_bot and update.effective_message.text and not update.effective_message.caption:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)

        elif update.effective_chat.type == 'channel':
            #if its channel_post
            user_url = update.channel_post.text if update.channel_post else update.edited_channel_post.text if update.edited_channel_post else None
            if update.channel_post is not None and update.channel_post.via_bot is not None and update.channel_post.via_bot.is_bot and update.channel_post.text and not update.channel_post.caption:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.channel_post.message_id)
                
        chat_id = update.effective_chat.id
        if str(chat_id) not in chat_ids:
            chat_ids.append(str(chat_id))
            save_chat_ids()

        #user_url_message  = update.message if update.message else update.edited_message
        global user_urls
        user_urls[update.effective_chat.id] = {'user_url_message_id': update.effective_message.message_id, 'user_url': user_url}
        context.bot.send_chat_action(chat_id=update.effective_chat.id, timeout = 60, action=ChatAction.CHOOSE_STICKER)
        if 'instagram' in user_url:
            if chat_id != config.logs:
                log_handling(update, 'info', 'Found instagram link')
                log_request(update, user_url, 'instagram',context)
                download_queue.put((update, context, user_url))
                threading.Thread(target=download_instagram_post, args=(update, context, user_url)).start()
                #download_instagram_post(update, context, user_url)
            else:
                return
        elif 'youtube' in user_url:
            if chat_id != config.logs:
                log_handling(update, 'info', 'found youtube link')
                log_request(update, user_url, 'Youtube Link',context)
                download_queue.put((update, context))
                threading.Thread(target=download_video, args=(update, context)).start()
                #download_video(update, context)
                return
            else:
                return
    except telegram.error.Unauthorized:
        log_handling(update, 'error', 'Unauthorized access')
    except telegram.error.Conflict:
        log_handling(update, 'error', 'Conflict error')
    except Exception as e:
        log_handling(update, 'error', 'Error: ' + str(e))
        pass


def handle_callback_query(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    user_url = update.callback_query.data
    user_url_message_id = user_urls[user_id].get('user_url_message_id')
    user_url = user_urls[user_id].get('user_url')
    if user_url:
        if update.callback_query.data == 'video_download':
            log_handling(update, 'info', 'Selected video download')
            download_instagram_post(update, context, user_url,user_url_message_id, audio=False, first_time=False)
        elif update.callback_query.data == 'audio_download':
            log_handling(update, 'info', 'Selected audio download')
            download_instagram_post(update, context, user_url,user_url_message_id, audio=True, first_time=False)

def log_request(update: Update, message: str, media_type: str, context: CallbackContext):
    if update.effective_chat.id != config.logs:
        if update.effective_chat.type == 'private':
            chat_details = "Private chat"
            log_message = (
                f"Download request ({media_type}) from "
                f"@{update.effective_user.username} ({update.effective_user.id})\n\n"
                f"{chat_details}\n\n{message}"
            )
        else:
            chat_details = f"Group: *{update.effective_chat.title}* (`{update.effective_chat.id}`)"
            log_message = (
                f"Download request ({media_type})\n\n"
                f"{chat_details}\n\n{message}"
            )
        context.bot.send_message(chat_id=config.logs, text = log_message)

def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""

    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    if isinstance(context.error, telegram.error.Unauthorized):
        return

    if isinstance(context.error, telegram.error.Conflict):
        logger.error("Telegram requests conflict")
        return

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        f'#error_report\n'
        f'An exception was raised in runtime\n'
        f'<pre>{html.escape(json.dumps(update.to_dict() if isinstance(update, Update) else str(update), indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>{html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>{html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_document(chat_id=config.logs, document=StringIO(message), filename='error_report.txt',
                              caption='#error_report\nAn exception was raised in runtime\n')

    if update:
        error_class_name = ".".join([context.error.__class__.__module__, context.error.__class__.__qualname__])
        context.bot.send_message(chat_id=config.logs, text=f'Error\n{error_class_name}: {str(context.error)}')

def main():
    """Main entry point of the script."""
    updater = Updater(os.getenv('TOKEN'), use_context=True)

    dispatcher = updater.dispatcher
    debounced_inline_search = debounce(2, inline_search)  # 0.5 seconds delay
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('all', broadcast_message))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_private_messages))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))
    dispatcher.add_handler(InlineQueryHandler(debounced_inline_search, run_async=True))
    dispatcher.add_error_handler(error_handler)

    # Set commands menu
    public_commands = [
        BotCommand('start', 'Start the bot'),
        BotCommand('help', 'Help message'),
    ]
    dev_commands = public_commands + [BotCommand('all', 'Send chat to all members')]
    try:
        updater.bot.set_my_commands(public_commands)
        updater.bot.set_my_commands(dev_commands, scope=BotCommandScopeChat(config.DEVELOPER_ID))
    except telegram.error.BadRequest as exc:
        logger.warning(f'Couldn\'t set my commands for developer chat: {exc.message}')

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()