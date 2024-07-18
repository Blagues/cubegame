import socket
import threading
import json


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.connections = {}  # Changed to a dictionary to store socket:address pairs

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while True:
            client_socket, address = self.socket.accept()
            print(f"New connection from {address}")
            self.connections[client_socket] = address
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        buffer = ""
        address = self.connections[client_socket]
        print(f"Started handling client: {address}")
        try:
            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        print(f"Client {address} disconnected.")
                        break
                    buffer += data
                    while buffer:
                        try:
                            parsed_data, index = json.JSONDecoder().raw_decode(buffer)
                            self.process_data(parsed_data, client_socket)
                            buffer = buffer[index:].strip()
                        except json.JSONDecodeError:
                            # If we can't parse the JSON, we need more data
                            break
                except socket.error as e:
                    if e.errno == 104:  # Connection reset by peer
                        print(f"Connection reset by client {address}")
                    else:
                        print(f"Socket error with client {address}: {e}")
                    break
                except Exception as e:
                    print(f"Error handling client {address}: {e}")
                    break
        finally:
            print(f"Closing connection with {address}")
            del self.connections[client_socket]
            client_socket.close()

    def send_data(self, data, sender_socket):
        for conn in self.connections:
            if conn != sender_socket:  # Don't send to the original sender
                try:
                    conn.send(json.dumps(data).encode('utf-8'))
                except:
                    print(f"Failed to send data to {self.connections[conn]}")

    def process_data(self, data, sender_socket):
        try:
            self.send_data(data, sender_socket)
        except Exception as e:
            print(f"Error processing data: {e}")

    def close(self):
        if self.socket:
            self.socket.close()


if __name__ == "__main__":
    server = Server("127.0.0.1", 5000)
    server.start()
    input("Press Enter to close server\n")
    server.close()