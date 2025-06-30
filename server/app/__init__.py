import eventlet
eventlet.monkey_patch()
from flask import Flask
from flask_socketio import SocketIO
from pymongo import MongoClient
import os

client = MongoClient(os.environ["MONGO_URI"])
db = client["chat_db"]


# ✅ Create the SocketIO instance at the top
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'

    # ✅ MongoDB connection
    client = MongoClient("mongodb://localhost:27017/")
    app.db = client["chat_db"]

    # ✅ Register Blueprint
    from .routes import main
    app.register_blueprint(main)

    # ✅ Attach SocketIO to app
    socketio.init_app(app)

    # ✅ Register socket event handlers
    from .socket_events import register_socket_events
    register_socket_events(socketio)

    return app
