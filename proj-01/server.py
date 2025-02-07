import socket
import threading

from server_sys import db
from utils import utils

class Server:
    def __init__(self):
        CFG = utils.Config()
        self.account_db_name = CFG.get_account_db()

        self.msg_magic = CFG.get_msg_magic()
        self.msg_magic_size = CFG.get_msg_magic_size()
        self.msg_type_size = CFG.get_msg_type_size()

        self.msg_min_size = self.msg_magic_size + self.msg_type_size + self.msg_magic_size
        self.msg_max_size = CFG.get_msg_max_size()

        self.account_db = db.AccountDatabase(self.account_db_name)
        self.host = CFG.get_server_config()['host']
        self.port = CFG.get_server_config()['port']

        print("Server host:", self.host)
        print("Server port:", self.port)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.clients = []
        self.action_map = {} # Maps string action identifiers to functions
    
    def start(self):
        """Start the server and accept client connections."""
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"New connection from {addr}")
            self.clients.append(client_socket)
            threading.Thread(target=self.recv_client_message, args=(client_socket, addr)).start()

    def recv_client_message(self, client_socket, addr) -> bool:
        """Handle client messages."""
        try:
            while True:
                message_bytes = client_socket.recv(self.msg_max_size).decode("utf-8")
                message = utils.Message.from_bytes(message_bytes, self)
                if message.valid():
                    message_type, message_content = message.unpack()
                    print(f"Received message type {message_type} from {addr}: {message_content}")
                    action_status = self.perform_action(message_type, message_content)
                    if action_status:
                        print("Action OK")
                    else:
                        print("Action Unsuccessful")
        except ConnectionResetError:
            print(f"Client {addr} disconnected.")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                client_socket.close()

    def perform_action(self, message_type: str, message_content: str):
        # TODO: Actions
        return True
    
    def create_account(self, username: str, password: str):
        self.account_db.add_account(username, password)

    def delete_account(self, username: str):
        self.account_db.delete_account(username)
    
    def login_account(self, username: str, password: str):
        self.account_db.verify_account(username, password)
    
if __name__ == "__main__":
    server = Server()
    server.start()
