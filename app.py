from flask import Flask, request, session, redirect, render_template
import traceback
import db

app = Flask(__name__)
app.secret_key = "secretkey"
db.create_db()

@app.route("/")
def index():
    user = session.get("user")
    balance = None
    if user:
        user_data = db.get_user(user)
        if user_data:
            balance = user_data["balance"]
    return render_template("index.html", user=user, balance=balance)

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
    data = db.get_user(username)
    
    if data:
        return render_template("profile.html", username=data["username"], balance=data["balance"])
    return "User not found", 404

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user" not in session:
        return "Login first", 401
        
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
    try:
        result = 1 / 0
    except Exception as e:
        return f"Server Error:{traceback.format_exc()}", 500

if __name__ == "__main__":
    app.run(debug=False)
