import os
import logging
import warnings
import io
import run_model

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv('TG_BOT_TOKEN', None)
BOT_EXCLUSIVE_USERNAMES = os.getenv('TG_BOT_EXCLUSIVE_USERNAMES', None)

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# TODO: Find a prettier solution. This works very nice though...
global model_pipeline
model_pipeline = None

async def voicenote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  chat_id =update.effective_chat.id
  message = update.message
  logger.info("[chat_id={}] Message from name={}".format(chat_id, update.effective_chat.effective_name))
  
  file = None
  file_io = io.BytesIO()

  # Extends timeout to cope with .de internetz
  file_kwargs = {
    'read_timeout': 300,
    'write_timeout': 300,
    'connect_timeout': 300,
    'pool_timeout': 300,
  }

  attachment = message.effective_attachment
  logger.info("[chat_id={}] Get file from {}".format(chat_id, type(attachment)))
  file = await message.effective_attachment.get_file(**file_kwargs)

  logger.info("[chat_id={}] Downloading audio".format(chat_id))
  message = await message.reply_text('Downloading the Audio/Voice...', quote=True)
  await file.download_to_memory(file_io)
  file_io.seek(0)

  await message.edit_text('Loading the Model...')

  global model_pipeline
  if model_pipeline is None:
    logger.info("[chat_id={}] Waking up the model".format(chat_id))
    with warnings.catch_warnings(record=True):
      model_pipeline = run_model.load_model()

  logger.info("[chat_id={}] Processing".format(chat_id))
  await message.edit_text('Processing the audio/voice...')

  result = model_pipeline(file_io.read())

  logger.info("[chat_id={}] Formatting".format(chat_id))
  await message.edit_text('Formatting...')

  response = run_model.format_chunks_text(result['chunks'])

  logger.info("[chat_id={}] Response sent: {}".format(chat_id, result))
  await message.edit_text(response)

def main() -> None:
  application = Application.builder().token(BOT_TOKEN).build()
  msg_filter = filters.VOICE | filters.AUDIO

  if BOT_EXCLUSIVE_USERNAMES:
    usernames = tuple(map(lambda x: x.strip(), BOT_EXCLUSIVE_USERNAMES.split(',')))
    logger.info("Started with restricted audience: usernames={}".format(usernames))
    only_my_user_list = filters.Chat()
    only_my_user_list.add_usernames(usernames)
    msg_filter = only_my_user_list & msg_filter
    
  application.add_handler(MessageHandler(msg_filter, voicenote))

  application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
  main()
