from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import csv
import json
import io
import shutil
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
# Save data in an easy-to-find folder in the user's Documents directory.
DATA_DIR = Path.home() / "Documents" / "Student Course Management"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "courses.db"
CSV_PATH = DATA_DIR / "courses.csv"

# Preserve data from an older project version if its database exists.
OLD_DB_PATH = APP_DIR / "courses.db"
if OLD_DB_PATH.exists() and not DB_PATH.exists():
    shutil.copy2(OLD_DB_PATH, DB_PATH)
app = Flask(__name__)
app.secret_key = "change-this-for-production"

DEFAULT_COURSES = [
    ("CYB 203", "Cybercrime Law and Countermeasures", 2),
    ("COS 201", "Computer Programming I", 3),
    ("ENT 211", "Entrepreneurship and Innovation", 2),
    ("MIVA-CYB 207", "Zero Trust Networking", 2),
    ("SEN 201", "Introduction to Software Engineering", 2),
    ("MTH 201", "Mathematical Methods I", 2),
    ("CYB 201", "Introduction to Cybersecurity and Strategy", 2),
    ("CYB 299", "SIWES I", 3),
]

def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE COLLATE NOCASE,
                title TEXT NOT NULL,
                units INTEGER NOT NULL CHECK(units BETWEEN 1 AND 10)
            )
        """)
        count = db.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO courses (code, title, units) VALUES (?, ?, ?)",
                DEFAULT_COURSES
            )
    export_courses_to_csv()

def get_all_courses():
    with connect_db() as db:
        rows = db.execute(
            "SELECT code, title, units FROM courses ORDER BY code"
        ).fetchall()
    return [{"code": row["code"], "title": row["title"], "units": row["units"]}
            for row in rows]

def export_courses_to_csv():
    """Automatically write a readable course list to Documents."""
    courses = get_all_courses()
    temp_path = CSV_PATH.with_suffix(".csv.tmp")
    with temp_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["code", "title", "units"])
        writer.writeheader()
        writer.writerows(courses)
    temp_path.replace(CSV_PATH)
    return len(courses)

@app.route("/")
def dashboard():
    search = request.args.get("q", "").strip()
    with connect_db() as db:
        if search:
            courses = db.execute(
                """SELECT * FROM courses
                   WHERE code LIKE ? OR title LIKE ?
                   ORDER BY code""",
                (f"%{search}%", f"%{search}%")
            ).fetchall()
        else:
            courses = db.execute("SELECT * FROM courses ORDER BY code").fetchall()
        total_courses = db.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_units = db.execute("SELECT COALESCE(SUM(units), 0) FROM courses").fetchone()[0]
    return render_template(
        "index.html",
        courses=courses,
        search=search,
        total_courses=total_courses,
        total_units=total_units,
        save_folder=str(DATA_DIR)
    )


@app.route("/save-file", methods=["POST"])
def save_file():
    """Manually refresh the readable CSV copy in Documents."""
    try:
        count = export_courses_to_csv()
        flash(f"Saved {count} course(s) to your Documents folder successfully.", "success")
    except OSError as exc:
        flash(f"Could not save the course list: {exc}", "error")
    return redirect(url_for("dashboard"))

@app.route("/upload-file", methods=["POST"])
def upload_file():
    """Import a CSV or JSON course list selected from the user's laptop."""
    uploaded = request.files.get("course_file")
    if not uploaded or not uploaded.filename:
        flash("Choose a .csv or .json course file to upload.", "error")
        return redirect(url_for("dashboard"))

    filename = uploaded.filename.lower()
    try:
        raw_text = uploaded.stream.read().decode("utf-8-sig")
        if filename.endswith(".json"):
            data = json.loads(raw_text)
            if isinstance(data, dict):
                data = data.get("courses", [])
        elif filename.endswith(".csv"):
            data = list(csv.DictReader(io.StringIO(raw_text)))
        else:
            flash("Unsupported file type. Please upload a .csv or .json file.", "error")
            return redirect(url_for("dashboard"))

        if not isinstance(data, list) or not data:
            flash("The uploaded file is empty or does not contain a course list.", "error")
            return redirect(url_for("dashboard"))

        cleaned = []
        seen_codes = set()
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Each course must have code, title, and units fields.")
            code = str(item.get("code", item.get("course_code", ""))).strip().upper()
            title = str(item.get("title", item.get("course_title", ""))).strip()
            try:
                units = int(item.get("units", item.get("credit_units", 0)))
            except (TypeError, ValueError):
                units = 0
            if not code or not title or not 1 <= units <= 10:
                raise ValueError("Every course needs a code, title, and units from 1 to 10.")
            if code.casefold() in seen_codes:
                raise ValueError(f"Duplicate course code in uploaded file: {code}.")
            seen_codes.add(code.casefold())
            cleaned.append((code, title, units))

        # Replace the current list only after the entire uploaded file validates.
        with connect_db() as db:
            db.execute("DELETE FROM courses")
            db.executemany(
                "INSERT INTO courses (code, title, units) VALUES (?, ?, ?)",
                cleaned
            )
        export_courses_to_csv()
        flash(f"Uploaded {len(cleaned)} course(s). Your laptop's saved course list has been updated.", "success")
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error, ValueError, sqlite3.IntegrityError, OSError) as exc:
        flash(f"Could not upload this file: {exc}", "error")
    return redirect(url_for("dashboard"))

@app.route("/download-csv")
def download_csv():
    """Download a copy of the saved course list."""
    export_courses_to_csv()
    return send_file(CSV_PATH, as_attachment=True, download_name="courses.csv", mimetype="text/csv")

@app.route("/add", methods=["POST"])
def add_course():
    code = request.form.get("code", "").strip().upper()
    title = request.form.get("title", "").strip()
    try:
        units = int(request.form.get("units", ""))
    except ValueError:
        units = 0

    if not code or not title:
        flash("Please enter both a course code and a course title.", "error")
    elif not 1 <= units <= 10:
        flash("Units must be a whole number from 1 to 10.", "error")
    else:
        try:
            with connect_db() as db:
                db.execute(
                    "INSERT INTO courses (code, title, units) VALUES (?, ?, ?)",
                    (code, title, units)
                )
            export_courses_to_csv()
            flash(f"{code} was added and saved automatically in your Documents folder.", "success")
        except sqlite3.IntegrityError:
            flash(f"A course with code {code} already exists.", "error")
        except OSError as exc:
            flash(f"Course was saved in the database, but the course-list copy could not be updated: {exc}", "error")
    return redirect(url_for("dashboard"))

@app.route("/edit/<int:course_id>", methods=["POST"])
def edit_course(course_id):
    code = request.form.get("code", "").strip().upper()
    title = request.form.get("title", "").strip()
    try:
        units = int(request.form.get("units", ""))
    except ValueError:
        units = 0

    if not code or not title or not 1 <= units <= 10:
        flash("Enter a code, title, and a unit value from 1 to 10.", "error")
    else:
        try:
            with connect_db() as db:
                result = db.execute(
                    "UPDATE courses SET code=?, title=?, units=? WHERE id=?",
                    (code, title, units, course_id)
                )
            if result.rowcount:
                export_courses_to_csv()
                flash("Course updated and saved automatically in your Documents folder.", "success")
            else:
                flash("Course not found.", "error")
        except sqlite3.IntegrityError:
            flash(f"Another course already uses the code {code}.", "error")
        except OSError as exc:
            flash(f"Course was updated in the database, but the course-list copy could not be updated: {exc}", "error")
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    with connect_db() as db:
        db.execute("DELETE FROM courses WHERE id=?", (course_id,))
    try:
        export_courses_to_csv()
        flash("Course deleted. Your local course list was updated automatically.", "success")
    except OSError as exc:
        flash(f"Course deleted from the database, but the course-list copy could not be updated: {exc}", "error")
    return redirect(url_for("dashboard"))

init_db()

if __name__ == "__main__":
    app.run(debug=True)
