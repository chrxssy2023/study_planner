from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/styles")
def styles():
    return render_template("styles.shtml")


@app.route("/webpages")
def webpages():
    return render_template("webpages.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)