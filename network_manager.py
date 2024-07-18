import socket
import threading
import json


class NetworkManager:
    def __init__(self, host, port, game):
        self.host = host
        self.port = port
        self.socket = None
        self.connections = []
        self.game = game

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Connected to server at {self.host}:{self.port}")
        threading.Thread(target=self.receive_data, daemon=True).start()

    def receive_data(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                self.process_data(data)
            except:
                break
        print("Disconnected from server")

    def send_data(self, data):
        self.socket.send(json.dumps(data).encode('utf-8'))

    def process_data(self, data):
        try:
            parsed_data = json.loads(data)
            self.game.handle_network_data(parsed_data)
        except json.JSONDecodeError:
            print(f"Invalid JSON data received: {data}")

    def close(self):
        if self.socket:
            self.socket.close()
