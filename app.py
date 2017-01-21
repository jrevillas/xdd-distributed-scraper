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

server_is_busy = False
server_logs = []

processed_tv_shows = 0
processed_seasons = 0
processed_chapters = 0
processed_links = 0

app = Flask(__name__)

@app.route("/")
def index_handler():
    return jsonify(application="xdd-distributed-scraper", version="0.1")

@app.route("/job", methods=['POST'])
def job_handler():
    if server_is_busy:
        return jsonify(status="busy")
    global server_is_busy
    server_is_busy = True
    return jsonify(request.get_json())

if __name__ == "__main__":
    app.run()
