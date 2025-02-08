import socket
import threading

from server_sys import db
from utils import message as MSG
from utils import config
from actions import actions

class Server:
    def __init__(self):
        CFG = config.Config()
        self.account_db_name = CFG.get_account_db()
        self.action_dict_name = CFG.get_actions_dict()

        self.msg_magic = CFG.get_msg_magic()
        self.msg_magic_size = CFG.get_msg_magic_size()
        self.msg_type_size = CFG.get_msg_type_size()

        self.msg_min_size = self.msg_magic_size + self.msg_type_size + self.msg_magic_size
        self.msg_max_size = CFG.get_msg_max_size()

        self.account_db = db.AccountDatabase(self.account_db_name)
        self.host = CFG.get_server_config()['host']
        self.port = CFG.get_server_config()['port']

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.action_handler = actions.ServerActionHandler(self, self.action_dict_name)
        self.clients = []

        print("Server host:", self.host)
        print("Server port:", self.port)

        self.start()
    
    def start(self):
        """Start the server and accept client connections."""
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[Server] Server started on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"[Server] New connection from {addr}")
            self.clients.append(client_socket)
            threading.Thread(target=self.recv_client_message, args=(client_socket, addr)).start()

    def send_client_message(self, client_socket, message: MSG.Message):
        """Send a message to the client."""
        try:
            if message.valid():
                encoded_message = message.encode()
                client_socket.sendall(encoded_message)
                print(f"[Server] Sent message to client: {message.message_content}")
        except Exception as e:
            print(f"[Server] Error sending message to client: {e}")


    def recv_client_message(self, client_socket, addr) -> bool:
        """Handle client messages."""
        try:
            while True:
                # First read the message length (4 bytes)
                length_bytes = client_socket.recv(4)
                if len(length_bytes) < 4:
                    print(f"[Server] Client {addr} disconnected.")
                    break
                message_length = int.from_bytes(length_bytes, 'big')

                # Now read the actual message
                message_bytes = client_socket.recv(message_length).decode("utf-8")
                if not message_bytes:
                    print(f"[Server] Client {addr} disconnected.")
                    break
                
                message = MSG.Message.from_bytes(message_bytes, self)
                if message.valid():
                    message_type, message_content = message.unpack()
                    print(f"Received message type {message_type} from {addr}: {message_content}")
                    message_args = MSG.MessageArgs.to_arglist(message_content)
                    action_status = self.perform_action(message_type, message_args)
                    if action_status:
                        print("Action OK.")
                    else:
                        print(f"[Server] Action {message_type} Unsuccessful.")
                else:
                    # Ignore invalid messages.
                    pass
        except ConnectionResetError:
            print(f"[Server] Client {addr} disconnected.")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                client_socket.close()

    def perform_action(self, message_type: str, message_args: list[str]):
        # print(message_args)
        return self.action_handler.execute_action(message_type, message_args)
    
if __name__ == "__main__":
    server = Server()
