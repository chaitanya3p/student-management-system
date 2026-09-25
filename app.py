import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from werkzeug.security import check_password_hash


load_dotenv()


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


def get_student_id():
    try:
        student_id = int(input("Enter student ID: ").strip())

        if student_id <= 0:
            raise ValueError

        return student_id

    except ValueError:
        print("Student ID must be a positive whole number.")
        return None


def get_subject_id():
    try:
        subject_id = int(input("Enter subject ID: ").strip())

        if subject_id <= 0:
            raise ValueError

        return subject_id

    except ValueError:
        print("Subject ID must be a positive whole number.")
        return None


def admin_login(connection):
    username = input("Enter admin username: ").strip()
    password = input("Enter admin password: ").strip()

    query = """
        SELECT password
        FROM admins
        WHERE username = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (username,)
        )

        admin = cursor.fetchone()

        if admin is None:
            print("Invalid username or password.")
            return False

        stored_password = admin[0]

        if not check_password_hash(stored_password, password):
            print("Invalid username or password.")
            return False

        print("Login successful.")
        return True

    except Error as error:
        print(f"Login error: {error}")
        return False

    finally:
        if cursor is not None:
            cursor.close()


def add_student(connection):
    name = input("Enter name: ").strip()
    email = input("Enter email: ").strip()
    phone = input("Enter phone (optional): ").strip() or None
    department = input("Enter department (optional): ").strip() or None

    if not name or not email:
        print("Name and email are required.")
        return

    year_text = input("Enter year (optional): ").strip()

    if year_text:
        try:
            year = int(year_text)
        except ValueError:
            print("Year must be a whole number.")
            return
    else:
        year = None

    query = """
        INSERT INTO students
        (name, email, phone, department, year)
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (name, email, phone, department, year)
        )

        connection.commit()

        print("Student added successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not add student: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def view_all_students(connection):
    query = """
        SELECT student_id, name, email, phone, department, year
        FROM students
        ORDER BY student_id
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(query)

        students = cursor.fetchall()

        if not students:
            print("No students found.")
            return

        print("\nID | Name | Email | Phone | Department | Year")
        print("-" * 75)

        for student in students:
            print(
                " | ".join(
                    str(value) if value is not None else ""
                    for value in student
                )
            )

    except Error as error:
        print(f"Could not retrieve students: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def search_student(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    query = """
        SELECT student_id, name, email, phone, department, year
        FROM students
        WHERE student_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:
            print("Student not found.")
            return

        print("\n========== STUDENT ==========")
        print(f"ID         : {student[0]}")
        print(f"Name       : {student[1]}")
        print(f"Email      : {student[2]}")
        print(f"Phone      : {student[3] or 'Not provided'}")
        print(f"Department : {student[4] or 'Not provided'}")
        print(f"Year       : {student[5] or 'Not provided'}")
        print("=============================")

    except Error as error:
        print(f"Could not search for student: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def update_student(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    name = input("Enter new name: ").strip()
    email = input("Enter new email: ").strip()
    phone = input("Enter new phone (optional): ").strip() or None
    department = input("Enter new department (optional): ").strip() or None
    year_text = input("Enter new year (optional): ").strip()

    if not name or not email:
        print("Name and email are required.")
        return

    if year_text:
        try:
            year = int(year_text)
        except ValueError:
            print("Year must be a whole number.")
            return
    else:
        year = None

    query = """
        UPDATE students
        SET name = %s,
            email = %s,
            phone = %s,
            department = %s,
            year = %s
        WHERE student_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
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

        if cursor.rowcount == 0:
            print("Student not found.")
        else:
            print("Student updated successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not update student: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def delete_student(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    confirmation = input(
        "Are you sure you want to delete this student? (y/n): "
    ).strip().lower()

    if confirmation != "y":
        print("Delete cancelled.")
        return

    query = """
        DELETE FROM students
        WHERE student_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (student_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Student not found.")
        else:
            print("Student deleted successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not delete student: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def add_subject(connection):
    subject_name = input("Enter subject name: ").strip()
    department = input("Enter department: ").strip()
    semester_text = input("Enter semester: ").strip()

    if not subject_name:
        print("Subject name is required.")
        return

    try:
        semester = int(semester_text)

        if semester <= 0:
            raise ValueError

    except ValueError:
        print("Semester must be a positive whole number.")
        return

    query = """
        INSERT INTO subjects
        (subject_name, department, semester)
        VALUES (%s, %s, %s)
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                subject_name,
                department,
                semester
            )
        )

        connection.commit()

        print("Subject added successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not add subject: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def view_all_subjects(connection):
    query = """
        SELECT subject_id, subject_name, department, semester
        FROM subjects
        ORDER BY subject_id
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(query)

        subjects = cursor.fetchall()

        if not subjects:
            print("No subjects found.")
            return

        print("\nID | Subject | Department | Semester")
        print("-" * 60)

        for subject in subjects:
            print(
                f"{subject[0]} | "
                f"{subject[1]} | "
                f"{subject[2] or ''} | "
                f"{subject[3] or ''}"
            )

    except Error as error:
        print(f"Could not retrieve subjects: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def update_subject(connection):
    subject_id = get_subject_id()

    if subject_id is None:
        return

    subject_name = input("Enter new subject name: ").strip()
    department = input("Enter new department: ").strip()
    semester_text = input("Enter new semester: ").strip()

    if not subject_name:
        print("Subject name is required.")
        return

    try:
        semester = int(semester_text)

        if semester <= 0:
            raise ValueError

    except ValueError:
        print("Semester must be a positive whole number.")
        return

    query = """
        UPDATE subjects
        SET subject_name = %s,
            department = %s,
            semester = %s
        WHERE subject_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                subject_name,
                department,
                semester,
                subject_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Subject not found.")
        else:
            print("Subject updated successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not update subject: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def delete_subject(connection):
    subject_id = get_subject_id()

    if subject_id is None:
        return

    confirmation = input(
        "Are you sure you want to delete this subject? (y/n): "
    ).strip().lower()

    if confirmation != "y":
        print("Delete cancelled.")
        return

    query = """
        DELETE FROM subjects
        WHERE subject_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (subject_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Subject not found.")
        else:
            print("Subject deleted successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not delete subject: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def add_marks(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    subject_id = get_subject_id()

    if subject_id is None:
        return

    try:
        marks = int(
            input("Enter marks (0-100): ").strip()
        )

    except ValueError:
        print("Marks must be a whole number.")
        return

    if marks < 0 or marks > 100:
        print("Marks must be between 0 and 100.")
        return

    query = """
        INSERT INTO marks
        (student_id, subject_id, marks)
        VALUES (%s, %s, %s)
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                student_id,
                subject_id,
                marks
            )
        )

        connection.commit()

        print("Marks added successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not add marks: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def view_student_marks(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    query = """
        SELECT
            sub.subject_id,
            sub.subject_name,
            m.marks
        FROM marks m
        JOIN subjects sub
            ON m.subject_id = sub.subject_id
        WHERE m.student_id = %s
        ORDER BY sub.subject_id
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (student_id,)
        )

        results = cursor.fetchall()

        if not results:
            print("No marks found for this student.")
            return

        print("\n========== STUDENT MARKS ==========")
        print(f"Student ID: {student_id}")
        print("-----------------------------------")

        for result in results:
            print(
                f"Subject ID: {result[0]} | "
                f"{result[1]} | "
                f"Marks: {result[2]}"
            )

        print("===================================")

    except Error as error:
        print(f"Could not retrieve marks: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def update_marks(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    subject_id = get_subject_id()

    if subject_id is None:
        return

    try:
        new_marks = int(
            input("Enter new marks (0-100): ").strip()
        )

    except ValueError:
        print("Marks must be a whole number.")
        return

    if new_marks < 0 or new_marks > 100:
        print("Marks must be between 0 and 100.")
        return

    query = """
        UPDATE marks
        SET marks = %s
        WHERE student_id = %s
        AND subject_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                new_marks,
                student_id,
                subject_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Marks record not found.")
        else:
            print("Marks updated successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not update marks: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def delete_marks(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    subject_id = get_subject_id()

    if subject_id is None:
        return

    confirmation = input(
        "Are you sure you want to delete these marks? (y/n): "
    ).strip().lower()

    if confirmation != "y":
        print("Delete cancelled.")
        return

    query = """
        DELETE FROM marks
        WHERE student_id = %s
        AND subject_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                student_id,
                subject_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Marks record not found.")
        else:
            print("Marks deleted successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not delete marks: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def add_attendance(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    subject_id = get_subject_id()

    if subject_id is None:
        return

    try:
        total_classes = int(
            input("Enter total classes: ").strip()
        )

        attended_classes = int(
            input("Enter attended classes: ").strip()
        )

    except ValueError:
        print("Classes must be whole numbers.")
        return

    if total_classes <= 0:
        print("Total classes must be greater than 0.")
        return

    if attended_classes < 0:
        print("Attended classes cannot be negative.")
        return

    if attended_classes > total_classes:
        print("Attended classes cannot be greater than total classes.")
        return

    query = """
        INSERT INTO attendance
        (student_id, subject_id, total_classes, attended_classes)
        VALUES (%s, %s, %s, %s)
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                student_id,
                subject_id,
                total_classes,
                attended_classes
            )
        )

        connection.commit()

        print("Attendance added successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not add attendance: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def view_student_attendance(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    query = """
        SELECT
            sub.subject_id,
            sub.subject_name,
            a.total_classes,
            a.attended_classes,
            (a.attended_classes * 100.0 / a.total_classes)
        FROM attendance a
        JOIN subjects sub
            ON a.subject_id = sub.subject_id
        WHERE a.student_id = %s
        ORDER BY sub.subject_id
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (student_id,)
        )

        results = cursor.fetchall()

        if not results:
            print("No attendance found for this student.")
            return

        print("\n========== STUDENT ATTENDANCE ==========")
        print(f"Student ID: {student_id}")
        print("----------------------------------------")

        for result in results:
            print(
                f"Subject ID: {result[0]} | "
                f"{result[1]} | "
                f"Total: {result[2]} | "
                f"Attended: {result[3]} | "
                f"Percentage: {result[4]:.2f}%"
            )

        print("========================================")

    except Error as error:
        print(f"Could not retrieve attendance: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def update_attendance(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    subject_id = get_subject_id()

    if subject_id is None:
        return

    try:
        total_classes = int(
            input("Enter new total classes: ").strip()
        )

        attended_classes = int(
            input("Enter new attended classes: ").strip()
        )

    except ValueError:
        print("Classes must be whole numbers.")
        return

    if total_classes <= 0:
        print("Total classes must be greater than 0.")
        return

    if attended_classes < 0:
        print("Attended classes cannot be negative.")
        return

    if attended_classes > total_classes:
        print("Attended classes cannot be greater than total classes.")
        return

    query = """
        UPDATE attendance
        SET total_classes = %s,
            attended_classes = %s
        WHERE student_id = %s
        AND subject_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                total_classes,
                attended_classes,
                student_id,
                subject_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Attendance record not found.")
        else:
            print("Attendance updated successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not update attendance: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def delete_attendance(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    subject_id = get_subject_id()

    if subject_id is None:
        return

    confirmation = input(
        "Are you sure you want to delete this attendance? (y/n): "
    ).strip().lower()

    if confirmation != "y":
        print("Delete cancelled.")
        return

    query = """
        DELETE FROM attendance
        WHERE student_id = %s
        AND subject_id = %s
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            query,
            (
                student_id,
                subject_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            print("Attendance record not found.")
        else:
            print("Attendance deleted successfully.")

    except Error as error:
        connection.rollback()
        print(f"Could not delete attendance: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def view_result(connection):
    student_id = get_student_id()

    if student_id is None:
        return

    marks_query = """
        SELECT
            s.name,
            sub.subject_id,
            sub.subject_name,
            m.marks
        FROM marks m
        JOIN students s
            ON m.student_id = s.student_id
        JOIN subjects sub
            ON m.subject_id = sub.subject_id
        WHERE s.student_id = %s
        ORDER BY sub.subject_id
    """

    attendance_query = """
        SELECT
            sub.subject_id,
            sub.subject_name,
            a.total_classes,
            a.attended_classes,
            (a.attended_classes * 100.0 / a.total_classes)
        FROM attendance a
        JOIN subjects sub
            ON a.subject_id = sub.subject_id
        WHERE a.student_id = %s
        ORDER BY sub.subject_id
    """

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            marks_query,
            (student_id,)
        )

        marks_results = cursor.fetchall()

        if not marks_results:
            print("No marks found for this student.")
            return

        student_name = marks_results[0][0]

        total = sum(
            result[3]
            for result in marks_results
        )

        subject_count = len(marks_results)

        average = total / subject_count
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

        if all(
            result[3] >= 40
            for result in marks_results
        ):
            status = "PASS"
        else:
            status = "FAIL"

        cursor.execute(
            attendance_query,
            (student_id,)
        )

        attendance_results = cursor.fetchall()

        print("\n========== STUDENT RESULT ==========")
        print(f"Student ID : {student_id}")
        print(f"Name       : {student_name}")

        print("------------------------------------")
        print("MARKS")
        print("------------------------------------")

        for result in marks_results:
            print(
                f"{result[2]} : {result[3]}"
            )

        print("------------------------------------")
        print(f"Total      : {total}")
        print(f"Subjects   : {subject_count}")
        print(f"Average    : {average:.2f}")
        print(f"Percentage : {percentage:.2f}%")
        print(f"Grade      : {grade}")
        print(f"Status     : {status}")

        print("------------------------------------")
        print("ATTENDANCE")
        print("------------------------------------")

        if attendance_results:
            for result in attendance_results:
                print(
                    f"{result[1]} : "
                    f"{result[3]}/{result[2]} "
                    f"({result[4]:.2f}%)"
                )
        else:
            print("No attendance records found.")

        print("====================================")

    except Error as error:
        print(f"Could not calculate result: {error}")

    finally:
        if cursor is not None:
            cursor.close()


def show_menu():
    print("\n===== Student Result Management System =====")
    print("1. Add student")
    print("2. View all students")
    print("3. Search student by ID")
    print("4. Update student")
    print("5. Delete student")
    print("6. Add subject")
    print("7. View all subjects")
    print("8. Update subject")
    print("9. Delete subject")
    print("10. Add marks")
    print("11. View student marks")
    print("12. Update marks")
    print("13. Delete marks")
    print("14. Add attendance")
    print("15. View student attendance")
    print("16. Update attendance")
    print("17. Delete attendance")
    print("18. View result")
    print("19. Exit")


def main():
    connection = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if not connection.is_connected():
            print("Could not connect to MySQL.")
            return

        print("Connected to the student database.")

        while True:
            if admin_login(connection):
                break

            retry = input(
                "Do you want to try again? (y/n): "
            ).strip().lower()

            if retry != "y":
                print("Goodbye.")
                return

        while True:
            show_menu()

            choice = input(
                "Enter your choice (1-19): "
            ).strip()

            if choice == "1":
                add_student(connection)

            elif choice == "2":
                view_all_students(connection)

            elif choice == "3":
                search_student(connection)

            elif choice == "4":
                update_student(connection)

            elif choice == "5":
                delete_student(connection)

            elif choice == "6":
                add_subject(connection)

            elif choice == "7":
                view_all_subjects(connection)

            elif choice == "8":
                update_subject(connection)

            elif choice == "9":
                delete_subject(connection)

            elif choice == "10":
                add_marks(connection)

            elif choice == "11":
                view_student_marks(connection)

            elif choice == "12":
                update_marks(connection)

            elif choice == "13":
                delete_marks(connection)

            elif choice == "14":
                add_attendance(connection)

            elif choice == "15":
                view_student_attendance(connection)

            elif choice == "16":
                update_attendance(connection)

            elif choice == "17":
                delete_attendance(connection)

            elif choice == "18":
                view_result(connection)

            elif choice == "19":
                print("bye.")
                break

            else:
                print(
                    "Invalid choice. "
                    "Please enter a number from 1 to 19."
                )

    except Error as error:
        print(f"Database connection error: {error}")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()