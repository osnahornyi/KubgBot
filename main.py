import os

import requests
from bs4 import BeautifulSoup as bs

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


bot.polling()
