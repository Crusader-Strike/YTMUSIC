import requests
import bs4
import time
import re
import os
from moviepy.editor import VideoFileClip
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram import Update
from utils import log_handling
def download_and_send_video(update: Update, context: CallbackContext, url, downloading_msg, delete_video: bool = True):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id

    post_shortcode = url.split("/")
    shortcode = post_shortcode[4]

    context.bot.edit_message_text(chat_id=chat_id, message_id=downloading_msg.message_id, text='Downloading ...')
    response = requests.get(url)
    if response.status_code == 200:
        with open(f"{shortcode}.mp4", "wb") as file:
            file.write(response.content)
        with open(f"{shortcode}.mp4", "rb") as video_file:
            context.bot.edit_message_text(chat_id=chat_id, message_id=downloading_msg.message_id, text='Sending ...')
            dump_file = context.bot.send_video(chat_id, video_file, supports_streaming=True, reply_to_message_id=message_id)
        if os.path.exists(file.name) and delete_video:
            os.remove(f"{shortcode}.mp4")

def convert_video_to_audio(update: Update, context: CallbackContext, video_path, downloading_msg, output_ext="mp3", delete_video: bool = True):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id

    post_shortcode = video_path.split("/")
    shortcode = post_shortcode[4]
    context.bot.edit_message_text(chat_id=chat_id, message_id=downloading_msg.message_id, text='Downloading ...')
    response = requests.get(video_path)
    if response.status_code == 200:
        with open(f"{shortcode}.mp4", "wb") as file:
            file.write(response.content)
        context.bot.edit_message_text(chat_id=chat_id, message_id=downloading_msg.message_id, text='Downloaded')
        filename, ext = os.path.splitext(file.name)
        context.bot.edit_message_text(chat_id=chat_id, message_id=downloading_msg.message_id, text='Converting ...')
        with VideoFileClip(file.name) as clip:
            clip.audio.write_audiofile(f"{filename}.{output_ext}")

        try:
            context.bot.edit_message_text(chat_id=chat_id, message_id=downloading_msg.message_id, text='Sending ...')
            file_path = f"{filename}.{output_ext}"
            context.bot.send_audio(chat_id, open(file_path, 'rb'), reply_to_message_id=message_id)
        except Exception as e:
            print(f"Error sending audio file: {e}")

        if os.path.exists(file.name) and delete_video:
            os.remove(file.name)
            os.remove(f"{shortcode}.mp3")

def download_instagram_post(update: Update, context: CallbackContext, url, user_message_id = None, audio=False, first_time=True):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    #url = url.replace("==", "%3D%3D")
    content_value = url.replace("www.", "d.dd")

    #log_handling(update, 'info', 'Found instagram link')
    #log(update, user_url, 'instagram',context)
    #content_value = url.replace("www.", "d.dd")
    if first_time:
        response = requests.get(content_value)
        if response.status_code == 200:
            # Determine the content type
            content_type = response.headers.get('Content-Type', '')
            # Ask user whether to download video or audio
            if 'video' in content_type:
                reply_text = "Do you want to download video or audio?"

                keyboard = [
                    [InlineKeyboardButton("Video", callback_data="video_download"), InlineKeyboardButton("Audio", callback_data="audio_download")]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text, reply_markup=reply_markup)
                return
            else:
                log_handling(update, 'info', 'found image and sent to telegram')
                update.effective_message.reply_photo(content_value,quote=True,reply_to_message_id=update.message.message_id,allow_sending_without_reply=True)

    msg = context.bot.send_message(chat_id, "Downloading from Instagram ...")

    try:
        ddinsta = True
        try:
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text='Searching Link ... (try 1)')
            
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text='Got Link')

        except:
            pass
        try:
            if ddinsta:
                if audio:
                    convert_video_to_audio(update, context, content_value, msg)
                else:
                    #dump_file = context.bot.send_video(chat_id, content_value, supports_streaming=True, reply_to_message_id=message_id)
                    # delete 'got link' message
                    context.bot.delete_message(chat_id, msg.message_id)

                    update.effective_message.reply_video(content_value, supports_streaming=True,quote=True,reply_to_message_id=user_message_id,allow_sending_without_reply=True)
        except Exception as e:
            print(e)
            pass
    except KeyError:
        context.bot.send_message(chat_id, f"400: Sorry, Unable To Find It Make Sure Its Publically Available :)", reply_to_message_id=message_id,allow_sending_without_reply=True)
