import socket
import threading
import hashlib as hasher

from utils import message as MSG
from utils import config
from actions import actions

class Client:
    def __init__(self):
        CFG = config.Config()
        self.action_dict_name = CFG.get_actions_dict()

        self.msg_magic = CFG.get_msg_magic()
        self.msg_magic_size = CFG.get_msg_magic_size()
        self.msg_type_size = CFG.get_msg_type_size()

        self.msg_min_size = self.msg_magic_size + self.msg_type_size + self.msg_magic_size
        self.msg_max_size = CFG.get_msg_max_size()

        self.host = CFG.get_client_config()['host']
        self.port = CFG.get_client_config()['port']
        self.connected = False

        self.action_handler = actions.ClientActionHandler(self, self.action_dict_name)

        print("Client host:", self.host)
        print("Client port:", self.port)

        self.connect()

    def send_server_message(self, message: MSG.Message):
        """Send a message to the server."""
        if self.connected:
            try:
                if message.valid():
                    print("Send message to server...")
                    encoded_message = message.encode()
                    length = len(encoded_message)
                    self.client_socket.send(length.to_bytes(4, 'big'))
                    self.client_socket.send(encoded_message)
            except:
                print("Failed to send message. Connection lost.")
                self.disconnect()
        else:
            print("Not connected to server.")
    
    def recv_server_message(self):
        while self.connected:
            try:
                message_bytes = self.client_socket.recv(self.msg_max_size).decode("utf-8")
                message = MSG.Message.from_bytes(message_bytes, self)
                if message.valid():
                    message_type, message_content = message.Message(message_bytes).unpack()
                    print(f"Received message type {message_type}: {message_content}")
                    message_args = MSG.MessageArgs.to_arglist(message_content)
                    action_status = self.perform_action(message_type, message_args)
                    if action_status:
                        print("Action OK.")
                    else:
                        print("[Client] Action Unsuccessful.")
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

    def perform_action(self, message_type, message_args: list[str]):
        print(message_args)
        return self.action_handler.execute_action(message_type, message_args)

    def disconnect(self):
        """Disconnect from the server."""
        if self.client_socket:
            self.client_socket.close()
            self.connected = False
            print("Disconnected from the server.")


def test_end_to_end(client):
    def hash_function(s: str):
        return hasher.sha256(s.encode()).hexdigest()

    msg_content = MSG.MessageArgs("Hello World", 3)
    msg = MSG.Message(message_args=msg_content, message_type="reserved", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("alice", hash_function("password1"))
    msg = MSG.Message(message_args=msg_content, message_type="create_account", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", hash_function("password2"))
    msg = MSG.Message(message_args=msg_content, message_type="create_account", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("alice", "bob", "Hi Bob!")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", "alice", "Hello Alice!")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("alice", "bob", "How are you?")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", "alice", "Good how about you?")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", "alice", 3)
    msg = MSG.Message(message_args=msg_content, message_type="fetch_text_messages", endpoint=client)
    client.send_server_message(msg)


if __name__ == "__main__":
    client = Client()
    threading.Thread(target=client.recv_server_message, daemon=True).start()

    test_end_to_end(client)

    while True:
        pass
