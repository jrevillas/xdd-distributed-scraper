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

FLAGS = ["english", "japanese", "spanish"]

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
        db.incr("processed_seasons")
    db.incr("processed_tv_shows")
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

def determine_metadata(link_div):
    metadata = {"audio": None, "subtitles": None}
    for flag_div in link_div.find_all("div", {"class": "flag"}):
        metadata["subtitles"] = determine_subtitles(flag_div)
        if metadata["subtitles"] is None:
            metadata["audio"] = determine_audio(flag_div)
    return metadata

def determine_audio(flag_div):
    if "LAT" in flag_div.get_text():
        return "latin"
    language = flag_div.get("class")[-1]
    if language in FLAGS:
        return language
    return "unknown"

def determine_subtitles(flag_div):
    if "SUB" in flag_div.get_text():
        language = flag_div.get("class")[-1]
        if language in FLAGS:
            return language
        return "unknown"

def resolve_internal_link(internal_link):
    try:
        req = get_session().get(XDD_ROOT + internal_link, headers=HEADERS)
    except requests.exceptions.RequestException:
        resolve_internal_link(internal_link)
    html = BeautifulSoup(req.text, "lxml")
    for link in html.find_all("a", {"class": "episodeText"}, href=True):
        return extract_redirection(link["href"])

def extract_redirection(link):
    try:
        req = get_session().get(XDD_ROOT + link, allow_redirects=False, headers=HEADERS)
    except requests.exceptions.RequestException:
        extract_redirection(link)
    external_url = req.headers.get("Location")
    if external_url is not None:
        db.incr("processed_links")
        return external_url

def process_chapter(chapter_link, chapter_db):
    try:
        req = get_session().get(XDD_ROOT + chapter_link, headers=HEADERS)
    except requests.exceptions.RequestException:
        process_chapter(chapter_link, chapter_db)
    html = BeautifulSoup(req.text, "lxml")
    for link in html.find_all("a", {"class": "a aporteLink done"}, href=True):
        external_url = resolve_internal_link(link["href"])
        if external_url is not None:
            mirror = determine_metadata(link)
            mirror["external_url"] = external_url
            chapter_db["mirrors"].append(mirror)
    storage.update_episode(chapter_db)
    db.incr("processed_chapters")

def find_seasons(tv_show):
    try:
        req = get_session().get(XDD_TV_SHOW_ENDPOINT + tv_show, headers=HEADERS)
    except requests.exceptions.RequestException:
        find_seasons(tv_show)
    html = BeautifulSoup(req.text, "lxml")
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
    try:
        session.post(XDD_LOGIN_ENDPOINT, data=data, headers=HEADERS)
    except requests.exceptions.RequestException:
        login(username, password)
    print("xdd_login(...) OK")
    return session
