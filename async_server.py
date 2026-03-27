import asyncio
import ssl
import time

rooms = {}
clients = {}
last_seen = {}
TIMEOUT = 30

class Room:
    def __init__(self):
        self.clients = []
        self.seq = 0

async def handle_client(reader, writer):
    writer.write(b"Enter username: ")
    await writer.drain()
    username = (await reader.readline()).decode().strip()
    clients[username] = writer
    last_seen[writer] = time.time()

    writer.write(b"Enter room: ")
    await writer.drain()
    room_name = (await reader.readline()).decode().strip()

    if room_name not in rooms:
        rooms[room_name] = Room()

    room = rooms[room_name]
    room.clients.append(writer)

    await broadcast(room, f"{username} joined the room", writer)

    try:
        while True:
            data = await asyncio.wait_for(reader.readline(), timeout=TIMEOUT)
            if not data:
                break

            last_seen[writer] = time.time()
            msg = data.decode().strip()

            # HEARTBEAT
            if msg == "/ping":
                writer.write(b"/pong\n")
                await writer.drain()
                continue

            # LEAVE ROOM
            if msg == "/leave":
                if writer in room.clients:
                    room.clients.remove(writer)
                await broadcast(room, f"{username} left the room", writer)
                writer.write(b"You left the room\n")
                await writer.drain()
                room = None
                continue

            # JOIN ROOM
            if msg.startswith("/join"):
                parts = msg.split(" ", 1)
                if len(parts) == 2:
                    new_room = parts[1]

                    if room and writer in room.clients:
                        room.clients.remove(writer)
                        await broadcast(room, f"{username} left the room", writer)

                    if new_room not in rooms:
                        rooms[new_room] = Room()

                    room = rooms[new_room]
                    room.clients.append(writer)

                    writer.write(f"Joined {new_room}\n".encode())
                    await writer.drain()

                    await broadcast(room, f"{username} joined the room", writer)
                continue

            # PRIVATE MESSAGE
            if msg.startswith("/msg"):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    _, target, text = parts
                    if target in clients:
                        clients[target].write(f"[PRIVATE] {username}: {text}\n".encode())
                        await clients[target].drain()
                    else:
                        writer.write(f"User {target} not found\n".encode())
                        await writer.drain()
                continue

            # FILE
            if msg.startswith("/file"):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    _, fname, content = parts
                    await broadcast(room, f"[FILE] {username}: {fname} -> {content}", writer)
                continue

            # NORMAL MESSAGE
            if room:
                await broadcast(room, f"{username}: {msg}", writer)

    except asyncio.TimeoutError:
        print(f"[TIMEOUT] {username} disconnected")

    finally:
        if room and writer in room.clients:
            room.clients.remove(writer)
            await broadcast(room, f"{username} left the room", writer)

        if username in clients:
            del clients[username]
        if writer in last_seen:
            del last_seen[writer]

        writer.close()
        await writer.wait_closed()

async def broadcast(room, message, sender):
    start = time.time()
    room.seq += 1
    msg = f"[{room.seq}] {message}\n"
    for client in room.clients:
        try:
            client.write(msg.encode())
            await client.drain()
        except:
            pass
    end = time.time()
    print(f"[PERF] {end-start:.6f}s | clients={len(room.clients)}")

async def main():
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("cert.pem", "key.pem")

    server = await asyncio.start_server(
        handle_client, "127.0.0.1", 5001, ssl=ssl_context
    )

    print("Secure Server with FULL features running on 127.0.0.1:5001")

    async with server:
        await server.serve_forever()

asyncio.run(main())
