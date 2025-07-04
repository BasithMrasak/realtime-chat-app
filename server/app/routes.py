from flask import Blueprint, render_template, request, redirect, url_for, current_app
from bson.objectid import ObjectId
from flask import session
from flask import current_app



main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = current_app.db        
        user = db["users"].find_one({"username": username, "password": password})

        if user:
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            return redirect(url_for('main.chat'))

        return "Invalid username or password.", 401

    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))



@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        display_name = request.form.get('display_name')
        password = request.form.get('password')

        db = current_app.db        
        users_collection = db["users"]

        # Check if username already exists
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return "Username already taken. Try another.", 409

        # Insert user into DB
        users_collection.insert_one({
            "username": username,
            "display_name": display_name,
            "password": password,  # No encryption as per earlier decision
            "status": "Offline",
            "profile_picture": "",
        })

        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    return render_template('chat.html', username=session['username'], display_name=session.get('display_name'))


@main.route('/chat-data')
def chat_data():
    db = current_app.db    
    messages = db["messages"].find().sort("timestamp", 1)

    chat_data = []
    for msg in messages:
        chat_data.append({
            "sender": msg.get("sender", ""),
            "message": msg.get("message", ""),
            "timestamp": msg.get("timestamp", "")
        })
    return chat_data

@main.route('/chat-history/<with_user>')
def chat_history(with_user):
    if 'username' not in session:
        return [], 401

    current_user = session['username']
    db = current_app.db    
    messages = db["messages"].find({
        "$or": [
            {"from_user": current_user, "to_user": with_user},
            {"from_user": with_user, "to_user": current_user}
        ]
    }).sort("timestamp", 1)

    return [{
        "from_user": msg["from_user"],
        "to_user": msg["to_user"],
        "message": msg["message"],
        "timestamp": msg["timestamp"]
    } for msg in messages]

@main.route('/room-history/<room_name>')
def room_history(room_name):
    db = current_app.db
    messages = db["group_messages"].find({"room": room_name}).sort("timestamp", 1)

    return [{
        "sender": msg["sender"],
        "message": msg["message"],
        "timestamp": msg["timestamp"],
        "room": msg["room"]
    } for msg in messages]

from flask import flash  # ✅ import this

@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    db = current_app.db
    users = db["users"]
    current_user = users.find_one({"username": session["username"]})

    if request.method == "POST":
        new_display_name = request.form.get("display_name")
        new_password = request.form.get("password")

        updates = {}
        if new_display_name and new_display_name != current_user["display_name"]:
            updates["display_name"] = new_display_name
            session["display_name"] = new_display_name

        if new_password:
            updates["password"] = new_password

        if updates:
            users.update_one({"username": session["username"]}, {"$set": updates})
            flash("✅ Profile updated successfully!")  # ✅ Flash message

    user = users.find_one({"username": session["username"]})
    return render_template("profile.html", user=user)
