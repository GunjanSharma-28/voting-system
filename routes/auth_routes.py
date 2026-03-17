from flask import Blueprint, render_template, request, redirect, session
from database.db import get_db_connection
from werkzeug.security import check_password_hash

# ---------------- ADMIN LOGIN ---------------- #

admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admin')

@admin_auth_bp.route("/login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM admins WHERE username=%s",(username,))
        admin = cur.fetchone()

        if admin and admin["password"] == password:
            session["admin"] = True
            return redirect("/admin/dashboard")

        return "Invalid admin login"

    return render_template("auth/admin_login.html")


# ---------------- VOTER LOGIN ---------------- #

voter_auth_bp =  Blueprint('voter_auth', __name__, url_prefix='/voter')
@voter_auth_bp.route("/login", methods=["GET","POST"])
def voter_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM voters WHERE username=%s",(username,))
        voter = cur.fetchone()

        if voter and check_password_hash(voter["password"], password):
            session["voter_id"] = voter["voter_id"]
            return redirect("/voter/dashboard")

        return "Invalid voter login"

    return render_template("auth/voter_login.html")


@voter_auth_bp.route('/logout')
def voter_logout():
    session.pop("voter_id", None)
    return redirect("/voter/login")
