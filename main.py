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

def get_subjects():
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT id, subject_name, teacher_name " \
    "FROM subjects ORDER BY subject_name")
    rows = cur.fetchall()
    con.close()
    return rows


def get_assignments():
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute("""
        SELECT assignment_name, subject_name, due_date, priority, status
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        ORDER BY a.due_date
    """)
    rows = cur.fetchall()
    con.close()
    return rows


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tags/<tag_type>")
def render_webpage(tag_type):
    title = tag_type.upper()
    tag_list = get_tags(tag_type)
    return render_template(
        "webtags.html",
        tags=tag_list,
        title=title,
        types=get_types(),
        order="asc"
    )


@app.route("/sort/<title>")
def render_sortpage(title):
    sort = request.args.get("sort")
    order = request.args.get("order", "asc")

    if order == "asc":
        new_order = "desc"
    else:
        new_order = "asc"

    if sort not in ["tag", "description"]:
        sort = "tag"

    query = f"""
        SELECT tag, description
        FROM html_tags
        WHERE type=?
        ORDER BY {sort} {order}
    """

    con = create_connection(DATABASE)
    cur = con.cursor()

    cur.execute(query, (title.upper(),))
    tag_list = cur.fetchall()

    con.close()

    return render_template(
        "webtags.html",
        tags=tag_list,
        title=title.upper(),
        types=get_types(),
        order=new_order
    )


@app.route("/search", methods=["GET", "POST"])
def render_search():
    search = request.form.get("search", "")
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

    return render_template(
        "webtags.html",
        tags=tag_list,
        title=title,
        types=get_types(),
        order="asc"
    )


@app.route("/assignments")
def assignments():
    assignment_list = get_assignments()
    return render_template("assignments.html", assignments=assignment_list)


@app.route("/subjects")
def subjects():
    subject_list = get_subjects()
    return render_template("subjects.html", subjects=subject_list)


@app.route("/calendar")
def calendar():
    return render_template("calendar.html")


@app.route("/notes")
def notes():
    return render_template("notes.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
