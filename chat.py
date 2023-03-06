import openai
import subprocess
from telegram import Update

from telegram.ext import ContextTypes


IMAGE, CHAT, SCRIBE = range(3)


async def chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    messages[update.effective_user.name] = [{"role": "system",
                                            "content": "You witty and knowledgeable assistant. You always glad to "
                                                       "tell jokes."}]
    await update.message.reply_text("Starting conversation!")
    return CHAT


async def speech_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    speech = await context.bot.get_file(update.message.voice.file_id)
    await speech.download('speech.mp3')

    subprocess.call(['ffmpeg', '-i', 'speech.mp3',
                     'speech.wav', '-y'])

    audio_file = open("speech.wav", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    return transcript['text']


messages = {}


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.name not in messages.keys():
        await chat_start(update, context)

    if update.message.text is not None:
        prompt = update.message.text
    else:
        prompt = await speech_to_text(update, context)

    messages[update.effective_user.name].append({"role": "user", "content": f'username {update.effective_user.name}'
                                                                            f' message {prompt}'})

    try:
        msg = await update.message.reply_text(f"Answering...")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages[update.effective_user.name],
            temperature=0.8,
            max_tokens=600,
            frequency_penalty=0.0,
            presence_penalty=0.2,
        )

        answer = response['choices'][0]['message']['content']
        await msg.edit_text(text=answer)
        messages[update.effective_user.name].append({"role": "assistant", "content": answer})
        print(response["usage"])
        print(len(messages[update.effective_user.name]))

        if response["usage"]["total_tokens"] > 3400:
            del messages[update.effective_user.name][:5]
        return CHAT

    except:
        await update.message.reply_text(text="Please try again")
        return CHAT


async def transcribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Redirect or record voice to transcribe')
    return SCRIBE


async def scribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    speech = await context.bot.get_file(update.message.voice.file_id)
    await speech.download('speech.mp3')

    subprocess.call(['ffmpeg', '-i', 'speech.mp3',
                     'speech.wav', '-y'])

    audio_file = open("speech.wav", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    await update.message.reply_text(transcript['text'])
    return transcribe(update, context)
