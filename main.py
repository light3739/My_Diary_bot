import os
import requests
from bs4 import BeautifulSoup
import time
import telebot
import datetime
import calendar
import mysql.connector
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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


def get_notes(month):
    query = "SELECT DATE_FORMAT(date, '%Y-%m-%d') FROM notes WHERE MONTH(date) = %s"
    year = 2023
    start_date = f"{year}-{month:02}-01"
    end_date = f"{year}-{month:02}-{calendar.monthrange(year, month)[1]}"
    cursor.execute(query, (month,))
    notes = {str(date) for date in cursor.fetchall() if date}
    return notes


def show_func(message):
    date = message.text
    cursor.execute("SELECT text FROM notes WHERE date = %s AND chat_id = %s", (date, message.chat.id))
    note = cursor.fetchone()
    if note:
        bot.send_message(message.chat.id, note)
    else:
        bot.send_message(message.chat.id,
                         'Заметки на эту дату не найдены')


@bot.message_handler(commands=['calendar'])
def calendar_callback(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, text="Choose a date:")
    year = 2023
    month = datetime.datetime.now().month
    notes = get_notes(month)
    keyboard = []
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                day_str = str(day)
                date = datetime.date(year, month, day)
                if str(date) in str(notes):
                    cursor.execute("SELECT smiley FROM notes WHERE date = %s AND chat_id = %s", (date, message.chat.id))
                    smail = cursor.fetchone()
                    day_str += str(smail)[2]  # костыль ебаный
                row.append(InlineKeyboardButton(day_str, callback_data=day_str))
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text="Calendar", reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    if call.data == "ignore":
        bot.answer_callback_query(call.id)
    else:
        bot.edit_message_text(text="Вы выбрали дату: {}".format(call.data),
                              chat_id=chat_id,
                              message_id=message_id)


@bot.message_handler(commands=['test'])
def test_callback(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, str(get_notes(3)))
    if str(datetime.date(2023, 3, 27)) in str(get_notes(3)):
        bot.send_message(chat_id, text="jaaaaa")


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
