import socket # used for network communication(TCP)
import threading #allows running multiple tasks
import ssl #enables secure encrypted connection
import time #used for heartbeat timing

HOST = "127.0.0.1" #server ip
PORT = 5001        #server port

ready_event = threading.Event() #signals main thread when server sends READY

def receive(sock): #runs in a sep thread
    #continuously recieves messages frm server
    buffer = b""
    while True:
        try:
            chunk = sock.recv(1024) #recieves data max--1024 bytes
            if not chunk:
                break  #if server disconnects -->stop loop
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line_str = line.decode()
                if line_str == "READY":
                    ready_event.set() #signal main thread to start sending file
                elif line_str.startswith("[FILE]"):
                    #extract filename from "[FILE] username: fname"
                    fname = line_str.split(": ", 1)[1] if ": " in line_str else "received_file"
                    print(line_str)
                    #read file size line
                    while b"\n" not in buffer:
                        chunk = sock.recv(1024)
                        if not chunk:
                            break
                        buffer += chunk
                    size_line, buffer = buffer.split(b"\n", 1)
                    filesize = int(size_line.decode().strip())
                    #read exactly filesize bytes
                    while len(buffer) < filesize:
                        chunk = sock.recv(1024)
                        if not chunk:
                            break
                        buffer += chunk
                    file_data = buffer[:filesize]
                    buffer = buffer[filesize:]
                    with open(f"received_{fname}", "wb") as f:
                        f.write(file_data)
                    print(f"[FILE SAVED] received_{fname} ({filesize} bytes)")
                else:
                    print(line_str) #bytes-->string
        except:
            break

def heartbeat(sock): #keeps connection alive
    while True:
        try:
            sock.sendall(b"/ping\n") #sends /ping message to server
            time.sleep(60) #waits 60 sec
        except:
            break #if connection fails -->stop heartbeat

def main():
    context = ssl.create_default_context() #creates SSL configuration
    context.check_hostname = False #skip hostname checking
    context.verify_mode = ssl.CERT_NONE #accepts self signed certificate

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET: IPv4, SOCK_STREAM: TCP
    sock = context.wrap_socket(s, server_hostname="localhost")
    #wraps socket with ssl
    #makes communication encrypted
    sock.connect((HOST, PORT))

    print(sock.recv(1024).decode(), end="")
    username = input()
    sock.sendall((username + "\n").encode())#sends username to all

    print(sock.recv(1024).decode(), end="")
    room = input()
    sock.sendall((room + "\n").encode())

    threading.Thread(target=receive, args=(sock,), daemon=True).start() #arg must be tuple
    threading.Thread(target=heartbeat, args=(sock,), daemon=True).start() #daemon-background thread that automatically stops when main program ends

    while True:
        msg = input() #stores message

        if msg.startswith("/file"):
            parts = msg.split(" ", 1)
            if len(parts) == 2:
                filename = parts[1]

                try:
                    with open(filename, "rb") as f:
                        data = f.read()

                    sock.sendall((msg + "\n").encode())#adds newline at the end

                    # wait for READY from server via receive thread
                    ready_event.clear()
                    ready_event.wait()

                    sock.sendall(f"{len(data)}\n".encode())
                    # send in chunks
                    chunk_size = 1024
                    for i in range(0, len(data), chunk_size):
                        sock.sendall(data[i:i+chunk_size])

                    print(f"Sent file: {filename}")

                except Exception as e:
                    print("ERROR:", e)

        else:
            sock.sendall((msg + "\n").encode())#adds newline at the end
if __name__ == "__main__":
    main()
