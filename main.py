from flask import Flask, render_template
import sqlite3
from sqlite3 import Error

app = Flask(__name__)
DATABASE = "study_planner.db"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route("/")
def index():
    return render_template("index.html")








@app.route('/tags/<tag_type>')
def render_webpage(tag_type):
    title = tag_type.upper()
    query = "SELECT tag, description FROM html_tags WHERE type=?"
    con = create_connection(DATABASE)
    print(con)
    cur = con.cursor()

    cur.execute(query, (title, ))
    tag_list = cur.fetchall()
    con.close()
    print(tag_list)
    return render_template("webtags.html", tags=tag_list, title=title)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
    