import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from pymongo import MongoClient
import os

# Global SocketIO instance
socketio = SocketIO()

# Global MongoDB instance (clean and simple)
mongo_client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
mongo_db = mongo_client["chat_db"]

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'

    # ✅ Store db directly on app object (best for small Flask apps)
    app.db = mongo_db

    # ✅ Register blueprints
    from .routes import main
    app.register_blueprint(main)

    # ✅ Init SocketIO
    socketio.init_app(app)

    # ✅ Register socket events
    from .socket_events import register_socket_events
    register_socket_events(socketio)

    return app
