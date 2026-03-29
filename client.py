import socket
import ssl
import threading
import time

HOST = "127.0.0.1"
PORT = 5001


def receive(sock):
    while True:
        try:
            msg = sock.recv(1024)
            if not msg:
                break
            decoded = msg.decode()
            if decoded.strip() == "/pong":  # hide heartbeat responses
                continue
            print(decoded, end="")
        except:
            break


def heartbeat(sock):
    while True:
        try:
            sock.sendall(b"/ping\n")
            time.sleep(10)
        except:
            break


def main():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = context.wrap_socket(s, server_hostname="localhost")
    sock.connect((HOST, PORT))

    print(sock.recv(1024).decode(), end="")
    username = input()
    sock.sendall((username + "\n").encode())

    print(sock.recv(1024).decode(), end="")
    room = input()
    sock.sendall((room + "\n").encode())

    threading.Thread(target=receive, args=(sock,), daemon=True).start()
    threading.Thread(target=heartbeat, args=(sock,), daemon=True).start()

    while True:
        msg = input()
        sock.sendall((msg + "\n").encode())


if __name__ == "__main__":
    main()
