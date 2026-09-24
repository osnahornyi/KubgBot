import telebot
import requests
import google.generativeai as genai

from telebot import types
from bs4 import BeautifulSoup as bs
from datetime import date

bot = telebot.TeleBot('7263625894:AAEa6GyVXX996GUV9u9AU0eQf23PepYITRI')
genai.configure(api_key="AIzaSyDTXDiCMNZu_q7bKuVsLgZGVIbpvIMkrIw")


def get_schedule(date_):
    session = requests.Session()

    log_page_html = session.get("https://elearning.kubg.edu.ua/login/index.php")
    log_page_soup = bs(log_page_html.content, "lxml")
    login_token = log_page_soup.find("input", {"name": "logintoken"})["value"]

    payload1 = {
        "anchor": "",
        "logintoken": login_token,
        "username": "osnahornyi.fitm22",
        "password": "FPrXiQ6K",
    }

    answer_page_html = session.post("https://elearning.kubg.edu.ua/login/index.php", data=payload1)
    answer_page_soup = bs(answer_page_html.content, "lxml")

    payload2 = {
        "id": "30129"
    }

    schedule_date_list = []

    schedule_page_html = session.post("https://elearning.kubg.edu.ua/local/gdo/student/schedule.php", data=payload2)
    schedule_page_soup = bs(schedule_page_html.content, "lxml")

    schedule_row = ""
    for i in schedule_page_soup.find("div", class_="table-responsive"):
        schedule_row = schedule_row + str(i.text)

    schedule_array = schedule_row.split("""

""")

    schedule = ""
    delimiter = "\n"
    checker = False
    for element in schedule_array:
        if checker == True:
            try:
                schedule += f"""\n{element.split(delimiter)[1]} пара\n📖 {element.split(delimiter)[2]}\n👨‍🏫 {element.split(delimiter)[3]}\n👫 {element.split(delimiter)[4]}\nДодаток: {element.split(delimiter)[5]}\n"""
            except IndexError:
                pass

        if len(element.split(",")[0].split(".")) == 3 and checker == False\
                and int(element.split(",")[0].split(".")[0]) == int(date_.split('.')[0])\
                and int(element.split(",")[0].split(".")[1]) == int(date_.split('.')[1])\
                and int(element.split(",")[0].split(".")[2]) == int(date_.split('.')[2]):
            checker = True
            schedule += f"📅 {date_.split('.')[0]}.{date_.split('.')[1]}.{date_.split('.')[2]}" + "\n"
        elif len(element.split(",")[0].split(".")) == 3 and checker == True:
            checker = False

    return schedule


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
