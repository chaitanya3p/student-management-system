import os

import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def login_required():
    return session.get("admin_logged_in")


# =========================
# LOGIN
# =========================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"].strip()

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT password FROM admins WHERE username = %s",
                (username,)
            )

            admin = cursor.fetchone()

            if admin and check_password_hash(admin[0], password):

                session["admin_logged_in"] = True
                session["username"] = username

                return redirect(url_for("dashboard"))

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

        except mysql.connector.Error as error:

            return render_template(
                "login.html",
                error=f"Database error: {error}"
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM marks")
        marks_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]

        return render_template(
            "dashboard.html",
            student_count=student_count,
            subject_count=subject_count,
            marks_count=marks_count,
            attendance_count=attendance_count,
            username=session.get("username")
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# STUDENTS
# ============================================================

@app.route("/students")
def students():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        search = request.args.get("search", "").strip()

        if search:

            search_value = f"%{search}%"

            cursor.execute(
                """
                SELECT *
                FROM students
                WHERE name LIKE %s
                   OR email LIKE %s
                   OR department LIKE %s
                   OR phone LIKE %s
                ORDER BY student_id
                """,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM students
                ORDER BY student_id
                """
            )

        student_list = cursor.fetchall()

        return render_template(
            "students.html",
            students=student_list,
            search=search,
            username=session.get("username")
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# ADD STUDENT
# -------------------------

@app.route("/students/add", methods=["GET", "POST"])
def add_student():

    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        department = request.form["department"].strip()
        year = request.form["year"].strip()

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO students
                (name, email, phone, department, year)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    phone,
                    department,
                    year
                )
            )

            connection.commit()

            return redirect(url_for("students"))

        except mysql.connector.Error as error:

            return f"Database error: {error}"

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("add_student.html")


# -------------------------
# EDIT STUDENT
# -------------------------

@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            name = request.form["name"].strip()
            email = request.form["email"].strip()
            phone = request.form["phone"].strip()
            department = request.form["department"].strip()
            year = request.form["year"].strip()

            cursor.execute(
                """
                UPDATE students
                SET name = %s,
                    email = %s,
                    phone = %s,
                    department = %s,
                    year = %s
                WHERE student_id = %s
                """,
                (
                    name,
                    email,
                    phone,
                    department,
                    year,
                    student_id
                )
            )

            connection.commit()

            return redirect(url_for("students"))

        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE student_id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:
            return "Student not found."

        return render_template(
            "edit_student.html",
            student=student
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# DELETE STUDENT
# -------------------------

@app.route("/students/delete/<int:student_id>")
def delete_student(student_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Delete related records first
        cursor.execute(
            "DELETE FROM marks WHERE student_id = %s",
            (student_id,)
        )

        cursor.execute(
            "DELETE FROM attendance WHERE student_id = %s",
            (student_id,)
        )

        cursor.execute(
            "DELETE FROM students WHERE student_id = %s",
            (student_id,)
        )

        connection.commit()

        return redirect(url_for("students"))

    except mysql.connector.Error as error:

        connection.rollback()

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# SUBJECTS
# ============================================================

@app.route("/subjects")
def subjects():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM subjects
            ORDER BY subject_id
            """
        )

        subject_list = cursor.fetchall()

        return render_template(
            "subjects.html",
            subjects=subject_list
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# ADD SUBJECT
# -------------------------

@app.route("/subjects/add", methods=["GET", "POST"])
def add_subject():

    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":

        subject_name = request.form["subject_name"].strip()
        department = request.form["department"].strip()
        semester = request.form["semester"].strip()

        connection = None
        cursor = None

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO subjects
                (subject_name, department, semester)
                VALUES (%s, %s, %s)
                """,
                (
                    subject_name,
                    department,
                    semester
                )
            )

            connection.commit()

            return redirect(url_for("subjects"))

        except mysql.connector.Error as error:

            return f"Database error: {error}"

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("add_subject.html")


# -------------------------
# EDIT SUBJECT
# -------------------------

@app.route("/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            subject_name = request.form["subject_name"].strip()
            department = request.form["department"].strip()
            semester = request.form["semester"].strip()

            cursor.execute(
                """
                UPDATE subjects
                SET subject_name = %s,
                    department = %s,
                    semester = %s
                WHERE subject_id = %s
                """,
                (
                    subject_name,
                    department,
                    semester,
                    subject_id
                )
            )

            connection.commit()

            return redirect(url_for("subjects"))

        cursor.execute(
            """
            SELECT *
            FROM subjects
            WHERE subject_id = %s
            """,
            (subject_id,)
        )

        subject = cursor.fetchone()

        if not subject:
            return "Subject not found."

        return render_template(
            "edit_subject.html",
            subject=subject
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# DELETE SUBJECT
# -------------------------

@app.route("/subjects/delete/<int:subject_id>")
def delete_subject(subject_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Delete related records first
        cursor.execute(
            "DELETE FROM marks WHERE subject_id = %s",
            (subject_id,)
        )

        cursor.execute(
            "DELETE FROM attendance WHERE subject_id = %s",
            (subject_id,)
        )

        cursor.execute(
            "DELETE FROM subjects WHERE subject_id = %s",
            (subject_id,)
        )

        connection.commit()

        return redirect(url_for("subjects"))

    except mysql.connector.Error as error:

        connection.rollback()

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# MARKS
# ============================================================

@app.route("/marks")
def marks():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                marks.mark_id,
                students.student_id,
                students.name AS student_name,
                subjects.subject_id,
                subjects.subject_name,
                marks.marks
            FROM marks
            INNER JOIN students
                ON marks.student_id = students.student_id
            INNER JOIN subjects
                ON marks.subject_id = subjects.subject_id
            ORDER BY marks.mark_id
            """
        )

        mark_list = cursor.fetchall()

        return render_template(
            "marks.html",
            marks=mark_list
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# ADD MARKS
# -------------------------

@app.route("/marks/add", methods=["GET", "POST"])
def add_marks():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            student_id = request.form["student_id"]
            subject_id = request.form["subject_id"]
            mark = request.form["marks"]

            cursor.execute(
                """
                SELECT mark_id
                FROM marks
                WHERE student_id = %s
                AND subject_id = %s
                """,
                (
                    student_id,
                    subject_id
                )
            )

            existing = cursor.fetchone()

            if existing:

                cursor.execute(
                    """
                    UPDATE marks
                    SET marks = %s
                    WHERE student_id = %s
                    AND subject_id = %s
                    """,
                    (
                        mark,
                        student_id,
                        subject_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO marks
                    (student_id, subject_id, marks)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        student_id,
                        subject_id,
                        mark
                    )
                )

            connection.commit()

            return redirect(url_for("marks"))

        cursor.execute(
            """
            SELECT student_id, name
            FROM students
            ORDER BY name
            """
        )

        student_list = cursor.fetchall()

        cursor.execute(
            """
            SELECT subject_id, subject_name
            FROM subjects
            ORDER BY subject_name
            """
        )

        subject_list = cursor.fetchall()

        return render_template(
            "add_marks.html",
            students=student_list,
            subjects=subject_list
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# DELETE MARK
# -------------------------

@app.route("/marks/delete/<int:mark_id>")
def delete_mark(mark_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM marks WHERE mark_id = %s",
            (mark_id,)
        )

        connection.commit()

        return redirect(url_for("marks"))

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# ATTENDANCE
# ============================================================

@app.route("/attendance")
def attendance():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                attendance.attendance_id,
                students.name AS student_name,
                subjects.subject_name,
                attendance.total_classes,
                attendance.attended_classes
            FROM attendance
            INNER JOIN students
                ON attendance.student_id = students.student_id
            INNER JOIN subjects
                ON attendance.subject_id = subjects.subject_id
            ORDER BY attendance.attendance_id
            """
        )

        attendance_list = cursor.fetchall()

        for record in attendance_list:

            if record["total_classes"] > 0:

                record["percentage"] = round(
                    (
                        record["attended_classes"]
                        / record["total_classes"]
                    ) * 100,
                    2
                )

            else:

                record["percentage"] = 0

        return render_template(
            "attendance.html",
            attendance=attendance_list
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# ADD / UPDATE ATTENDANCE
# -------------------------

@app.route("/attendance/add", methods=["GET", "POST"])
def add_attendance():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            student_id = request.form["student_id"]
            subject_id = request.form["subject_id"]
            total_classes = request.form["total_classes"]
            attended_classes = request.form["attended_classes"]

            cursor.execute(
                """
                SELECT attendance_id
                FROM attendance
                WHERE student_id = %s
                AND subject_id = %s
                """,
                (
                    student_id,
                    subject_id
                )
            )

            existing = cursor.fetchone()

            if existing:

                cursor.execute(
                    """
                    UPDATE attendance
                    SET total_classes = %s,
                        attended_classes = %s
                    WHERE student_id = %s
                    AND subject_id = %s
                    """,
                    (
                        total_classes,
                        attended_classes,
                        student_id,
                        subject_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO attendance
                    (
                        student_id,
                        subject_id,
                        total_classes,
                        attended_classes
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        student_id,
                        subject_id,
                        total_classes,
                        attended_classes
                    )
                )

            connection.commit()

            return redirect(url_for("attendance"))

        cursor.execute(
            """
            SELECT student_id, name
            FROM students
            ORDER BY name
            """
        )

        student_list = cursor.fetchall()

        cursor.execute(
            """
            SELECT subject_id, subject_name
            FROM subjects
            ORDER BY subject_name
            """
        )

        subject_list = cursor.fetchall()

        return render_template(
            "add_attendance.html",
            students=student_list,
            subjects=subject_list
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# -------------------------
# DELETE ATTENDANCE
# -------------------------

@app.route("/attendance/delete/<int:attendance_id>")
def delete_attendance(attendance_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM attendance
            WHERE attendance_id = %s
            """,
            (attendance_id,)
        )

        connection.commit()

        return redirect(url_for("attendance"))

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RESULTS
# ============================================================

@app.route("/results")
def results():

    if not login_required():
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT student_id, name
            FROM students
            ORDER BY name
            """
        )

        student_list = cursor.fetchall()

        selected_student = request.args.get("student_id")

        result = None

        if selected_student:

            cursor.execute(
                """
                SELECT
                    students.student_id,
                    students.name,
                    subjects.subject_name,
                    marks.marks
                FROM marks
                INNER JOIN students
                    ON marks.student_id = students.student_id
                INNER JOIN subjects
                    ON marks.subject_id = subjects.subject_id
                WHERE students.student_id = %s
                ORDER BY subjects.subject_name
                """,
                (selected_student,)
            )

            mark_list = cursor.fetchall()

            if mark_list:

                total_marks = sum(
                    item["marks"]
                    for item in mark_list
                )

                subject_count = len(mark_list)

                average = total_marks / subject_count

                percentage = average

                if percentage >= 90:
                    grade = "A+"
                elif percentage >= 80:
                    grade = "A"
                elif percentage >= 70:
                    grade = "B"
                elif percentage >= 60:
                    grade = "C"
                elif percentage >= 50:
                    grade = "D"
                else:
                    grade = "F"

                passed = all(
                    item["marks"] >= 40
                    for item in mark_list
                )

                result = {
                    "student_id": mark_list[0]["student_id"],
                    "student_name": mark_list[0]["name"],
                    "marks": mark_list,
                    "total": total_marks,
                    "average": round(average, 2),
                    "percentage": round(percentage, 2),
                    "grade": grade,
                    "status": "PASS" if passed else "FAIL"
                }

        return render_template(
            "results.html",
            students=student_list,
            result=result,
            selected_student=selected_student
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)