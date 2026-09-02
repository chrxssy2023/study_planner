"""Study Planner."""

from flask import Flask, render_template, request
import sqlite3
from sqlite3 import Error
import calendar as cal
from datetime import datetime

# Create the Flask application.
app = Flask(__name__)

# Store the name of the database file.
DATABASE = "study_planner.db"


def create_connection(db_file):
    """Create a conneciton to the SQLite database."""
    try:
        # Connect to the database.
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        # Display an error if the connection fails.
        print(e)
    return None


def get_subjects(sort="subject_name"):
    """Get all the subjects from the database and sort them."""
    # List the columns that are allowed to be sorted.
    allowed_sorts = [
        "id",
        "subject_name",
        "teacher_name",
        "room",
        "credits"
    ]

    # Use subject name if an invalid sort is selected.
    if sort not in allowed_sorts:
        sort = "subject_name"

    # Sort credits from highest to lowest
    if sort == "credits":
        order = "DESC"
    else:
        order = "ASC"

    # Select the subject information from the database.
    query = f"""
        SELECT id, subject_name, teacher_name, room, credits
        FROM subjects
        ORDER BY {sort} {order}
    """

    # Connect to the database.
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get the results.
    cur.execute(query)
    rows = cur.fetchall()

    # Closes the database connection.
    con.close()

    return rows


def get_assignments(sort="assignment_name"):
    """Get assignments and their subject names, then sort them."""
    # List the columns that can be used for sorting.
    allowed_sorts = [
        "assignment_name",
        "subject_name",
        "due_date",
        "priority",
        "status"
    ]

    # Use assignment name if the sort is invalid.
    if sort not in allowed_sorts:
        sort = "assignment_name"

    # Give each priority a sorting number.
    if sort == "priority":
        order_by = """
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END
        """

    # Give each status a sorting number.
    elif sort == "status":
        order_by = """
            CASE status
                WHEN 'Not Started' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Complete' THEN 3
                ELSE 4
            END
        """

    else:
        # Sort using the selected database column.
        order_by = sort

    # Get assignments and match them with their subjects.
    query = f"""
        SELECT assignment_name, subject_name, due_date, priority, status
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        ORDER BY {order_by}
    """

    # Connect to the database.
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get all matching assignments.
    cur.execute(query)
    rows = cur.fetchall()

    # Close the database connection.
    con.close()

    return rows


@app.route("/")
def index():
    """Display the home page"""
    # Load the home page template.
    return render_template("index.html")


@app.route("/sort/<title>")
def render_sortpage(title):
    """Display search results sorted by assignment or subject."""
    # Get the selected sort and order
    sort = request.args.get("sort")
    order = request.args.get("order", "asc")

    # Change the order
    if order == "asc":
        new_order = "desc"
    else:
        new_order = "asc"

    # Only allow assignment or subject as sorting options.
    if sort not in ["assignment", "subject"]:
        sort = "assignment"

    # Choose the database column to sort by.
    if sort == "assignment":
        sort_column = "assignments.assignment_name"
    else:
        sort_column = "subjects.subject_name"

    # Select assignments and their subject names.
    query = f"""
        SELECT assignments.assignment_name, subjects.subject_name
        FROM assignments
        JOIN subjects
        ON assignments.subject_id = subjects.id
        ORDER BY {sort_column} {order}
    """

    # Connect to the database.
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get the results.
    cur.execute(query)
    tasks = cur.fetchall()

    # Close the database connection.
    con.close()

    # Send the results to the search page.
    return render_template(
        "search.html",
        tasks=tasks,
        title=title,
        order=new_order
    )


@app.route("/search", methods=["GET", "POST"])
def render_search():
    """Search assignments and subjects matching the user's search query."""
    # Get the search text entered by the user.
    search = request.form.get("search", "")

    # Create a title using the search text.
    title = "Search for " + search

    # Find assignments or subjects containing the search text.
    query = """
        SELECT assignments.assignment_name, subjects.subject_name
        FROM assignments
        JOIN subjects
        ON assignments.subject_id = subjects.id
        WHERE assignments.assignment_name LIKE ?
        OR subjects.subject_name LIKE ?
    """

    # Add wildcards to allow partial matches.
    search = "%" + search + "%"

    # Connect to the database.
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the search query using the user's search text.
    cur.execute(query, (search, search))
    tasks = cur.fetchall()

    # Close the database connection.
    con.close()

    # Display the search results.
    return render_template(
        "search.html",
        tasks=tasks,
        title=title,
        order="asc"
    )


@app.route("/assignments")
def assignments():
    """Display all assignments from the database."""
    # Get the selected sorting option.
    sort = request.args.get("sort", "assignment_name")

    # Get the assignments usign the selected sorting option.
    assignment_list = get_assignments(sort)

    # Send the assignments to the assignments page.
    return render_template(
        "assignments.html",
        assignments=assignment_list
    )


@app.route("/subjects")
def subjects():
    """Display all subjects from the database."""
    # Get the selected sorting option
    sort = request.args.get("sort", "subject_name")

    # Get the subjects using the selected sorting option.
    subject_list = get_subjects(sort)

    # Send the subjects to the subjects page.
    return render_template(
        "subjects.html",
        subjects=subject_list
    )


@app.route("/calendar")
def calendar():
    """Display a monthly calendar using the selected date."""
    # Get the month and year.
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    # Use today's date if no month or year was selected.
    if month is None or year is None:
        today = datetime.today()
        month = today.month
        year = today.year

    # Get the requested calendar navigation option.
    change = request.args.get("change")

    # Move to the next month.
    if change == "next":
        month = month + 1

        # Move to January and increase the year.
        if month == 13:
            month = 1
            year = year + 1

    # Move to the previous month.
    elif change == "previous":
        month = month - 1

        # Move to December and decrease the year.
        if month == 0:
            month = 12
            year = year - 1

    # Create the weeks and days for the selected month.
    month_days = cal.monthcalendar(year, month)

    # Get the name of the selected month.
    month_name = cal.month_name[month]

    # Send the calendar information to the template.
    return render_template(
        "calendar.html",
        month=month,
        year=year,
        month_name=month_name,
        month_days=month_days
    )


@app.route("/notes")
def notes():
    """Display the notes page."""
    return render_template("notes.html")


if __name__ == "__main__":
    # Run the Flask application.
    app.run(host="0.0.0.0", port=81, debug=True)
