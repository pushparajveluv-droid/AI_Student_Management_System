from reportlab.platypus import SimpleDocTemplate, Table
from flask import send_file
from openpyxl import Workbook
from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "student_management_2026"

# Database Connection
db = mysql.connector.connect(
    host="hayabusa.proxy.rlwy.net",
    port=52517,
    user="root",
    password="SHsBDHNMNubqJGOcnMyaOAeEuSCtBQEe",
    database="railway"
)

cursor = db.cursor(dictionary=True)


@app.route("/")
def home():
    return redirect("/login")


# ---------------- USER REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        sql = """
        INSERT INTO users(fullname,email,phone,username,password)
        VALUES(%s,%s,%s,%s,%s)
        """

        values = (fullname, email, phone, username, password)

        cursor.execute(sql, values)
        db.commit()

        return redirect("/login")

    return render_template("user_register.html")


# ---------------- USER LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]

            return redirect("/dashboard")

        return "Invalid Username or Password"

    return render_template("user_login.html")
# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute(
        "SELECT COUNT(*) AS total FROM students WHERE user_id=%s",
        (session["user_id"],)
    )

    total = cursor.fetchone()["total"]

    return render_template(
        "dashboard.html",
        fullname=session["fullname"],
        total=total
    )


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
# ---------------- ADD STUDENT ---------------- #

@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        register_number = request.form["register_number"]
        name = request.form["name"]
        father_name = request.form["father_name"]
        mother_name = request.form["mother_name"]
        address = request.form["address"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        year = request.form["year"]
        gender = request.form["gender"]

        photo = request.files["photo"]
        photo_name = photo.filename

        if photo_name:
            photo.save("static/images/" + photo_name)

        cursor.execute("""
        INSERT INTO students
        (user_id, register_number, name, father_name, mother_name,
        address, email, phone, department, year, gender, photo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            register_number,
            name,
            father_name,
            mother_name,
            address,
            email,
            phone,
            department,
            year,
            gender,
            photo_name
        ))

        db.commit()

        return redirect("/students")

    return render_template("add_student.html")


# ---------------- STUDENTS ---------------- #

@app.route("/students")
def students():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search")

    if search:
        cursor.execute("""
        SELECT * FROM students
        WHERE user_id=%s
        AND (name LIKE %s OR register_number LIKE %s)
        ORDER BY id DESC
        """, (
            session["user_id"],
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("""
        SELECT * FROM students
        WHERE user_id=%s
        ORDER BY id DESC
        """, (session["user_id"],))

    students = cursor.fetchall()

    return render_template("students.html", students=students
    )
@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        cursor.execute("""
        UPDATE students
        SET register_number=%s,
            name=%s,
            department=%s,
            year=%s,
            email=%s,
            phone=%s
        WHERE id=%s AND user_id=%s
        """, (
            request.form["register_number"],
            request.form["name"],
            request.form["department"],
            request.form["year"],
            request.form["email"],
            request.form["phone"],
            id,
            session["user_id"]
        ))

        db.commit()

        return redirect("/students")

    cursor.execute(
        "SELECT * FROM students WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    student = cursor.fetchone()

    return render_template("edit_student.html", student=student
    )
@app.route("/delete_student/<int:id>")
def delete_student(id):

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute(
        "DELETE FROM students WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    db.commit()

    return redirect("/students")
@app.route("/export_excel")
def export_excel():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute("""
    SELECT register_number, name, father_name, mother_name,
           department, year, email, phone, gender
    FROM students
    WHERE user_id=%s
    """, (session["user_id"],))

    students = cursor.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Students"

    ws.append([
        "Register No",
        "Name",
        "Father Name",
        "Mother Name",
        "Department",
        "Year",
        "Email",
        "Phone",
        "Gender"
    ])

    for s in students:
        ws.append([
            s["register_number"],
            s["name"],
            s["father_name"],
            s["mother_name"],
            s["department"],
            s["year"],
            s["email"],
            s["phone"],
            s["gender"]
        ])

    filename = "students.xlsx"
    wb.save(filename)

    return send_file(filename, as_attachment=True)
@app.route("/export_pdf")
def export_pdf():

    if "user_id" not in session:
        return redirect("/login")

    cursor.execute("""
    SELECT register_number, name, department, year, email, phone
    FROM students
    WHERE user_id=%s
    """, (session["user_id"],))

    students = cursor.fetchall()

    data = [["Register No", "Name", "Department", "Year", "Email", "Phone"]]

    for s in students:
        data.append([
            s["register_number"],
            s["name"],
            s["department"],
            s["year"],
            s["email"],
            s["phone"]
        ])

    pdf = SimpleDocTemplate("students.pdf")
    table = Table(data)
    pdf.build([table])

    return send_file(
        "students.pdf",
        as_attachment=True,
        download_name="students.pdf"
    )
if __name__ == "__main__":
    app.run(debug=True)