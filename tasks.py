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

@task_queue.task
def scrap_tv_show(username, password, tv_show):
    session = login(username, password)
    for season_html in find_seasons(session, tv_show):
        for a in season_html.find_all("button", {"class": "big defaultPopup"}, href=True):
            print("scrap_tv_show(...) " + a["href"])
            process_chapter(session, a["href"])
    db.set("is_server_busy", "0")

def resolve_internal_link(session, internal_link):
    headers = {"Referer": XDD_ROOT}
    request = session.get(XDD_ROOT + internal_link, headers=headers)
    html = BeautifulSoup(request.text, "lxml")
    for link in html.find_all("a", {"class": "episodeText"}, href=True):
        redirection = session.get(XDD_ROOT + link["href"], headers=headers, allow_redirects=False)
        print("resolve_internal_link(...) " + redirection.headers["Location"])

def process_chapter(session, chapter_link):
    headers = {"Referer": XDD_ROOT}
    request = session.get(XDD_ROOT + chapter_link, headers=headers)
    html = BeautifulSoup(request.text, "lxml")
    for link in html.find_all("a", {"class": "a aporteLink done"}, href=True):
        resolve_internal_link(session, link["href"])

def find_seasons(session, tv_show):
    headers = {"Referer": XDD_ROOT}
    request = session.get(XDD_TV_SHOW_ENDPOINT + tv_show, headers=headers)
    html = BeautifulSoup(request.text, "lxml")
    return html.find_all("div", {"id": re.compile("^episodes-")})

def login(username, password):
    session = requests.Session()
    headers = {"Referer": XDD_ROOT}
    data = {
        "LoginForm[username]": username,
        "LoginForm[password]": password}
    session.post(XDD_LOGIN_ENDPOINT, headers=headers, data=data)
    print("xdd_login(...) OK")
    return session
