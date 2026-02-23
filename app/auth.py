"""
Authentication blueprint.

Handles user login, logout and session management
using Flask-Login.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models import User

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user authentication.
    
    Validates login credentials and creates a user session.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.index"))

        flash("Login fehlgeschlagen (E-Mail oder Passwort falsch).")
    return render_template("login.html")

@auth.route("/logout")
@login_required
def logout():
    """
    Logs out the current user and ends the session.
    """
    logout_user()
    return redirect(url_for("auth.login"))
