import os
import telebot
import requests
import google.generativeai as genai

from telebot import types
from bs4 import BeautifulSoup as bs
from datetime import date

bot = telebot.TeleBot(os.environ["BOT_TOKEN"])
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

LOGIN_URL = "https://elearning.kubg.edu.ua/login/index.php"
SCHEDULE_URL = "https://elearning.kubg.edu.ua/local/gdo/student/schedule.php"
GROUP_ID = "30129"


def login(session):
    page = bs(session.get(LOGIN_URL).content, "lxml")
    token = page.find("input", {"name": "logintoken"})["value"]
    session.post(LOGIN_URL, data={
        "anchor": "",
        "logintoken": token,
        "username": os.environ["ELEARNING_USER"],
        "password": os.environ["ELEARNING_PASSWORD"],
    })


def fetch_schedule_text(session):
    response = session.post(SCHEDULE_URL, data={"id": GROUP_ID})
    table = bs(response.content, "lxml").find("div", class_="table-responsive")
    return "".join(str(row.text) for row in table)


def parse_dmy(text):
    parts = text.split(".")
    if len(parts) != 3:
        return None
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def format_lesson(block):
    lines = block.split("\n")
    if len(lines) < 6:
        return ""
    return (f"\n{lines[1]} пара\n📖 {lines[2]}\n👨‍🏫 {lines[3]}\n"
            f"👫 {lines[4]}\nДодаток: {lines[5]}\n")


def parse_day(text, date_):
    target = parse_dmy(date_)
    if target is None:
        return ""
    schedule = ""
    collecting = False
    for block in text.split("\n\n"):
        block_date = parse_dmy(block.split(",")[0])
        if collecting and block_date is None:
            schedule += format_lesson(block)
        elif collecting:
            collecting = False
        elif block_date == target:
            collecting = True
            schedule += f"📅 {date_}\n"
    return schedule


def get_schedule(date_):
    session = requests.Session()
    login(session)
    return parse_day(fetch_schedule_text(session), date_)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📆 Отримати розклад занять")
    btn2 = types.KeyboardButton("💰 Вартість навчання")
    btn3 = types.KeyboardButton("📂 Подача документів")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Вітаю, чим я можу вам допомогти?", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "📆 Отримати розклад занять":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("📆 Сьогоднішня дата", callback_data="today")
        markup.add(btn1)
        bot.send_message(message.chat.id, "Напишіть будь ласка дату, розклад якої ви хочете отримати(у форматі 01.01.2025)", reply_markup=markup)
    elif message.text == "💰 Вартість навчання":
        bot.send_message(message.chat.id, "Зачекайте Gemini обробляє ваш запит...")
        model = genai.GenerativeModel('gemini-2.5-pro')

        response = model.generate_content("Яка вартість навчання на Факультеті інформаційних технологій та математики КУБГ (імені Бориса Грінченка) у 2025 році?")
        bot.send_message(message.chat.id, response.text)
    elif message.text == "📂 Подача документів":
        bot.send_message(message.chat.id, "Зачекайте Gemini обробляє ваш запит...")
        model = genai.GenerativeModel('gemini-2.5-pro')

        response = model.generate_content("Розпиши коротко як подати документи до Факультету інформаційних технологій та математики КУБГ (імені Бориса Грінченка) у 2025 році?")
        bot.send_message(message.chat.id, response.text)
    else:
        if len(message.text.split(".")) == 3:
            bot.send_message(message.chat.id, get_schedule(message.text))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == "today":
                today = date.today()
                formatted = today.strftime("%d.%m.%Y")

                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text=call.message.text + "\n\n📆 Сьогоднішня дата")
                bot.send_message(call.message.chat.id, get_schedule(formatted))
    except Exception as e:
        print(repr(e))

bot.polling()
