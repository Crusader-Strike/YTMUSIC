import logging
import os
from telegram import Update
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

logger = logging.getLogger(__name__)

# TODO: use LoggerAdapter instead
def log_handling(update: Update, level: str, message: str) -> None:
    """Log message with chat_id and message_id."""
    _level = getattr(logging, level.upper())
    if update.effective_chat != None :
        if update.effective_chat.type == 'private':
            logger.log(_level, f'[{update.effective_chat.id}:{update.effective_message.message_id}] {message} - from {update.effective_user.id} : {update.effective_user.full_name}')
        else:
            logger.log(_level, f'[{update.effective_chat.id}:{update.effective_message.message_id}] {message}')
    else:
        logger.log(_level, f'[{update.effective_user.id}] {message}')