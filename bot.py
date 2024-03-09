
import os
import telebot
import requests
import asyncio
import threading
import time
from PIL import Image
import pytesseract
import re
from textblob import TextBlob
import pywhatkit as kit
import urllib.request
import string
import numpy as np
import cv2

char = string.ascii_lowercase
file_code_name = {}

width = 50
height = 0
newwidth = 0
arr = string.ascii_letters
arr = arr + string.digits + "+,.-? "
letss = string.ascii_letters


def getimg(case, col):
    global width, height, back
    try:
        url = (
            "https://raw.githubusercontent.com/Ankit404butfound/HomeworkMachine/master/Image/%s.png"
            % case
        )
        imglink = urllib.request.urlopen(url)
    except:
        url = (
            "https://raw.githubusercontent.com/Ankit404butfound/HomeworkMachine/master/Image/%s.PNG"
            % case
        )
        imglink = urllib.request.urlopen(url)
    imgNp = np.array(bytearray(imglink.read()))
    img = cv2.imdecode(imgNp, -1)
    cv2.imwrite(r"%s.png" % case, img)
    img = cv2.imread("%s.png" % case)
    img[np.where((img != [255, 255, 255]).all(axis=2))] = col
    cv2.imwrite("chr.png", img)
    cases = Image.open("chr.png")
    back.paste(cases, (width, height))
    newwidth = cases.width
    width = width + newwidth


def text_to_handwriting(string, rgb=[0, 0, 138], save_to: str = "pywhatkit.png"):
    """Convert the texts passed into handwritten characters"""
    global arr, width, height, back
    try:
        back = Image.open("zback.png")
    except:
        url = "https://raw.githubusercontent.com/Ankit404butfound/HomeworkMachine/master/Image/zback.png"
        imglink = urllib.request.urlopen(url)
        imgNp = np.array(bytearray(imglink.read()))
        img = cv2.imdecode(imgNp, -1)
        cv2.imwrite("zback.png", img)
        back = Image.open("zback.png")
    rgb = [rgb[2], rgb[1], rgb[0]]
    count = -1
    lst = string.split()
    for letter in string:
        if width + 150 >= back.width or ord(letter) == 10:
            height = height + 227
            width = 50
        if letter in arr:
            if letter == " ":
                count += 1
                letter = "zspace"
                wrdlen = len(lst[count + 1])
                if wrdlen * 110 >= back.width - width:
                    width = 50
                    height = height + 227

            elif letter.isupper():
                letter = "c" + letter.lower()
            elif letter == ",":
                letter = "coma"
            elif letter == ".":
                letter = "fs"
            elif letter == "?":
                letter = "que"

            getimg(letter, rgb)

    back.save(f"{save_to}")
    back.close()
    back = Image.open("zback.png")
    width = 50
    height = 0
    return save_to



# Define a function to auto-correct text
def auto_correct_text(text):
    blob = TextBlob(text)
    corrected_text = blob.correct()
    return str(corrected_text)

GPT_API_KEY = ''
GPT_API_ENDPOINT = 'https://api.openai.com/v1/chat/completions'
BOT_TOKEN = ''
bot = telebot.TeleBot(BOT_TOKEN)

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\USER\AppData\Local\Tesseract-OCR\tesseract.exe"

# Function to send a message to GPT-3.5 Turbo and get a response asynchronously
async def send_to_gpt3_async(user_message):
    headers = {
        'Authorization': f'Bearer {GPT_API_KEY}',
        'Content-Type': 'application/json',
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.7
    }
    start_time = time.time()  # Capture the start time
    response = await asyncio.to_thread(requests.post, GPT_API_ENDPOINT, headers=headers, json=data)
    end_time = time.time()  # Capture the end time

    if response.status_code == 200:
        result = response.json()
        assistant_response = result['choices'][0]['message']['content']
        latency = end_time - start_time  # Calculate the latency
        print(f'Latency: {latency:.2f} seconds')
        return assistant_response
    else:
        error_message = response.json().get('error', 'Unknown error')
        return f'Error: GPT-3 API request failed. Details: {error_message}'

# Function to handle user messages
@bot.message_handler(content_types=['text', 'photo'])
def handle_user_message(message):
    if message.text:    
        user_message = message.text
        if "/handwriting" in user_message.lower():
            # Convert text to handwriting
            user_message = user_message.replace("/handwriting", "").strip()
            print(user_message)
            text_to_handwriting(user_message, save_to="myimage.png")
            # kit.text_to_handwriting(user_message, rgb=[0, 0, 250])
            with open('myimage.png', 'rb') as handwriting_image:
                bot.send_photo(message.chat.id, handwriting_image)
        else:
            # If the message is not a handwriting command, send it to GPT-3.5 Turbo
            print(user_message)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def get_gpt3_response():
                return await send_to_gpt3_async(user_message)

            response = loop.run_until_complete(get_gpt3_response())
            bot.reply_to(message, response)

    if message.photo:
        # If the message contains a photo, process it
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}'

        # Download the image from Telegram
        image_response = requests.get(file_url)
        with open('temp_image.jpg', 'wb') as image_file:
            image_file.write(image_response.content)

        # Perform OCR on the downloaded image
        image = Image.open('temp_image.jpg')
        text = pytesseract.image_to_string(image)

        # Remove spaces and line breaks from the recognized text
        text_cleaned = re.sub(r'\s+', ' ', text).strip()
        c=auto_correct_text(text_cleaned)
        if text_cleaned=="":
            bot.reply_to(message,"No TEXT")
        else:
            bot.reply_to(message, "AS it is")
            bot.reply_to(message, text_cleaned)
            bot.reply_to(message, "Autocorrected")
            bot.reply_to(message, c)

# Thread target function to run the bot
def bot_thread():
    bot.polling()

# Main function to start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot_thread = threading.Thread(target=bot_thread)
    bot_thread.start()
    try:
        bot_thread.join()
    except KeyboardInterrupt:
        pass

