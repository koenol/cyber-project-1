from flask import Flask, request, session, redirect, render_template
import traceback
import db

app = Flask(__name__)
db.create_db()
# FLAW 1 - A07:2025 Authentication Failures
# Using a weak secret key for session management and storing it in public repository.
app.secret_key = "secretkey"
# FLAW 1 FIX:
# Generate a random secret key, and save/load it from environment variable instead
# import os
# app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

@app.route("/")
def index():
    user = session.get("user")
    balance = None
    if user:
        user_data = db.get_user(user)
        if user_data:
            balance = user_data["balance"]
    return render_template("index.html", user=user, balance=balance)

# FLAW 2 - A04:2025 Cryptographic Failures
# This flaw is heavily tied to A07:2025 Authentication Failures. This vulnerability allows attacker to brute-force password checks easily because passwords are not hashed and login attempts are not limited.
# see db.py:18

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = db.check_login(username, password)
        if user:
            session["user"] = username
            session["role"] = user["role"]
            return redirect("/")
        
        return "Invalid username or password."
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/profile/<username>")
def profile(username):
    if "user" not in session:
        return redirect("/login")
    # FLAW 3 - A01:2025 Broken Access Control
    # The flaw checks only whether is logged in, but does not verify that user has permission to view user profile.
    data = db.get_user(username)
    # FLAW 3 FIX:
    # Verify the user is same as the profile they are trying to view
    # if session.get("user") != username:
    #   return "Invalid permissions", 403
    if data:
        return render_template("profile.html", username=data["username"], balance=data["balance"])
    return "User not found", 404

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user" not in session:
        return "Login first", 401
    
    # FLAW 4 - Missing CSRF
    # Missing CSRF is not part of OWASP TOP 10 2025 list, but due to its fundamental nature it is allowed in the course project.
    # Current implemention is missing CSRF token generation and check completely, allowing attackers to create forged requests from other websites if the user has a session cookie saved from this website.
    # FLAW 4 FIX:
    # from flask_wtf.csrf import CSRFProtect, validate_csrf
    # csrf = CSRFProtect(app) - This would be normally done earlier in the app, but for the demo it is easier to do it here
    # validate_csrf(request.form.get("csrf_token"))
    # see transfer.html:7 for FRONTEND fix.
        
    if request.method == "GET":
        return render_template("transfer.html")
    try:
        amount = int(request.form.get("amount"))
    except (TypeError, ValueError):
        return "Invalid amount", 400
        
    user1 = request.form.get("to_user")
    user2 = session["user"]
    status, message = db.transfer(user2, user1, amount)
    
    if not status:
        return message, 400 if message == "Not enough funds." else 404
    return redirect("/")

@app.route("/error")
def error_route():
    # FLAW 5 - A10:2025 Mishanding Exceptional Conditions
    # This method is used to demonstrates how mishandled exceptional conditions can be used to gain information about the website.
    # traceback.format_exc() exposes website structure.
    try:
        result = 1 / 0
    except Exception as e:
        return f"Server Error:{traceback.format_exc()}", 500
    # FLAW 5 FIX:
    # One option is to return more generic message, e.g:
    # return f"Server Error: Try again later.", 500

@app.route("/fake-website/<username>")
def fake_website(username):
    session["user"] = username
    session["role"] = "admin"
    return redirect(f"/profile/{username}")

if __name__ == "__main__":
    app.run(debug=False)
