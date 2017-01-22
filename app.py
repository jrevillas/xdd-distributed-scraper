import os

from flask import Flask, jsonify, request

XDD_USERNAME = os.environ.get("XDD_USERNAME")
if XDD_USERNAME == None:
    print("XDD_USERNAME is not set, exiting...")
    quit()

XDD_PASSWORD = os.environ.get("XDD_PASSWORD")
if XDD_PASSWORD == None:
    print("XDD_PASSWORD is not set, exiting...")
    quit()

processed_chapters = 0
processed_links = 0
processed_seasons = 0
processed_tv_shows = 0
server_is_busy = False
server_logs = []

app = Flask(__name__)

# Muestra el nombre de la aplicacion y su version.
@app.route("/")
def index_handler():
    return jsonify(
        application="xdd-distributed-scraper",
        version="0.1")

# Recibe la informacion necesaria sobre una serie para poder extraer las
# temporadas, capitulos y enlaces de los mismos. Cuando recibe una peticion
# valida cambia el estado del servicio a ocupado para evitar que se dispare el
# numero de conexiones salientes. Vuelve a cambiar el estado del servicio a
# disponible cuando termina de procesar la peticion.
@app.route("/job", methods=['POST'])
def job_handler():
    if server_is_busy:
        return jsonify(status="busy")
    global server_is_busy
    server_is_busy = True
    return jsonify(request.get_json())

# Muestra el numero de series, temporadas, capitulos y enlaces que se han
# procesado desde el arranque de la aplicacion.
@app.route("/stats")
def stats_handler():
    return jsonify(
        processed_chapters=processed_chapters,
        processed_links=processed_links,
        processed_seasons=processed_seasons,
        processed_tv_shows=processed_tv_shows)

if __name__ == "__main__":
    app.run()
