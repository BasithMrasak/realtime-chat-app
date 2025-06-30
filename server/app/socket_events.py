from flask_socketio import join_room, emit, send
from datetime import datetime
from flask import current_app, request
from collections import defaultdict

# Store mapping of username -> sid (for private messages)
user_sid_map = defaultdict(str)

def register_socket_events(socketio):
    @socketio.on("connect")
    def handle_connect():
        username = request.args.get("username")
        if username:
            user_sid_map[username] = request.sid
            print(f"{username} connected with SID {request.sid}")

             # Send only groups user is part of
            db = current_app.db
            groups = db["groups"].find({"members": username})
            group_names = [g["name"] for g in groups]
            emit("group_list_update", group_names, to=request.sid)

    @socketio.on("disconnect")
    def handle_disconnect():
        # Remove user from mapping when disconnected
        for user, sid in list(user_sid_map.items()):
            if sid == request.sid:
                del user_sid_map[user]
                print(f"{user} disconnected")
                break
    @socketio.on("join_room")
    def handle_join(data):
        room = data.get("room")
        username = data.get("username")
        join_room(room)
        print(f"✅ {username} joined room: {room}")
    @socketio.on("get_users")
    def handle_get_users(data):
        current_user = data.get("current_user")
        db = current_app.db
        users = db["users"].find({"username": {"$ne": current_user}})
        usernames = [user["username"] for user in users]
        emit("user_list", usernames)


    @socketio.on("send_message")
    def handle_private_message(data):
        from_user = data.get("from_user")
        to_user = data.get("to_user")
        message = data.get("message")
        timestamp = datetime.utcnow().isoformat()

        db = current_app.db
        db["messages"].insert_one({
            "from_user": from_user,
            "to_user": to_user,
            "message": message,
            "timestamp": timestamp
        })

        # Emit to sender
        emit("receive_message", {
            "from_user": from_user,
            "to_user": to_user,
            "message": message,
            "timestamp": timestamp
        }, to=request.sid)

        # Emit to recipient if they are connected
        to_sid = user_sid_map.get(to_user)
        if to_sid:
            emit("receive_message", {
                "from_user": from_user,
                "to_user": to_user,
                "message": message,
                "timestamp": timestamp
            }, to=to_sid)
    @socketio.on("create_or_join_group")
    def handle_create_or_join_group(data):
        group_name = data.get("group")
        username = data.get("username")

        db = current_app.db
        groups_collection = db["groups"]

        # Check if group exists
        group = groups_collection.find_one({"name": group_name})
        
        if group:
            # Add user to group if not already a member
            if username not in group.get("members", []):
                groups_collection.update_one(
                    {"name": group_name},
                    {"$addToSet": {"members": username}}
                )
        else:
            # Create new group
            groups_collection.insert_one({
                "name": group_name,
                "created_by": username,
                "members": [username]
            })

        # Join the Socket.IO room
        group_name= data.get("group")
        join_room(group_name)
        print(f"{username} joined group: {group_name}")
        print(socketio.server.manager.rooms)
        

        # Send updated group list to all users
        all_groups = groups_collection.find()
        group_names = [g["name"] for g in all_groups]
        emit("group_list_update", group_names, broadcast=True)
    @socketio.on("send_group_message")
    def handle_group_message(data):
        room = data.get("room")
        message = data.get("message")
        sender = data.get("sender")
        timestamp = datetime.utcnow().isoformat()

        db = current_app.db
        db["group_messages"].insert_one({
            "room": room,
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        })

        emit("receive_group_message", {
            "room": room,
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        }, to=room)


