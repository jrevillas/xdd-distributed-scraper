from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "xdd-distributed-scraper 0.1"

if __name__ == "__main__":
    app.run()
