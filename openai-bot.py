import openai
import subprocess
from PIL import Image
import logging
import time
from config import openaiToken as openaiToken, telegramOpenAI as telegramOpenAI
from telegram import Update
# import speech_recognition as sr

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
        await update.message.reply_text("/text для ввода текста или /image для создания изображений при помощи "
                                        "нейросети\n"
                                        f"Выбранный язык Русский, /switch чтобы изменить")
    else:
        await update.message.reply_text("/text to use text neuralink or /image to generate images\n"
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


async def speech_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    speech = await context.bot.get_file(update.message.voice.file_id)
    await speech.download('speech.mp3')
    subprocess.call(['ffmpeg', '-i', 'speech.mp3',
                     'speech.wav', '-y'])

    audio_file = open("speech.wav", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    """r = sr.Recognizer()
    with sr.AudioFile('speech.wav') as source:
        audio_data = r.record(source)
        prompt = r.recognize_google(audio_data, language=current_speech_language)"""

    return transcript['text']


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Starting conversation!")
    return CHAT


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return CHAT


messages = [{"role": "system", "content": "You witty and knowledgeable assistant fluent in Russian,"
                                          "English. You sharing scientific information and glad to crack a joke."}]


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text is not None:
        prompt = update.message.text
    else:
        prompt = await speech_to_text(update, context)

    messages.append({"role": "user", "content": f'username {update.effective_user.name}'
                                                f' message {prompt}'})

    try:
        msg = await update.message.reply_text(f"Building an answer...")
        msg

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=1.2,
            max_tokens=600,
            frequency_penalty=0.0,
            presence_penalty=0.8,
        )

        answer = response['choices'][0]['message']['content']
        await msg.edit_text(text=answer)
        messages.append({"role": "assistant", "content": answer})
        print(answer)
        print(response["usage"])

        if response["usage"]["prompt_tokens"] > 1950:
            await update.message.reply_text("Sorry but I run out of memory! Reloading...")
            return await text(update, context)
        return await message(update, context)

    except:
        await update.message.reply_text(text="Error, please try again")
        return await text(update, context)


async def image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Enter a request for an image or /text")
    return IMAGE


async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = update.message.text

    await update.message.reply_text(f"Building images...")

    response = openai.Image.create(
        prompt=prompt,
        n=5,
        size="1024x1024"
    )

    for i in range(5):
        await update.message.reply_photo(photo=response['data'][i]['url'])
        time.sleep(1)
    return await start(update, context)


def convert_image():
    img = Image.open("file.jpg")
    img = img.convert("RGBA")

    datas = img.getdata()

    newData = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.resize((1024, 1024), Image.Resampling.LANCZOS).convert('RGBA').save("file.png", format="png")


async def change_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = update.message.caption

    await update.message.reply_text(f"Alternating images...")
    file = await context.bot.get_file(update.message.photo[-1]['file_id'])
    await file.download('file.jpg')

    convert_image()

    try:
        response = openai.Image.create_edit(
            image=open('file.png', "rb"),
            prompt=prompt,
            n=3,
            size="1024x1024"
        )

        for i in range(3):
            await update.message.reply_photo(photo=response['data'][i]['url'])
    except:
        # image variation as a bonus:
        response = openai.Image.create_variation(
            image=open("file.png", "rb"),
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']

        await update.message.reply_photo(photo=image_url, caption='Bonus')

    time.sleep(1)
    return await start(update, context)


if __name__ == '__main__':
    application = Application.builder().token("TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("chat", text),
            CommandHandler('image', image),
            MessageHandler(filters.PHOTO, change_image),
            MessageHandler(filters.VOICE, chat),
        ],
        states={
            CHAT: [
                MessageHandler(filters.TEXT & (~ filters.COMMAND) & (~ filters.Regex('Image')), chat)
            ],
            IMAGE: [
                MessageHandler(filters.Regex("Image"), image),
                MessageHandler(filters.TEXT & (~ filters.COMMAND) & (~ filters.Regex('Image')), get_image)
            ],
        },
        fallbacks=[CommandHandler("text", text), CommandHandler("image", image)], allow_reentry=True,
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('switch', switch))
    application.add_handler(conv_handler)
    application.run_polling()
