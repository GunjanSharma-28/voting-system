from flask import Blueprint, render_template, request, redirect, session
from database.db import get_db_connection
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

UPLOAD_FOLDER = os.path.join("static", "images", "symbols")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ================================
# ADMIN DASHBOARD
# ================================
@admin_bp.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM admins")
    admins = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM voters")
    voters = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM candidates")
    candidates = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM votes")
    votes = cur.fetchone()["total"]

    # get active election
    cur.execute("SELECT * FROM election WHERE is_active=1 LIMIT 1")
    election = cur.fetchone()

    cur.close()
    db.close()

    return render_template(
        "admin/dashboard.html",
        admins=admins,
        voters=voters,
        candidates=candidates,
        votes=votes,
        election=election
    )


# ================================
# ADD VOTER
# ================================
@admin_bp.route("/add_voter", methods=["POST"])
def add_voter():

    if "admin" not in session:
        return redirect("/admin/login")

    name = request.form["name"]
    username = request.form["username"]
    password = generate_password_hash(request.form["password"])

    db = get_db_connection()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO voters (name, username, password) VALUES (%s,%s,%s)",
        (name, username, password)
    )

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")


# ================================
# ADD CANDIDATE
# ================================
@admin_bp.route("/add_candidate", methods=["POST"])
def add_candidate():

    if "admin" not in session:
        return redirect("/admin/login")

    name = request.form["name"]
    party = request.form["party"]
    symbol_file = request.files["symbol"]

    filename = secure_filename(symbol_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    symbol_file.save(file_path)

    db = get_db_connection()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO candidates (name, party, symbol) VALUES (%s,%s,%s)",
        (name, party, filename)
    )

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")


# ================================
# SET / UPDATE ELECTION
# ================================
@admin_bp.route("/set_election", methods=["POST"])
def set_election():

    if "admin" not in session:
        return redirect("/admin/login")

    start_date = request.form["start_date"]
    end_date = request.form["end_date"]

    db = get_db_connection()
    cur = db.cursor()

    # remove previous election
    cur.execute("DELETE FROM election")

    cur.execute(
        "INSERT INTO election (title,start_date,end_date,is_active) VALUES (%s,%s,%s,1)",
        ("Student Election", start_date, end_date)
    )

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")


# ================================
# VIEW VOTERS
# ================================
@admin_bp.route("/voters")
def view_voters():

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM voters")
    voters = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/voters.html", voters=voters)


# ================================
# DELETE VOTER
# ================================
@admin_bp.route("/delete_voter/<int:voter_id>")
def delete_voter(voter_id):

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("DELETE FROM votes WHERE voter_id=%s", (voter_id,))
    cur.execute("DELETE FROM voters WHERE voter_id=%s", (voter_id,))

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/voters")


# ================================
# VIEW CANDIDATES
# ================================
@admin_bp.route("/candidates")
def view_candidates():

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM candidates")
    candidates = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/candidates.html", candidates=candidates)


# ================================
# DELETE CANDIDATE
# ================================
@admin_bp.route("/delete_candidate/<int:candidate_id>")
def delete_candidate(candidate_id):

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("DELETE FROM votes WHERE candidate_id=%s", (candidate_id,))
    cur.execute("DELETE FROM candidates WHERE candidate_id=%s", (candidate_id,))

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/candidates")


# ================================
# RESET ELECTION
# ================================
@admin_bp.route("/reset_election", methods=["POST"])
def reset_election():

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("DELETE FROM votes")
    cur.execute("UPDATE voters SET has_voted = FALSE")

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")


# ================================
# DELETE ALL VOTERS
# ================================
@admin_bp.route("/delete_all_voters", methods=["POST"])
def delete_all_voters():

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("DELETE FROM votes")
    cur.execute("DELETE FROM voters")

    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")


# ================================
# RESULTS
# ================================
@admin_bp.route("/results")
def results():

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM election LIMIT 1")
    election = cur.fetchone()

    if not election:
        return "Election not configured."

    now = datetime.now()

    if now < election["end_date"]:
        remaining = election["end_date"] - now

        return render_template(
            "admin/results_locked.html",
            end_date=election["end_date"],
            remaining=remaining
        )

    cur.execute("""
        SELECT c.name, c.party, c.symbol, COUNT(v.id) AS total_votes
        FROM candidates c
        LEFT JOIN votes v ON c.candidate_id = v.candidate_id
        GROUP BY c.candidate_id
        ORDER BY total_votes DESC
    """)

    results = cur.fetchall()

    winner = None
    tie = False

    if results:
        max_votes = results[0]["total_votes"]
        top = [r for r in results if r["total_votes"] == max_votes]

        if len(top) == 1:
            winner = top[0]
        else:
            tie = True

    cur.close()
    db.close()

    return render_template(
        "admin/results.html",
        results=results,
        winner=winner,
        tie=tie
    )


# ================================
# LOGOUT
# ================================
@admin_bp.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/")