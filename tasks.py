import os
from random import choice
import re

from bs4 import BeautifulSoup
import redis
import requests

import storage

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

XDD_ROOT = "http://www.pordede.com"
XDD_LOGIN_ENDPOINT = XDD_ROOT + "/site/login"
XDD_TV_SHOW_ENDPOINT = XDD_ROOT + "/serie/"

HEADERS = {"Referer": XDD_ROOT}

sessions = [
    {"username": "pdd-qbg768g", "password": "qbg768g"},
    {"username": "pdd-n6q2kps", "password": "n6q2kps"},
    {"username": "pdd-dg1z8et", "password": "dg1z8et"}]

db = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

def scrap_tv_show(tv_show):
    login_all()
    storage.get_tv_show(tv_show)
    current_season = 1
    current_chapter = 1
    for season_html in find_seasons(tv_show):
        print("scrap_tv_show(...) " + tv_show + "-" + str(current_season))
        for a in season_html.find_all("button", {"class": "big defaultPopup"}, href=True):
            print("scrap_tv_show(...) " + tv_show + "-" + str(current_season) + "-" + str(current_chapter))
            chapter_db = storage.get_episode(tv_show, current_season, current_chapter)
            process_chapter(a["href"], chapter_db)
            save_status(tv_show, current_season, current_chapter)
            current_chapter += 1
        current_season += 1
        current_chapter = 1
    db.set("is_server_busy", "0")

def get_session():
    return choice(sessions)

'''
Actualiza el estado de la serie con una referencia al ultimo capitulo que se ha
procesado. Habilita la posibilidad de reanudar procesos en sucesivas ejecuciones
desde AWS Lambda.
'''
def save_status(tv_show, current_season, current_chapter):
    db.set("status_" + tv_show, str(current_season) + "-" + str(current_chapter))

def resolve_internal_link(internal_link):
    request = get_session().get(XDD_ROOT + internal_link, headers=HEADERS)
    html = BeautifulSoup(request.text, "lxml")
    for link in html.find_all("a", {"class": "episodeText"}, href=True):
        redirection = get_session().get(XDD_ROOT + link["href"], headers=HEADERS, allow_redirects=False)
        external_url = redirection.headers.get("Location")
        if external_url:
            print("resolve_internal_link(...) " + external_url)
            return external_url

def process_chapter(chapter_link, chapter_db):
    request = get_session().get(XDD_ROOT + chapter_link, headers=HEADERS)
    html = BeautifulSoup(request.text, "lxml")
    for link in html.find_all("a", {"class": "a aporteLink done"}, href=True):
        external_url = resolve_internal_link(link["href"])
        if external_url is not None:
            chapter_db["mirrors"].append(external_url)
    storage.update_episode(chapter_db)

def find_seasons(tv_show):
    request = get_session().get(XDD_TV_SHOW_ENDPOINT + tv_show, headers=HEADERS)
    html = BeautifulSoup(request.text, "lxml")
    return html.find_all("div", {"id": re.compile("^episodes-")})

def login_all():
    for idx, item in enumerate(sessions):
        if not isinstance(item, requests.sessions.Session):
            sessions[idx] = login(item["username"], item["password"])

def login(username, password):
    session = requests.Session()
    data = {
        "LoginForm[username]": username,
        "LoginForm[password]": password}
    session.post(XDD_LOGIN_ENDPOINT, headers=HEADERS, data=data)
    print("xdd_login(...) OK")
    return session
