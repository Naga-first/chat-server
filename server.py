import asyncio
import websockets
import json
import os

USER_CREDENTIALS_FILE = "users.json"

# Load and save users
def load_users():
    if os.path.exists(USER_CREDENTIALS_FILE):
        with open(USER_CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_CREDENTIALS_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()
connected_clients = {}

async def broadcast(message, sender=None):
    disconnected_clients = []
    for client, username in connected_clients.items():
        if client != sender:
            try:
                await client.send(message)
            except:
                disconnected_clients.append(client)

    for client in disconnected_clients:
        del connected_clients[client]

async def handle_client(websocket, path):
    try:
        await websocket.send("LOGIN or REGISTER?")
        choice = await websocket.recv()

        if choice.upper() == "REGISTER":
            await websocket.send("Enter a new username:")
            username = await websocket.recv()

            if username in users:
                await websocket.send("Username already exists. Try again.")
                return
            else:
                await websocket.send("Enter a new password:")
                password = await websocket.recv()
                users[username] = password
                save_users(users)
                await websocket.send("Registration successful! Please login.")
                return

        elif choice.upper() == "LOGIN":
            await websocket.send("Enter your username:")
            username = await websocket.recv()

            if username not in users:
                await websocket.send("Username not found. Try again.")
                return

            await websocket.send("Enter your password:")
            password = await websocket.recv()

            if users[username] != password:
                await websocket.send("Incorrect password. Try again.")
                return

            await websocket.send("Login successful!")
            connected_clients[websocket] = username
            await broadcast(f"{username} joined the chat!", sender=websocket)

            # Handle messages
            async for message in websocket:
                if message.strip().upper() == "EXIT":
                    await broadcast(f"{username} has left the chat.")
                    del connected_clients[websocket]
                    break
                else:
                    await broadcast(f"{username}: {message}")

    except websockets.exceptions.ConnectionClosed:
        if websocket in connected_clients:
            username = connected_clients[websocket]
            del connected_clients[websocket]
            await broadcast(f"{username} has left the chat.")

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 55555)
    print("WebSocket server started on ws://0.0.0.0:55555")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
