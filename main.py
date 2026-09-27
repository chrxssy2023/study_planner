"""Studyous."""

# Import the Flask tools needed to create pages and handle requests
import calendar as cal
from datetime import datetime

# Import SQLite to connect the website to the database
import sqlite3

# Import the database error type so connection errors can be handled
from sqlite3 import Error

from flask import Flask, redirect, render_template, request

# Create the Flask application
app = Flask(__name__)

# Store the name of the SQLite database file
DATABASE = "study_planner.db"

# Store the different colour themes available on the website
THEMES = ["pink", "light", "dark", "colourblind"]


def create_connection(db_file):
    """Create a connection to the SQLite database."""
    try:
        # Connect to the database.
        connection = sqlite3.connect(db_file)

        # Return the database connection.
        return connection

    except Error as e:
        # Display an error if the database connection fails
        print(e)

    return None


def get_subjects(sort="subject_name", order="asc"):
    """Get all subjects from the database and sort them."""
    # List the columns that users are allowed to sort by
    allowed_sorts = [
        "id",
        "subject_name",
        "teacher_name",
        "room",
        "credits",
    ]

    # Use subject name if the sort option is invalid
    if sort not in allowed_sorts:
        sort = "subject_name"

    # Change sort order to uppercase.
    order = order.upper()

    # Only allow ascending or descending sorting
    if order not in ("ASC", "DESC"):
        order = "ASC"

    # Select the subject information from the database
    query = f"""
        SELECT id, subject_name, teacher_name, room, credits
        FROM subjects
        ORDER BY {sort} {order}
    """

    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get results
    cur.execute(query)
    rows = cur.fetchall()

    # Close the database connection after getting the data
    con.close()

    # Return the list of subjects
    return rows


def get_assignments(
    sort="assignment_name", order="asc", incomplete_only=False
):
    """Get assignments and their subject names, then sort them."""
    # List columns that users are allowed to sort by
    allowed_sorts = [
        "assignment_name",
        "subject_name",
        "due_date",
        "priority",
        "status",
    ]

    # Use assignment name if an invalid sort option is selected
    if sort not in allowed_sorts:
        sort = "assignment_name"

    # Give each priority a sorting number so High appears before Medium/Low
    if sort == "priority":
        order_by = """
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END
        """

    # Give each status a sorting number so statuses appear in a set order
    elif sort == "status":
        order_by = """
            CASE status
                WHEN 'Not Started' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Completed' THEN 3
                ELSE 4
            END
        """

    else:
        # Sort using the selected database column
        order_by = sort

    # Convert the sorting order to uppercase
    order = order.upper()

    # Only allow ascending or descending sorting
    if order not in ("ASC", "DESC"):
        order = "ASC"

    # Start with no WHERE condition
    where_clause = ""

    # If incomplete_only is selected, remove completed assignments
    if incomplete_only:
        where_clause = "WHERE a.status != 'Completed'"

    # Get assignments and match them with their subject names
    query = f"""
        SELECT assignment_name, subject_name, due_date, priority, status
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        {where_clause}
        ORDER BY {order_by} {order}
    """

    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get all matching assignments
    cur.execute(query)
    rows = cur.fetchall()

    # Close the database connection
    con.close()

    # Return the assignments
    return rows


def get_reminder_by_id(assignment_id):
    """Get one incomplete assignment for the reminder detail view."""
    # Select one assignment and its subject information
    query = """
        SELECT a.assignment_name, s.subject_name,
               a.due_date, a.priority, a.status
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.id = ? AND a.status != 'Completed'
    """

    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Find the assignment using its ID
    cur.execute(query, (assignment_id,))
    row = cur.fetchone()

    # Close the database connection
    con.close()

    # Return the selected reminder
    return row


def get_reminders():
    """Get upcoming assignments to display as reminders in the sidebar."""
    # Select incomplete assignments and their subject information
    query = """
        SELECT assignments.id,
               assignments.assignment_name,
               subjects.subject_name,
               assignments.due_date,
               assignments.priority,
               assignments.status
        FROM assignments
        JOIN subjects
        ON assignments.subject_id = subjects.id
        WHERE assignments.status != 'Completed'
        ORDER BY assignments.due_date ASC
        LIMIT 5
    """

    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get the reminders
    cur.execute(query)
    rows = cur.fetchall()

    # Close the database connection
    con.close()

    # Return the five closest upcoming reminders
    return rows


@app.context_processor
def inject_reminders():
    """Make reminders available on every page."""
    # Send the reminders to all templates
    return {"reminders": get_reminders()}


@app.route("/")
def index():
    """Display the home page."""
    # Get a random study quote from the database
    quote = get_quote()

    # Display the homepage and send the quote to the template
    return render_template("index.html", quote=quote)


@app.route("/sort/<title>")
def render_sortpage(title):
    """Display search results sorted by assignment or subject."""
    # Get the selected sorting option from the URL
    sort = request.args.get("sort")
    order = request.args.get("order", "asc")

    # Change the order for the next time the user clicks the sort button
    new_order = "desc" if order == "asc" else "asc"

    # Only allow assignment or subject as sorting options
    if sort not in ["assignment", "subject"]:
        sort = "assignment"

    # Choose the database column to sort by
    if sort == "assignment":
        sort_column = "assignments.assignment_name"
    else:
        sort_column = "subjects.subject_name"

    # Select assignments and their subject names
    query = f"""
        SELECT assignments.assignment_name, subjects.subject_name
        FROM assignments
        JOIN subjects
        ON assignments.subject_id = subjects.id
        ORDER BY {sort_column} {order}
    """

    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get the results
    cur.execute(query)
    tasks = cur.fetchall()

    # Close the database connection
    con.close()

    # Send the results to the search page
    return render_template(
        "search.html", tasks=tasks, title=title, order=new_order
    )


@app.route("/search", methods=["GET", "POST"])
def render_search():
    """Search assignments and subjects matching the user's search query."""
    # Get the search text entered by the user
    search = request.form.get("search", "").strip()

    # Create a title using the search text
    title = "Search for " + search

    # Find assignments or subjects containing the search text
    if not search:
        # Show no results if the search box is empty
        tasks = []

    else:
        # Search for the text in assignment and subject names
        query = """
            SELECT assignments.assignment_name, subjects.subject_name
            FROM assignments
            JOIN subjects
            ON assignments.subject_id = subjects.id
            WHERE assignments.assignment_name LIKE ?
            OR subjects.subject_name LIKE ?
        """

        # Add wildcards so partial words can also be found
        search = "%" + search + "%"

        # Connect to the database
        con = create_connection(DATABASE)
        cur = con.cursor()

        # Run the search using the user's search text
        cur.execute(query, (search, search))
        tasks = cur.fetchall()

        # Close the database connection
        con.close()

    # Display the search results
    return render_template(
        "search.html", tasks=tasks, title=title, order="asc"
    )


@app.route("/assignments")
def assignments():
    """Display all assignments from the database."""
    # Get the selected sorting option from the URL
    sort = request.args.get("sort", "assignment_name")
    order = request.args.get("order", "asc")

    # Change the order for the next sort button click
    new_order = "desc" if order == "asc" else "asc"

    # Get the assignments using the selected sorting option
    assignment_list = get_assignments(sort, order)

    # Send the assignments to the assignments page
    return render_template(
        "assignments.html", assignments=assignment_list, order=new_order
    )


@app.route("/subjects")
def subjects():
    """Display all subjects from the database."""

    # Get the selected sorting option from the URL
    sort = request.args.get("sort", "subject_name")
    order = request.args.get("order", "asc")

    # Change the order for the next sort button click
    new_order = "desc" if order == "asc" else "asc"

    # Get the subjects using the selected sorting option
    subject_list = get_subjects(sort, order)

    # Send the subjects to the subjects page
    return render_template(
        "subjects.html", subjects=subject_list, order=new_order
    )


@app.route("/calendar")
def calendar():
    """Display a monthly calendar using the selected date."""
    # Get the month and year selected by the user
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    # Get today's date
    today = datetime.today()

    # Use today's month and year if no date was selected
    if month is None or year is None:
        month = today.month
        year = today.year

    # Store today's day, month and year so it can be highlighted
    today_day = today.day
    today_month = today.month
    today_year = today.year

    # Get the calendar navigation option
    change = request.args.get("change")

    # Move to the next month
    if change == "next":
        month += 1

        # If December is passed, move to January of next year
        if month == 13:
            month = 1
            year += 1

    # Move to the previous month
    elif change == "previous":
        month -= 1

        # If January is passed, move to December of previous year
        if month == 0:
            month = 12
            year -= 1

    # Create the weeks and days for the selected month
    month_days = cal.monthcalendar(year, month)

    # Get the name of the selected month
    month_name = cal.month_name[month]

    # Send the calendar information to the template
    return render_template(
        "calendar.html",
        month=month,
        year=year,
        month_name=month_name,
        month_days=month_days,
        today_day=today_day,
        today_month=today_month,
        today_year=today_year,
    )


@app.route("/notes")
@app.route("/notes/<int:note_id>")
def notes(note_id=None):
    """Display the notes page."""
    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Get all notes and sort them by their creation time
    cur.execute("""
        SELECT id, title, note, created_at
        FROM notes
        ORDER BY created_at DESC
    """)
    notes_list = cur.fetchall()

    # Start with no selected note
    selected_note = None

    # If the user selected a specific note, find it using its ID
    if note_id is not None:
        cur.execute(
            """
            SELECT id, title, note, created_at
            FROM notes
            WHERE id = ?
        """,
            (note_id,),
        )
        selected_note = cur.fetchone()

    # If no note was selected, display the newest note first
    elif notes_list:
        selected_note = notes_list[0]

    # Close the database connection
    con.close()

    # Send the notes to the notes page
    return render_template(
        "notes.html", notes=notes_list, selected_note=selected_note
    )


@app.route("/theme/<theme>")
def change_theme(theme):
    """Change the colour theme of the website."""
    # Only allow the four available themes
    if theme not in THEMES:
        theme = "pink"

    # Save the selected theme in a browser cookie
    response = redirect(request.referrer or "/")
    response.set_cookie("theme", theme)

    # Return the user to the previous page
    return response


@app.route("/reminders")
def reminders():
    """Display all upcoming reminders."""
    # Get the assignment ID if the user selected one reminder
    assignment_id = request.args.get("id", type=int)

    # Get selected sorting option
    sort = request.args.get("sort", "due_date")
    order = request.args.get("order", "asc")

    # List the columns that reminders can be sorted by
    allowed_sorts = [
        "assignment_name",
        "subject_name",
        "due_date",
        "priority",
        "status",
    ]

    # Use due date if an invalid sorting option is selected
    if sort not in allowed_sorts:
        sort = "due_date"

    # Change the order for the next sort button click
    new_order = "desc" if order == "asc" else "asc"

    # If an assignment ID was selected, display only that reminder
    if assignment_id:
        row = get_reminder_by_id(assignment_id)
        reminder_list = [row] if row else []
        page_title = "Reminder"

    else:
        # Otherwise, display all incomplete assignments as reminders
        reminder_list = get_assignments(
            sort, order, incomplete_only=True
        )
        page_title = "All Reminders"

    # Send the reminders to the reminders page
    return render_template(
        "reminders.html",
        all_reminders=reminder_list,
        order=new_order,
        page_title=page_title,
    )


def get_quote():
    """Get one random quote from the database."""
    # Select one random quote and its author
    query = """
        SELECT quote, author
        FROM quotes
        ORDER BY RANDOM()
        LIMIT 1
    """

    # Connect to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Run the query and get one random quote
    cur.execute(query)
    quote = cur.fetchone()

    # Close the database connection
    con.close()

    # Return the quote.
    return quote


# Only run Flask application when this file is run directly
if __name__ == "__main__":
    # Start website on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
