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


@app.route("/webpages")
def render_webpages():

    query = "SELECT assignment_name, due_date FROM assignments"

    con = create_connection(DATABASE)
    cur = con.cursor()

    cur.execute(query)
    tag_list = cur.fetchall()

    con.close()

    print(tag_list)

    return render_template("webpages.html", tags=tag_list)


@app.route("/styles")
def render_styles():

    query = "SELECT assignment_name, due_date FROM assignments"

    con = create_connection(DATABASE)
    cur = con.cursor()

    cur.execute(query)
    tag_list = cur.fetchall()

    con.close()

    print(tag_list)

    return render_template("styles.html", tags=tag_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
