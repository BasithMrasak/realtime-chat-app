import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from pymongo import MongoClient
import os

# ✅ Global SocketIO instance
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'

    # ✅ MongoDB connection using MONGO_URI from environment
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    app.db = client["chat_db"]
    
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['mongo_db'] = mongo_db

    # ✅ Register Flask blueprint
    from .routes import main
    app.register_blueprint(main)

    # ✅ Attach SocketIO to app
    socketio.init_app(app)

    # ✅ Register socket event handlers
    from .socket_events import register_socket_events
    register_socket_events(socketio)

    return app
