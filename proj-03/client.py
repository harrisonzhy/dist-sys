import socket
import threading
import hashlib as hasher
import queue
import argparse
import time
import random
from concurrent.futures import ThreadPoolExecutor

from utils import message as MSG
from utils import config
from utils import utils
from actions import actions

class Client:
    def __init__(self, 
                 host       =None, 
                 listen_port=None, 
                 peers      =None,
                 send_proba =0.5,
                 id         =None
                ):

        # Configurations
        CFG = config.Config()
        self.action_dict_name = CFG.get_actions_dict()

        # Message specification
        self.msg_magic = CFG.get_msg_magic()
        self.msg_magic_size = CFG.get_msg_magic_size()
        self.msg_type_size = CFG.get_msg_type_size()
        self.msg_min_size = self.msg_magic_size + self.msg_type_size + self.msg_magic_size
        self.msg_max_size = CFG.get_msg_max_size()

        # Client state
        self.host = host if host else CFG.get_client_config()['host']
        self.port = listen_port if listen_port else CFG.get_client_config()['port']
        self.id = id
        self.connected = False

        # Clocks
        self.send_proba = send_proba
        self.clock_rate = random.randint(1, 6)
        self.ticks = 0

        # Action-related items
        self.action_handler = actions.ClientActionHandler(self, self.action_dict_name)
        self.callback_handler = actions.ClientCallbackHandler(self, self.action_dict_name)
        self.message_queue = queue.Queue()
        
        # Initialize system log
        self.log = self.initialize_system_log()
        self.log_system_event(f"Log for client [{self.id}] at clock rate [{self.clock_rate}]")

        # Communication
        print("Peer host:", self.host)
        print("Peer port:", self.port)
        self.listen_socket = None
        self.peer_sockets = []

        self.start_listening()
        if peers:
            self.connect_to_peers(peers)
        
        threading.Thread(target=self.process_queued_messages, daemon=True).start()
        # threading.Thread(target=self.random_message_sender, daemon=True).start()

    def initialize_system_log(self):
        log = open(f"log/log_client_{self.id}.txt", "w+")
        self.log_system_event(f"Log for client [{self.id}] at clock rate [{self.clock_rate}]")
        return log

    def random_message_sender(self):
        """Periodically send a message to peers with probability `self.send_proba`."""
        while True:
            if random.random() < self.send_proba:
                # Create a message
                message = MSG.Message(
                    message_type="status",
                    message_args=MSG.MessageArgs(
                        f"Hello from {self.host}:{self.port} at {time.strftime('%H:%M:%S')}"
                    ),
                    endpoint=self)
                # Choose random peer to message
                if len(self.peer_sockets) > 0:
                    random_socket = random.choice(self.peer_sockets)
                    self.send_peer_message(random_socket, message)
            time.sleep(1)
    
    def send_peer_message(self, peer_socket, message: MSG.Message):
        if self.connected:
            try:
                # Send message to server
                # print("Send message to server...")
                encoded_message = message.encode()
                length = len(encoded_message)
                peer_socket.sendall(length.to_bytes(4, 'big'))
                peer_socket.sendall(encoded_message)
                print(f"[Peer] Sent message...")
            except Exception as e:
                print("[Peer] Failed to send message. Connection lost:", e)
                self.disconnect()
        else:
            print("[Peer] Not connected to server.") 

    def recv_peer_messages(self, peer_socket):
        """Handle peer messages for a given socket."""
        try:
            while True:
                # First, read the 4-byte message length.
                length_bytes = utils.recv_all(peer_socket, 4)
                if not length_bytes:
                    print("[Peer] Connection closed by remote peer.")
                    break
                message_length = int.from_bytes(length_bytes, 'big')

                # Now, read the actual message.
                message_bytes = utils.recv_all(peer_socket, message_length)
                if not message_bytes:
                    print("[Peer] Connection closed during message reception.")
                    break

                # Decode and process the message.
                message = MSG.Message.from_bytes(message_bytes.decode("utf-8"), self)
                if message.valid():
                    message_type, message_content = message.unpack()
                    message_args = MSG.MessageArgs.to_arglist(message_content)
                    self.message_queue.put((message_type, message_args))
                else:
                    print("[Peer] Received invalid message.")
        except Exception as e:
            print("[Peer] Lost connection to peer due to:", e)
        finally:
            try:
                peer_socket.close()
            except Exception as e:
                print("[Peer] Error closing socket:", e)
            if peer_socket in self.peer_sockets:
                self.peer_sockets.remove(peer_socket)
            print("[Peer] Cleaned up connection.")

    def start_listening(self):
        """Create a listening socket for incoming peer connections."""
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.listen_socket.bind((self.host, self.port))
            self.listen_socket.listen(5)
            print(f"[Peer] Listening for incoming connections on {self.host}:{self.port}")
            threading.Thread(target=self.accept_connections, daemon=True).start()
        except Exception as e:
            print("[Peer] Failed to start listening due to:", e)

    def accept_connections(self):
        """Continuously accept incoming peer connections."""
        while True:
            try:
                peer_socket, addr = self.listen_socket.accept()
                print(f"[Peer] Accepted connection from {addr}")
                # self.peer_sockets.append(peer_socket)
                threading.Thread(target=self.recv_peer_messages, args=(peer_socket,), daemon=True).start()
            except Exception as e:
                print("[Peer] Error accepting connection:", e)
                break

    def connect_to_peer(self, peer_host, peer_port):
        """Attempt to connect to a peer until successful."""
        while True:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                peer_socket.connect((peer_host, peer_port))
                print(f"[Peer] Connected to peer at {peer_host}:{peer_port}")
                self.peer_sockets.append(peer_socket)
                threading.Thread(target=self.recv_peer_messages, args=(peer_socket,), daemon=True).start()
                break
            except Exception as e:
                print(f"[Peer] Could not connect to peer at {peer_host}:{peer_port}. Retrying...", e)
                time.sleep(1)


    def connect_to_peers(self, peers):
        """Connect to multiple peers given a list of strings in 'host:port' format."""
        for peer in peers:
            try:
                peer_host, peer_port_str = peer.split(':')
                peer_port = int(peer_port_str)
                self.connect_to_peer(peer_host, peer_port)
            except Exception as e:
                print(f"[Peer] Invalid peer entry '{peer}':", e)
        self.connected = True

    def broadcast_message(self, message: MSG.Message):
        """Send a message to all connected peers."""
        for socket in self.peer_sockets:
            self.send_peer_message(message, socket)

    def log_system_event(self, *args):
        self.log.write(",".join(map(str, args)) + "\n")
        self.log.flush()

    def perform_random_event(self):
        if self.connected:
            random_update = random.randint(1, 10)
            message_args = MSG.MessageArgs(f"Local time at client {self.id}: {self.ticks}")
            message = MSG.Message(message_type="status", message_args=message_args, endpoint=self)
            if (random_update == 1 or random_update == 2):
                self.send_peer_message(self.peer_sockets[random_update - 1], message)
                recipient = f"Client {random_update}"
            else:
                recipient = "None"
            self.log_system_event(
                f"[Ticks: {self.ticks}, System: {time.strftime('%H:%M:%S')}] Sent message '{message_args.to_string()}' to [{recipient}]"
            )

    def process_queued_messages(self):
        """Processes messages from the server message queue (serially)."""
        while True:
            try:
                _, message_args = self.message_queue.get_nowait()
                # self.perform_callback(message_type, message_args)
                print("[Peer] Received message...")
                self.log_system_event(
                    f"[Ticks: {self.ticks}, System: {time.strftime('%H:%M:%S')}] Received message '{message_args}' at queue length [{self.message_queue.qsize()}]"
                )
            except queue.Empty:
                self.perform_random_event()
            except Exception as e:
                print("[Peer] Message process error due to:", e)
            self.ticks += 1
            time.sleep(1 / self.clock_rate)

    def perform_callback(self, message_type: str, message_args: list[str]):
        action_status = self.callback_handler.execute_action(message_type, message_args)
        if action_status:
            # print("[Peer] Action OK.")
            pass
        else:
            print(f"[Peer] Action {message_type} Unsuccessful.")
    
    def disconnect(self):
        """Cleanly disconnect from all peers and close listening socket."""
        print("[Peer] Disconnecting...")
        for socket in self.peer_sockets:
            try:
                socket.close()
            except Exception:
                pass
        self.peer_sockets.clear()
        if self.listen_socket:
            try:
                self.listen_socket.close()
            except Exception:
                pass
        self.connected = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the peer client.")
    parser.add_argument('--id', type=int, help="ID for client log", default=None)
    parser.add_argument('--host', type=int, help="Host for this client to connect to.", default=None)
    parser.add_argument('--port', type=int, help="Port for this peer to listen on.", default=None)
    parser.add_argument('--peers', type=str,
                        help="Comma-separated list of peers in host:port format (e.g. 127.0.0.1:5555,127.0.0.1:5556)",
                        default=None)
    parser.add_argument('--proba', type=float,
                        help="Probability (0<=p<=1) to send a message each iteration", default=0.5)
    args = parser.parse_args()
    peers = args.peers.split(',') if args.peers else None
    client = Client(host=args.host, listen_port=args.port, peers=peers, send_proba=args.proba, id=args.id)

    while True:
        time.sleep(1)
