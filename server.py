from flask import Flask, request
from flask_socketio import SocketIO, send, emit
import json
import os
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

USER_CREDENTIALS_FILE = "users.json"

def load_users():
    if os.path.exists(USER_CREDENTIALS_FILE):
        with open(USER_CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_CREDENTIALS_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()
clients = {}

@app.route('/')
def index():
    return "Chat Server is Running!"

@socketio.on('connect')
def handle_connect():
    print("A user connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("A user disconnected")
    for nickname, sid in list(clients.items()):
        if sid == request.sid:
            del clients[nickname]
            socketio.emit('message', f"{nickname} has left the chat.")
            break

@socketio.on('register')
def handle_register(data):
    username = data.get('username')
    password = data.get('password')
    if username in users:
        emit('register_response', {'status': 'error', 'message': 'Username already exists'})
    else:
        users[username] = password
        save_users(users)
        emit('register_response', {'status': 'success', 'message': 'Registration successful'})

@socketio.on('login')
def handle_login(data):
    username = data.get('username')
    password = data.get('password')
    if username not in users or users[username] != password:
        emit('login_response', {'status': 'error', 'message': 'Invalid username or password'})
    else:
        clients[username] = request.sid
        emit('login_response', {'status': 'success', 'message': 'Login successful'})
        socketio.emit('message', f"{username} has joined the chat.")

@socketio.on('message')
def handle_message(data):
    username = data.get('username')
    message = data.get('message')
    print(f"{username}: {message}")
    socketio.emit('message', f"{username}: {message}")

def run_socket_server():
    print("Starting chat server...")
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)), allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    threading.Thread(target=run_socket_server, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
