import time
import openai
from openai_bot import start
from PIL import Image
from telegram import Update

from telegram.ext import ContextTypes


IMAGE, CHAT = range(2)


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