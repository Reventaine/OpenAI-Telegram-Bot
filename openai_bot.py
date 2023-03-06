import logging
from config import openaiToken as openaiToken, telegramOpenAI as telegramOpenAI
from chat import *
from image import *
from telegram import Update


from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

IMAGE, CHAT = range(2)

openai.api_key = openaiToken

current_speech_language = 'en_EN'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if current_speech_language == 'ru_RU':
        await update.message.reply_text("/chat для начала беседы или /image для создания изображений при помощи "
                                        "нейросети\n"
                                        f"Выбранный язык Русский, /switch чтобы изменить")
    else:
        await update.message.reply_text("/chat to start a conversation with neuralink or /image to generate images\n"
                                        f"Current language is English, /switch to change")
    return ConversationHandler.END


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if current_speech_language == 'en_EN':
        await update.message.reply_text("/chat to start a conversation with neuralink Chat-GPT3, which can complete "
                                        "text or provide a "
                                        "dialog, works in different languages \n/image to generate images from "
                                        "text. You can ask neuralink via VoiceMessage, /switch to change language."
                                        "\nUpload a photo without any commands to alternate this photo."
                                        "\n The photo must be square with the white area that you want to alter (you "
                                        "can change image via telegram, crop it to a square and paint it"
                                        "in white). Add a caption to specify how you want to alter it."
                                        "\nWithout a caption provided there will be a full alternate image by neuralink"
                                        )
    else:
        await update.message.reply_text("/chat для использования текстовой нейросети Chat-GPT3, которая может "
                                        "завершить текст или предоставить диалог\n/image "
                                        "для создания изображений из текста. Вы можете попросить нейросеть при помощи "
                                        "VoiceMessage, /switch чтобы изменить язык. \nЗагрузить фотографию без "
                                        "каких-либо команд для изменения этой фотографии.\nФотография должна быть "
                                        "квадратной с белой областью, которую вы хотите изменить (вы можете изменить "
                                        "изображение через telegram, обрезать его до квадрата и закрасить в белый "
                                        "цвет). Добавьте надпись, чтобы указать, как вы хотите ее изменить."
                                        "\nБез подписи будет создано полное альтернативное изображение.")
    return ConversationHandler.END


async def switch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_speech_language

    if current_speech_language == 'ru_RU':
        current_speech_language = 'en_EN'
        await update.message.reply_text(f'Current speech language is English')
    else:
        current_speech_language = 'ru_RU'
        await update.message.reply_text(f'Выбранный язык Русский')


if __name__ == '__main__':
    application = Application.builder().token(telegramOpenAI).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("chat", chat_start),
            CommandHandler('image', image),
            CommandHandler('transcribe', transcribe),
            MessageHandler(filters.PHOTO, change_image),
        ],
        states={
            CHAT: [
                MessageHandler(filters.TEXT & (~ filters.COMMAND) & (~ filters.Regex('Image')), chat),
                MessageHandler(filters.VOICE, chat),
            ],
            IMAGE: [
                MessageHandler(filters.Regex("Image"), image),
                MessageHandler(filters.TEXT & (~ filters.COMMAND) & (~ filters.Regex('Image')), get_image)
            ],
            SCRIBE: [
                MessageHandler(filters.VOICE, scribe),
            ]
        },
        fallbacks=[CommandHandler("text", chat_start), CommandHandler("image", image), CommandHandler('start', start)]
        , allow_reentry=True,
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('switch', switch))
    application.add_handler(conv_handler)
    application.run_polling()
