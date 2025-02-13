import asyncio
import websockets
import os
import json

USER_CREDENTIALS_FILE = "users.json"

# Load and save user credentials
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
    for client, nickname in connected_clients.items():
        if client != sender:
            try:
                await client.send(message)
            except:
                disconnected_clients.append(client)
    for client in disconnected_clients:
        del connected_clients[client]

async def authenticate(websocket):
    while True:
        await websocket.send("LOGIN or REGISTER?")
        choice = await websocket.recv()
        choice = choice.strip().upper()

        if choice == "REGISTER":
            await websocket.send("Enter a new username:")
            username = await websocket.recv()
            username = username.strip()

            if username in users:
                await websocket.send("Username already exists. Try again.")
            else:
                await websocket.send("Enter a new password:")
                password = await websocket.recv()
                users[username] = password
                save_users(users)
                await websocket.send("Registration successful! Please login.")
                continue

        elif choice == "LOGIN":
            await websocket.send("Enter your username:")
            username = await websocket.recv()
            username = username.strip()

            if username not in users:
                await websocket.send("Username not found. Try again.")
            else:
                await websocket.send("Enter your password:")
                password = await websocket.recv()

                if users[username] == password:
                    await websocket.send("Login successful!")
                    return username
                else:
                    await websocket.send("Incorrect password. Try again.")
        else:
            await websocket.send("Invalid choice. Please type LOGIN or REGISTER.")

async def handle_client(websocket, path):
    nickname = await authenticate(websocket)
    connected_clients[websocket] = nickname

    await broadcast(f"{nickname} joined the chat!", sender=websocket)
    await websocket.send("Connected to the server!")

    try:
        async for message in websocket:
            if message.strip().upper() == "EXIT":
                await broadcast(f"{nickname} has left the chat.")
                break
            else:
                await broadcast(f"{nickname}: {message}", sender=websocket)
    except:
        pass
    finally:
        del connected_clients[websocket]
        await broadcast(f"{nickname} has left the chat.")

async def main():
    host = "0.0.0.0"
    port = 55555
    async with websockets.serve(handle_client, host, port):
        print(f"WebSocket server started on ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down the server.")
