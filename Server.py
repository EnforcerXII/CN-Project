import socket
from threading import Thread


class Server:
    clients = []  # keeps track of clients with their sockets (in 2-tuples')

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        print("Server is ready")

    def listen(self):
        while True:
            socket, addr = self.socket.accept()

            client_name = client_socket.recv(1024).decode()
            client = {"client_name": client_name, "client_socket": client_socket}
            Server.clients.append(client)

            Thread(target=self.new_client, args=(client,)).start()

    def handle_new_client(self, client):
        client_name = client["client_name"]
        client_socket = client["client_socket"]

        while True:
            client_message = client_socket.recv(1024).decode()

            if client_name in self.clients:
                self.broadcast_message(client_name, client_message)

    def broadcast_message()
