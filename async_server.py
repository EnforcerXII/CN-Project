import asyncio  #allows handling multiple clients at once(async server)
import ssl      #add encryption (secure communic)
import time     #used for :performance measurement,timeout tracking
#asynchronous function allows multiple tasks to be handled at same time is a function that can run without blocking others
rooms = {} #stores chat rooms
clients = {}  #username->connection(writer)mapping
last_seen = {}  #tracks last activity of each client,used for failure detection
TIMEOUT = 300  # if no message for 300s disconnect

class Room:
    def __init__(self):
        self.clients = []  #clients-->list ofusers in room
        self.seq = 0       #seq-->message ordering counter

async def handle_client(reader, writer):  #runs seperately for each client
    writer.write(b"Enter username: ")  #sends prompt to client
    await writer.drain()  #drain()--ensures it is sent immediately 
    username = (await reader.readline()).decode().strip() #decode convert bytes to string,strip removes whitespace
    clients[username] = writer  #stores user for private messaging
    last_seen[writer] = time.time() #stores current time->used for timeout

    writer.write(b"Enter room: ")
    await writer.drain()
    room_name = (await reader.readline()).decode().strip()

    if room_name not in rooms:
        rooms[room_name] = Room() #create room if it doesnt exist

    room = rooms[room_name]
    room.clients.append(writer)  #add client to room

    await broadcast(room, f"{username} joined the room", writer) #normal message
    #notify others
    try:
        while True: #keeps running until client disconnects
            data = await asyncio.wait_for(reader.readline(), timeout=TIMEOUT)
            #waits for msg
            # if no msg for 30 sec ->timeout error
            if not data:
                break

            last_seen[writer] = time.time()#upadate activity time
            msg = data.decode().strip()#convert message to string

            # HEARTBEAT
            if msg == "/ping":  #client sends ping
                writer.write(b"/pong\n")
                await writer.drain()  #server replies
                continue

            # LEAVE ROOM
            if msg == "/leave":
                if writer in room.clients:
                    room.clients.remove(writer) #remove user
                await broadcast(room, f"{username} left the room", writer)#notify others
                writer.write(b"You left the room\n")#notify user
                await writer.drain()
                room = None #user not in room now
                continue

            # JOIN ROOM
            if msg.startswith("/join"):
                parts = msg.split(" ", 1) #extract room name
                if len(parts) == 2:
                    new_room = parts[1]

                    if room and writer in room.clients:
                        room.clients.remove(writer) #leave old room
                        await broadcast(room, f"{username} left the room", writer)

                    if new_room not in rooms:
                        rooms[new_room] = Room()

                    room = rooms[new_room]
                    room.clients.append(writer) #join new room

                    writer.write(f"Joined {new_room}\n".encode()) #confirm user
                    await writer.drain()

                    await broadcast(room, f"{username} joined the room", writer)
                continue

            # PRIVATE MESSAGE
            if msg.startswith("/msg"):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    _, target, text = parts #extract target user,message
                    if target in clients:
                        clients[target].write(f"[PRIVATE] {username}: {text}\n".encode())
                        await clients[target].drain()
                    else:
                        writer.write(f"User {target} not found\n".encode())
                        await writer.drain()
                continue
           # FILE
            if msg.startswith("/file"):
                parts = msg.split(" ", 1)
                if len(parts) == 2:
                    fname = parts[1]

                    writer.write(b"READY\n")
                    await writer.drain()

                    # receive file size
                    size_data = await reader.readuntil(b"\n")
                    filesize = int(size_data.decode().strip())

                    # receive file bytes (FIXED)
                    remaining = filesize
                    file_data = b""

                    while remaining > 0:
                        chunk = await reader.read(min(1024, remaining))
                        if not chunk:
                            break
                        file_data += chunk
                        remaining -= len(chunk)

                    # save file
                    with open(f"server_{fname}", "wb") as f:
                        f.write(file_data)

                    # send file to other clients
                    for client in room.clients:
                        if client != writer:
                            try:
                                client.write(f"[FILE] {username}: {fname}\n".encode())
                                client.write(f"{filesize}\n".encode())
                                client.write(file_data)
                                await client.drain()
                            except:
                                pass

                    print(f"[FILE RECEIVED] {fname} from {username}")
                continue

            # NORMAL MESSAGE
            if room:
                await broadcast(room, f"{username}: {msg}", writer)

    except asyncio.TimeoutError:
        #triggered when inactive
        print(f"[TIMEOUT] {username} disconnected")

    finally:
        if room and writer in room.clients:
            room.clients.remove(writer) #remove user
            await broadcast(room, f"{username} left the room", writer)

        if username in clients:
            del clients[username]  #clean memory
        if writer in last_seen:
            del last_seen[writer]

        writer.close()
        await writer.wait_closed() #close connection

async def broadcast(room, message, sender):
    start = time.time()
    room.seq += 1
    msg = f"[{room.seq}] {message}\n" #add ordering
    for client in room.clients:
        try:
            client.write(msg.encode()) #send message
            await client.drain()
        except:
            pass
    end = time.time()
    print(f"[PERF] {end-start:.6f}s | clients={len(room.clients)}")
    #logs performance
async def main():
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    #creates secure context
    ssl_context.load_cert_chain("cert.pem", "key.pem")
    #loads certificate
    server = await asyncio.start_server(
        handle_client, "127.0.0.1", 5001, ssl=ssl_context
    ) #start server

    print("Secure Server with FULL features running on 127.0.0.1:5001")

    async with server:
        await server.serve_forever()
    #runs forever
asyncio.run(main())
