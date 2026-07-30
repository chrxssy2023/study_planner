from flask import Flask, render_template, request
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


def get_tags(tag_type):
    title = tag_type.upper()
    query = "SELECT tag, description FROM html_tags WHERE type=?"

    con = create_connection(DATABASE)
    cur = con.cursor()

    cur.execute(query, (title,))
    tag_list = cur.fetchall()
    con.close()

    print(tag_list)
    return tag_list


def get_types():
    con = create_connection(DATABASE)
    cur = con.cursor()

    query = "SELECT DISTINCT type FROM html_tags ORDER BY type ASC"

    cur.execute(query)
    records = cur.fetchall()

    print(records)

    for i in range(len(records)):
        records[i] = records[i][0]

    print(records)

    con.close()
    return records


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tags/<tag_type>")
def render_webpage(tag_type):
    title = tag_type.upper()
    tag_list = get_tags(tag_type)
    return render_template("webtags.html", tags=get_tags(tag_type),
title=title, types=get_types())


@app.route("/search", methods=["GET", "POST"])
def render_search():
    search = request.form["search"]
    title = "Search for " + search

    query = """
        SELECT tag, description
        FROM html_tags
        WHERE tag LIKE ?
        OR description LIKE ?
    """

    search = "%" + search + "%"

    con = create_connection(DATABASE)
    cur = con.cursor()

    cur.execute(query, (search, search))
    tag_list = cur.fetchall()

    con.close()

    return render_template("webtags.html", tags=tag_list, 
                           title=title, types=get_types())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
