from flask import Blueprint, render_template, request, redirect, session
from database.db import get_db_connection
from datetime import datetime

voter_bp = Blueprint('voter', __name__, url_prefix='/voter')


# =========================
# VOTER DASHBOARD
# =========================
@voter_bp.route("/dashboard")
def dashboard():

    if not session.get("voter_id"):
        return redirect("/voter/login")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    # Get election settings
    cur.execute("SELECT * FROM election LIMIT 1")
    settings = cur.fetchone()

    now = datetime.now()
    election_active = False

    if settings:
        if settings["start_date"] <= now <= settings["end_date"]:
            election_active = True

    # Get candidates
    cur.execute("SELECT * FROM candidates")
    candidates = cur.fetchall()

    # Check if voter already voted
    cur.execute(
        "SELECT has_voted FROM voters WHERE voter_id=%s",
        (session["voter_id"],)
    )

    voter = cur.fetchone()
    has_voted = voter["has_voted"] if voter else False

    cur.close()
    db.close()

    return render_template(
        "voter/dashboard.html",
        candidates=candidates,
        election_active=election_active,
        has_voted=has_voted,
        settings=settings
    )


# =========================
# CAST VOTE
# =========================
@voter_bp.route("/vote", methods=["POST"])
def vote():

    if not session.get("voter_id"):
        return redirect("/voter/login")

    candidate_id = request.form.get("candidate_id")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    # Check election active
    cur.execute("SELECT * FROM election LIMIT 1")
    settings = cur.fetchone()

    now = datetime.now()

    if not settings or not (settings["start_date"] <= now <= settings["end_date"]):
        return "Election is not active."

    # Check if voter already voted
    cur.execute(
        "SELECT has_voted FROM voters WHERE voter_id=%s",
        (session["voter_id"],)
    )

    voter = cur.fetchone()

    if voter["has_voted"]:
        return "You have already voted."

    # Validate candidate
    cur.execute(
        "SELECT * FROM candidates WHERE candidate_id=%s",
        (candidate_id,)
    )

    candidate = cur.fetchone()

    if not candidate:
        return "Invalid candidate selected."

    # Insert vote
    cur.execute(
        "INSERT INTO votes (voter_id, candidate_id) VALUES (%s,%s)",
        (session["voter_id"], candidate_id)
    )

    # Mark voter as voted
    cur.execute(
        "UPDATE voters SET has_voted=TRUE WHERE voter_id=%s",
        (session["voter_id"],)
    )

    db.commit()

    cur.close()
    db.close()

    return redirect("/voter/dashboard")


# =========================
# LOGOUT
# =========================
@voter_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")