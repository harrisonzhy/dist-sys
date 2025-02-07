import socket
import threading

from utils import utils

class Client:
    def __init__(self):
        CFG = utils.Config()
        self.msg_magic = CFG.get_msg_magic()
        self.msg_magic_size = CFG.get_msg_magic_size()
        self.msg_type_size = CFG.get_msg_type_size()

        self.msg_min_size = self.msg_magic_size + self.msg_type_size + self.msg_magic_size
        self.msg_max_size = CFG.get_msg_max_size()

        self.host = CFG.get_client_config()['host']
        self.port = CFG.get_client_config()['port']
        self.connected = False

        print("Client host:", self.host)
        print("Client port:", self.port)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def send_server_message(self, message: utils.Message):
        """Send a message to the server."""
        if self.connected:
            try:
                print("Send server message...")
                self.client_socket.send(message.encode())
            except:
                print("Failed to send message. Connection lost.")
                self.disconnect()
        else:
            print("Not connected to server.")
    
    def recv_server_message(self):
        while self.connected:
            try:
                message_bytes = self.client_socket.recv(self.msg_max_size).decode("utf-8")
                message_type, message_content = utils.Message(message_bytes).unpack()
                print(f"Received message type {message_type}: {message_content}")
                action_status = self.perform_action(message_type, message_content)
                print("Action status:", action_status)
                if action_status:
                    print("Action OK")
                else:
                    print("Action Unsuccessful...")
            except:
                break
        print("Lost connection to the server.")
        self.disconnect()
    
    def connect(self):
        """Establish a connection with the server."""
        if self.connected:
            print("Already connected to the server.")
            return
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            print("Connected to the server.")
            self.connected = True
            threading.Thread(target=self.recv_server_message, daemon=True).start()
        except ConnectionRefusedError:
            print("Failed to connect to the server. Is it running?")

    def disconnect(self):
        """Disconnect from the server."""
        if self.client_socket:
            self.client_socket.close()
            self.connected = False
            print("Disconnected from the server.")

if __name__ == "__main__":
    client = Client()
    threading.Thread(target=client.recv_server_message, daemon=True).start()
    if True:
        msg = utils.Message(message_content="Hello World", message_type="00000000", endpoint=client)
        client.send_server_message(msg)

        while True:
            pass
