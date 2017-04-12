import os
from threading import Thread

from flask import Flask, jsonify, request
import redis

from tasks import scrap_tv_show

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

db = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
db.set("is_server_busy", 0)
db.set("processed_chapters", 0)
db.set("processed_links", 0)
db.set("processed_seasons", 0)
db.set("processed_tv_shows", 0)

app = Flask(__name__)

@app.route("/tv-show/<tv_show>/s<season>e<episode>")
def episode_handler(tv_show, season, episode):
    return jsonify(
        episode=episode,
        season=season,
        tv_show=tv_show)

@app.route("/")
def index_handler():
    return jsonify(
        application="xdd-distributed-scraper",
        version="3.0")

'''
Recibe la informacion necesaria sobre una serie para poder extraer las
temporadas, capitulos y enlaces de los mismos. Cuando recibe una peticion valida
cambia el estado del servicio a ocupado para evitar que se dispare el numero de
conexiones salientes.
'''
@app.route("/job", methods=['POST'])
def job_handler():
    if db.get("is_server_busy") == "1":
        return jsonify(status="busy"), 503
    payload = request.get_json()
    if not "tv_show" in payload:
        return jsonify(error="'tv_show' key is missing"), 400
    if not "xdd_session" in payload:
        return jsonify(error="'xdd_session' key is missing"), 400
    db.set("is_server_busy", 1)
    t = Thread(
        args=[payload["tv_show"], payload["xdd_session"]],
        daemon=True,
        target=scrap_tv_show)
    t.start()
    return jsonify(
        status="submitted",
        tv_show=payload["tv_show"],
        xdd_session=payload["xdd_session"])

@app.route("/mirror/<mirror>")
def mirror_handler(mirror):
    return jsonify(mirror=mirror)

@app.route("/tv-show/<tv_show>/s<season>")
def season_handler(tv_show, season):
    return jsonify(
        season=season,
        tv_show=tv_show)

'''
Muestra el numero de series, temporadas, capitulos y enlaces que se han
procesado desde el arranque de la aplicacion.
'''
@app.route("/stats")
def stats_handler():
    return jsonify(
        processed_chapters=int(db.get("processed_chapters")),
        processed_links=int(db.get("processed_links")),
        processed_seasons=int(db.get("processed_seasons")),
        processed_tv_shows=int(db.get("processed_tv_shows")))

@app.route("/tv-show/<tv_show>")
def tv_show_handler(tv_show):
    return jsonify(tv_show=tv_show)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port)
