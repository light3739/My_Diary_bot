import os
import requests
from bs4 import BeautifulSoup
import time
import telebot
import datetime
import calendar
import mysql.connector
from telebot import types

BOT_TOKEN = '5873352611:AAG1jcPiabZdUSLUStLBNROhjWr98NkNONo'
bot = telebot.TeleBot(BOT_TOKEN)
conn = mysql.connector.connect(
    host="localhost",
    user="yourusername",
    password="Pilostlight1$",
    database="mydatabase"
)
cursor = conn.cursor()
cursor.execute('''create table if not exists notes (date date, chat_id int, text text, smiley text)''')


@bot.message_handler(commands=['add'])
def add(message):
    # Check if a note for today already exists
    today = datetime.date.today()
    cursor.execute("SELECT * FROM notes WHERE date = %s AND chat_id = %s", (today, message.chat.id))
    note = cursor.fetchone()
    if note:
        bot.send_message(chat_id=message.chat.id, text='Заметка на сегодня уже существует')
    else:
        bot.send_message(chat_id=message.chat.id, text='Введите текст:')
        bot.register_next_step_handler(message, lambda m: ask_for_smiley(m))


def ask_for_smiley(message):
    text = message.text
    chat_id = message.chat.id
    keyboard = types.ReplyKeyboardMarkup(row_width=3)
    emoji3 = types.KeyboardButton(text='😊')
    emoji1 = types.KeyboardButton(text='😢')
    emoji2 = types.KeyboardButton(text='🙂')
    keyboard.add(emoji1, emoji2, emoji3)
    bot.send_message(chat_id, 'Выберите смайлик:', reply_markup=keyboard)
    bot.register_next_step_handler(message, lambda m: add_note_with_smiley(m, text, chat_id, m.text))


def add_note_with_smiley(message, text, chat_id, smiley):
    date = datetime.date.today()
    cursor.execute("INSERT INTO notes (date, chat_id, text, smiley) VALUES (%s, %s, %s, %s)",
                   (date, chat_id, text, smiley))
    conn.commit()
    bot.send_message(chat_id, 'Заметка добавлена', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['show'])
def show(message):
    bot.send_message(chat_id=message.chat.id, text='Введите дату:')
    bot.register_next_step_handler(message, show_func)


def show_func(message):
    date = message.text
    cursor.execute("SELECT text FROM notes WHERE date = %s AND chat_id = %s", (date, message.chat.id))
    note = cursor.fetchone()
    if note:
        bot.send_message(message.chat.id, note)
    else:
        bot.send_message(message.chat.id,
                         'Заметки на эту дату не найдены')


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    response = requests.get('https://api.quotable.io/random')
    if response.status_code == 200:
        data = response.json()
        quote = data['content']
        author = data['author']
        bot.reply_to(message, f"{quote}\n- {author}")
    else:
        bot.reply_to(message, "Sorry, I couldn't get a quote at the moment.")


while True:
    try:
        bot.polling()
    except Exception as e:
        if "429" in str(e):
            time.sleep(60)
