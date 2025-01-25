from telegram.ext import CallbackContext
from telegram import Update, ParseMode, ChatAction
from pytubefix import YouTube
from pytubefix.cli import on_progress
import generate
from typing import Tuple
import os
import config
import ffmpeg
'''from mutagen.id3 import ID3, TPE1
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3'''
from utils import log_handling
import requests
import re

#import sys
#sys.path.insert(0, '/persian-to-finglish/')
#from persian_to_finglish import bestPersianTofinglish as finglish
from youtube_title_parse import get_artist_title
    #log_handling(update, 'info', 'Showing search results')

def remove_non_english_chars(s):
    return re.sub(r'[^\x00-\x7F]+', '', s)

def po_token_verifier() -> Tuple[str, str]:
        token_object = {}
        token_object["visitorData"] = generate.generate_visitorData()
        token_object["poToken"] = generate.generate_poToken(generate.secret_key)
        return token_object["visitorData"], token_object["poToken"]

def download_video(update: Update, context: CallbackContext, url = None):
    #update.callback_query.message
    #bot = context.bot
    
    context.bot.send_chat_action(chat_id=update.effective_chat.id, timeout = 60, action=ChatAction.FIND_LOCATION)
    log_handling(update, 'info', 'fetch video information')
    # Send a sticker while fetching information
    emoji_message = context.bot.send_message(chat_id=update.effective_chat.id, text='🔍')
    
    yt = YouTube(update.effective_message.text,use_po_token=True,po_token_verifier=po_token_verifier)
    
    #url = update.message.text
    try:
        file_name = yt.title  # Get the title using backoff
        print("Downloading", file_name)
    except Exception as e:
        context.bot.send_message(chat_id=config.logs, text=f"Error fetching video title: {e}")
        return
    '''#video_id = urlparse(input_text).query.split('=')[1]
    video_id = urlparse(input_text).query.split('=')[1]
    #video_info = YoutubeDL().extract_info(url, download=False)
    #video_title = video_info['title']
    file_name = _get_description_with_backoff(yt)                               
    #msg = context.bot.send_message(chat_id=update.message.chat_id, text=f"Downloading... \n{file_name}")
    print("Downloading", file_name)'''

    try:
        log_handling(update, 'info', 'Downloading video')
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=emoji_message.message_id)
        emoji_message = context.bot.send_message(chat_id=update.effective_chat.id, text='⌛️')
        #file_name = re.sub(r'[^\x00-\x7F]+', '', file_name)
        
        # Remove all invalid characters and replace with space
        file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)
        # Replace all spaces with "-"
        #file_name = re.sub(r'\s+', '-', file_name)
        file_name = file_name.rstrip('- ')
        try:
            artist_name, track_name = get_artist_title(file_name)
        except Exception as e:
            print(e)
            # Extract artist name and track name
            match = re.search(r'^(.+?)\s*-\s*(.+)$', file_name)
            match2 = re.search(r'^(.+?)\s*-\s*(.+?)\s*-\s*.+$', file_name)
            parts = file_name.split('-')
            if match:
                artist_name = match.group(1).strip()
                track_name = match.group(2).strip()
                print("Artist:", artist_name)
                print("Track:", track_name)
            elif match2:
                artist_name = match.group(1).strip()
                track_name = match.group(2).strip()
                print("Artist:", artist_name)
                print("Track:", track_name)
            elif len(parts) > 1:
                artist_name = parts[0].strip()
                track_name = '-'.join(parts[1:]).strip()
                print("Artist:", artist_name)
                print("Track:", track_name)
            elif len(parts) == 1:
                try:
                    artist_name = yt.keywords[0].strip()
                    track_name = parts[0].strip()
                except:
                    artist_name = "Unknown Artist"
                    track_name = file_name
                    
            else:
                print("No match found")

        if any(c.isalpha() and c.isascii() for c in artist_name):
            artist_name = re.sub(r'[^\x00-\x7F-]+', '', artist_name)
        if any(c.isalpha() and c.isascii() for c in track_name):
            track_name = re.sub(r'[^\x00-\x7F()]+', '', track_name.replace('-', '').replace('(', '').replace(')', ''))
            track_name = track_name.strip()
        #artist_name = persian_to_finglish(artist_name)
        #track_name = persian_to_finglish(track_name)
        #artist_name = finglish.convert_text(artist_name)
        #track_name = finglish.convert_text(track_name)
        print(file_name)
        context.bot.send_chat_action(chat_id=update.effective_chat.id, timeout = 60, action=ChatAction.RECORD_AUDIO)
        video_path = YouTube(yt.watch_url,on_progress_callback=on_progress,use_po_token=True,po_token_verifier=po_token_verifier).streams.filter(only_audio=True).get_by_itag(140).download(filename=f"{file_name}.mp3")
        #file_name1  = file_name.replace('"','')
        '''try:
            # Open the M4A file
            input_file = ffmpeg.input(f"{file_name}.m4a")
            # Convert the audio to MP3
            output_file = ffmpeg.output(input_file, f"{file_name}.mp3", format="mp3", **{'y': None})
            # Run the conversion
            ffmpeg.run(output_file, capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
                print('stdout:', e.stdout.decode('utf8'))
                print('stderr:', e.stderr.decode('utf8'))
                raise e'''
        #context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=msg.message_id, text='Converting to audio...')
        #video_path = info['requested_downloads'][0]['filepath']
        #audio_path = f'outputs/{video_title}.mp3'
        #video_clip = VideoFileClip(video_path)
        #audio_clip = video_clip.audio
        #audio_clip.write_audiofile(audio_path)
        #audio_clip.close()
        #video_clip.close()
        def reduce_file_size(file_path, target_size_bytes):
            import subprocess
            quality = 112  # initial quality in kbps
            step = 16  # step to decrease quality in kbps
            while True:
                command = [
                    'ffmpeg',
                    '-y',  # force overwriting output file
                    '-i', f'{file_path}.mp3',
                    '-c:a', 'libmp3lame',
                    f'-b:a', f'{quality}k',
                    '-ar', '22050',
                    f'{file_path}_reduced.mp3'
                ]
                subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output_size = os.path.getsize(f"{file_path}_reduced.mp3")
                if output_size < target_size_bytes:
                    os.remove(f"{file_path}.mp3")
                    os.rename(f"{file_path}_reduced.mp3", f"{file_path}.mp3")
                    break
                quality -= step
                if quality < 16:  # minimum quality in kbps
                    raise Exception("Unable to reduce file size to target size")
                os.remove(f"{file_path}_reduced.mp3")
        #video_path = YouTube(yt.watch_url).streams.filter(only_audio=True).first().download(filename=f'{video_title}.mp3')
        log_handling(update, 'info', 'check audio file size')
        file_size = os.path.getsize(f"{file_name}.mp3")
        
        if file_size > 50 * 1024 * 1024:  # Convert 50MB to bytes
            target_size_bytes = 50 * 1024 * 1024  # 50MB in bytes
            reduce_file_size(file_name, target_size_bytes)

            # Rename the final reduced file to the original name
            
            #context.bot.send_document(chat_id=update.effective_message.chat_id, document=audio_file, caption=caption, filename=file_name,disable_content_type_detection=True, timeout=300)
            #os.remove(video_path)
            #os.remove(audio_path)
        '''file_size = os.path.getsize(f"{file_name}.mp3")
        if file_size > 50 * 1024 * 1024:  # Convert 50MB to bytes
            context.bot.send_message(chat_id=update.message.chat_id, text='The converted audio file is too large to send.')
            os.remove(video_path)
            #os.remove(audio_path)
            return'''
        #video_path = YouTube(yt.watch_url, on_progress_callback = on_progress).streams.filter(only_audio=True).first().download(filename=f'{video_title}.mp3')
        #context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=msg.message_id, text='Sending...')
        ##video_path = os.path.join(ROOT_DIR,f'{video_title}.mp3')
        #audio_path = f'outputs/{video_title}.mp3'
        #video_clip = VideoFileClip(video_path)
        #audio_clip = video_clip.audio
        #audio_clip.write_audiofile(audio_path)
        #audio_clip.close()
        # Check the file size after conversion
        '''artist, music = extract_artist_and_music(file_name)
        print("Artist:", artist)
        print("Music:", music)'''
        # Load the audio file
        '''audio = MP3(f"{file_name}.mp3", ID3=EasyID3)
                
        # Check if the file already has an ID3 tag, if not, add one
        if audio.tags is None:
            audio.add_tags()'''
        
        # Split the string into parts using '-' as the separator
        '''parts = file_name.split('-')
        # Assign each part to a variable
        artist = parts[0]
        music = parts[1]
        #tag = parts[2]'''

        '''audio.tags['title'] = track_name
        # Set the artist name
        #artist = yt.author.split(' - ')[0]
        audio.tags['artist'] = artist_name

        #audio.tags['grouping'] = tag

        # Save the changes
        audio.save()'''
        
        log_handling(update, 'info', 'download thumbnail')
        temp1 = yt.thumbnail_url.partition(".jpg")[0] + ".jpg"
        thumbnail_path = temp1.split('/')[-1]
        thumbnail_path = f"{update.effective_message.chat_id}{thumbnail_path}"
        if not os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'wb') as photo_file:
                photo_file.write(requests.get(yt.thumbnail_url).content)
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=emoji_message.message_id)

        emoji_message = context.bot.send_message(chat_id=update.effective_chat.id, text='📥')
        log_handling(update, 'info', 'send audio file')
        with open(f"{file_name}.mp3", 'rb') as audio_file:
            with open(thumbnail_path, 'rb') as photo_file:
                #print(f"Artist name updated to: {audio.tags['artist'][0]}")
                '''tag.tags['TIT2'] = yt.title
                tag.tags['TPE1'] = mutagen.id3.TPE1(encoding=3, text=yt.author)
                # Save the changes
                tag.save(v1=0, v2_version=3)'''

                if update.effective_message.chat.type =='channel':
                    caption = update.effective_message.sender_chat.link
                    caption = caption.replace("https://t.me/", "@")
                else:
                    caption = ""
                context.bot.send_photo(chat_id=update.effective_message.chat_id, photo=photo_file)
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=emoji_message.message_id)
            with open(thumbnail_path,'rb') as photo_file1:
                    context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=audio_file, thumb=photo_file1, caption=caption, title=track_name, performer=artist_name,timeout = 300)
        '''with open(video_path, 'rb') as audio_file:
            context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=audio_file, thumb=yt.thumbnail_url)'''
        
            #context.bot.delete_message(chat_id=update.message.chat_id, message_id=status.message_id)
        #os.remove(f"{file_name}.mp3")
        os.remove(video_path)  
        os.remove(thumbnail_path)                                                                                     
        #os.remove(audio_path)
    except Exception as e:
        print(e)
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=emoji_message.message_id)
            emoji_message = context.bot.send_message(chat_id=update.effective_chat.id, text='❌')
            context.job_queue.run_once(lambda x: x.bot.delete_message(chat_id=emoji_message.chat_id, message_id=emoji_message.message_id), 15, context=emoji_message)
            if os.path.exists(video_path):
                #os.remove(f"{file_name}.mp3")
                os.remove(video_path)
                os.remove(thumbnail_path)
        except : 
            pass
        

    #else:
        #yt = YouTube(url)
        
        '''results = YoutubeSearch(update.message.text, max_results=5).to_dict()
        if not results:
            context.bot.send_message(chat_id=update.message.chat_id, text='No video found')
            return
        
        # Show the search results with buttons
        reply_text = "Please select a number for the search result:\n"
        keyboard = [
            [InlineKeyboardButton(text=f"{i}. {result['duration']}\n {result['title']}", callback_data=f"select_result_{i}")]
            for i, result in enumerate(results, start=1)
        ] + [[InlineKeyboardButton("Cancel", callback_data="cancel_search")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        #context.bot.reply_text(update.effective_message.chat_id, reply_text=reply_text, reply_markup=reply_markup.to_dict(), parse_mode=ParseMode.HTML)'''

        #update.effective_message.reply_text(reply_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

        # Store the search results in the global dictionary
        #youtube_results[update.message.chat_id] = results
    
    '''def progress(d):

        if d['status'] == 'downloading':
            try:
                update = False

                if last_edited.get(f"{update.message.chat_id}-{msg.message_id}"):
                    if (datetime.datetime.now() - last_edited[f"{update.message.chat_id}-{msg.message_id}"]).total_seconds() >= 5:
                        update = True
                else:
                    update = True

                if update:
                    perc = round(d['downloaded_bytes'] *
                                100 / d['total_bytes'])
                    new_text = f"Downloading {d['info_dict']['title']}\n\n{perc}%"
                    # Check if the new_text is different from the current message text
                    if new_text != msg.text:
                        context.bot.edit_message_text(
                            chat_id=update.message.chat_id, message_id=msg.message_id, text=new_text)
                    last_edited[f"{update.message.chat.id}-{msg.message_id}"] = datetime.datetime.now()
            except Exception as e:
                print(e)

    
    # Define ydl_opts with extractor_args
    ydl_opts = {
        'format': 'm4a/bestaudio',
        'extract-audio': True,
        'outtmpl': f'outputs/{video_title}.%(ext)s',
        'progress_hooks': [progress],
        'postprocessors': [{            # Postprocessor to convert to MP3
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',   # Specify MP3 format
                'preferredquality': '128',  # Specify quality (optional)
        }],
        'cookiefile': '/cookies.txt',
        'verbose': True  # Enable verbose logging
    }'''
    #video_title = ''.join(e for e in video_title if e.isalnum())
    #video_title = video_title[:30]  # Trim the title to a maximum of 30 characters
    
    #with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #info = ydl.extract_info(url, download=True)
    
        #os.remove(audio_path)
   

    #video_title = ''.join(e for e in video_title if e.isalnum())
    #video_title = video_title[:30]  # Trim the title to a maximum of 30 characters
    
    #with YouTube(input_text).streams.filter(only_audio=True).first().download(filename=f'{video_title}.mp3',skip_existing=False):