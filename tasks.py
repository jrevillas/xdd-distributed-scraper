import os
import re
import time

from bs4 import BeautifulSoup
from celery import Celery
import redis
import requests

db = redis.StrictRedis(decode_responses=True)
task_queue = Celery("tasks", broker=os.environ["CELERY_BROKER"])

XDD_ROOT = "http://www.pordede.com"
XDD_LOGIN_ENDPOINT = XDD_ROOT + "/site/login"
XDD_TV_SHOW_ENDPOINT = XDD_ROOT + "/serie/"

HEADERS = {"Referer": XDD_ROOT}

@task_queue.task
def scrap_tv_show(username, password, tv_show):
    session = login(username, password)
    current_season = 1
    current_chapter = 1
    for season_html in find_seasons(session, tv_show):
        for a in season_html.find_all("button", {"class": "big defaultPopup"}, href=True):
            print("scrap_tv_show(...) " + tv_show + "-" + str(current_season) + "-" + str(current_chapter))
            process_chapter(session, a["href"])
            save_status(tv_show, current_season, current_chapter)
            current_chapter += 1
        current_season += 1
        current_chapter = 1
    db.set("is_server_busy", "0")

'''
Actualiza el estado de la serie con la referencia al ultimo capitulo que se ha
procesado. Habilita la posibilidad de reanudar procesos en sucesivas ejecuciones
desde AWS Lambda.
'''
def save_status(tv_show, current_season, current_chapter):
    db.set("status_" + tv_show, str(current_season) + "-" + str(current_chapter))

def resolve_internal_link(session, internal_link):
    request = session.get(XDD_ROOT + internal_link, headers=HEADERS)
    html = BeautifulSoup(request.text, "lxml")
    for link in html.find_all("a", {"class": "episodeText"}, href=True):
        redirection = session.get(XDD_ROOT + link["href"], headers=HEADERS, allow_redirects=False)
        print("resolve_internal_link(...) " + redirection.headers["Location"])

def process_chapter(session, chapter_link):
    request = session.get(XDD_ROOT + chapter_link, headers=HEADERS)
    html = BeautifulSoup(request.text, "lxml")
    for link in html.find_all("a", {"class": "a aporteLink done"}, href=True):
        resolve_internal_link(session, link["href"])

def find_seasons(session, tv_show):
    request = session.get(XDD_TV_SHOW_ENDPOINT + tv_show, headers=HEADERS)
    html = BeautifulSoup(request.text, "lxml")
    return html.find_all("div", {"id": re.compile("^episodes-")})

def login(username, password):
    session = requests.Session()
    data = {
        "LoginForm[username]": username,
        "LoginForm[password]": password}
    session.post(XDD_LOGIN_ENDPOINT, headers=HEADERS, data=data)
    print("xdd_login(...) OK")
    return session
