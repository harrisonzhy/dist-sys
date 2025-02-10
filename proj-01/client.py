import socket
import threading
import hashlib as hasher
import queue
from concurrent.futures import ThreadPoolExecutor

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
        self.server_message_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=1)

        print("Client host:", self.host)
        print("Client port:", self.port)

        self.connect()

    def send_server_message(self, message: MSG.Message):
        """Send a message to the server."""
        if self.connected:
            try:
                if message.valid():
                    # Send message to server
                    # print("Send message to server...")
                    encoded_message = message.encode()
                    length = len(encoded_message)
                    self.client_socket.sendall(length.to_bytes(4, 'big'))
                    self.client_socket.sendall(encoded_message)
            except Exception as e:
                print("[Client] Failed to send message. Connection lost:", e)
                self.disconnect()
        else:
            print("[Client] Not connected to server.")

    def recv_server_message(self):
        """Handle server messages."""
        try:
            while self.connected:
                # First read the message length (4 bytes)
                length_bytes = self.client_socket.recv(4)
                if len(length_bytes) < 4:
                    break
                message_length = int.from_bytes(length_bytes, 'big')

                # Now read the actual message
                message_bytes = self.client_socket.recv(message_length).decode("utf-8")
                if not message_bytes:
                    break
                
                message = MSG.Message.from_bytes(message_bytes, self)
                if message.valid():
                    message_type, message_content = message.unpack()
                    message_args = MSG.MessageArgs.to_arglist(message_content)
                    # print(f"[Client] Received message type {message_type}")

                    # Push server response to job queue
                    self.server_message_queue.put((message_type, message_args))
                else:
                    # Ignore invalid messages.
                    # print("Invalid message.")
                    pass
        except Exception as e:
            print("[Client] Lost connection to server due to:", e)
        self.disconnect()

    def connect(self):
        """Establish a connection with the server."""
        if self.connected:
            print("[Client] Already connected to the server.")
            return
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            print("[Client] Connected to the server.")
            self.connected = True
            threading.Thread(target=self.recv_server_message, daemon=True).start()
            threading.Thread(target=self.process_queued_messages, daemon=True).start()
        except Exception as e:
            print("[Client] Failed to connect to the server due to:", e)

    def disconnect(self):
        """Disconnect from the server."""
        if self.client_socket:
            self.client_socket.close()
            self.connected = False
            print("[Client] Disconnected from the server.")
    
    def process_queued_messages(self):
        """Processes messages from the server message queue (serially)."""
        while True:
            try:
                message_type, message_args = self.server_message_queue.get()
                future = self.executor.submit(self.perform_action, message_type, message_args)
                future.result()
            except queue.Empty:
                pass
            except Exception as e:
                print("[Client] Message process error due to:", e)

    def perform_action(self, message_type: str, message_args: list[str]):
        action_status = self.action_handler.execute_action(message_type, message_args)
        if action_status:
            print("[Client] Action OK.")
        else:
            print(f"[Client] Action {message_type} Unsuccessful.")

def test_end_to_end(client):
    def hash_function(s: str):
        return hasher.sha256(s.encode()).hexdigest()

    msg_content = MSG.MessageArgs("Hello World")
    msg = MSG.Message(message_args=msg_content, message_type="status", endpoint=client)
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
    test_end_to_end(client)
    while True:
        pass
