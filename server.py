import socket
import threading
import os
import json


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

host = "::"  
port = 55555

server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)  
server.bind((host, port))
server.listen()

clients = []
nicknames = []

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except:
                if client in clients:
                    index = clients.index(client)
                    nickname = nicknames[index]
                    clients.remove(client)
                    nicknames.remove(nickname)
                    print(f"Disconnected: {nickname}")
                    client.close()

def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message.strip().upper() == "EXIT":
                index = clients.index(client)
                nickname = nicknames[index]
                broadcast(f"{nickname} has left the chat.".encode('ascii'))
                print(f"{nickname} has disconnected.")
                clients.remove(client)
                nicknames.remove(nickname)
                client.close()
                break
            else:
                broadcast(f"{nicknames[clients.index(client)]}: {message}".encode('ascii'), sender=client)
        except:
            if client in clients:
                index = clients.index(client)
                nickname = nicknames[index]
                broadcast(f"{nickname} has left the chat.".encode('ascii'))
                print(f"{nickname} has disconnected unexpectedly.")
                clients.remove(client)
                nicknames.remove(nickname)
                client.close()
                break

def authenticate(client):
    while True:
        client.send("LOGIN or REGISTER?".encode('ascii'))
        choice = client.recv(1024).decode('ascii').strip().upper()

        if choice == "REGISTER":
            client.send("Enter a new username:".encode('ascii'))
            username = client.recv(1024).decode('ascii').strip()

            if username in users:
                client.send("Username already exists. Try again.".encode('ascii'))
            else:
                client.send("Enter a new password:".encode('ascii'))
                password = client.recv(1024).decode('ascii').strip()
                users[username] = password
                save_users(users)
                client.send("Registration successful! Please login.".encode('ascii'))
                continue

        elif choice == "LOGIN":
            client.send("Enter your username:".encode('ascii'))
            username = client.recv(1024).decode('ascii').strip()

            if username not in users:
                client.send("Username not found. Try again.".encode('ascii'))
            else:
                client.send("Enter your password:".encode('ascii'))
                password = client.recv(1024).decode('ascii').strip()

                if users[username] == password:
                    client.send("Login successful!".encode('ascii'))
                    return username
                else:
                    client.send("Incorrect password. Try again.".encode('ascii'))
        else:
            client.send("Invalid choice. Please type LOGIN or REGISTER.".encode('ascii'))

def receive():
    print(f"Server is running and listening on [{host}]:{port}...")
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        nickname = authenticate(client)
        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname is {nickname}")
        broadcast(f"{nickname} joined the chat!".encode('ascii'))
        client.send('Connected to the server!'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

if __name__ == "__main__":
    try:
        receive()
    except KeyboardInterrupt:
        print("\nShutting down the server.")
        server.close()
