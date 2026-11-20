from . import bp
from app.extensions import socketio


@bp.route("/history")
def history():
    return "Chat history"


@socketio.on("message")
def handle_message(data):
    socketio.emit("message", data)
