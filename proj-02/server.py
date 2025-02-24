import socket
import threading
import queue
import grpc
import uuid
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Iterable as iterable

from database import db
from utils import message as MSG
from utils import config
from utils import utils
from actions import actions

from utils import service_pb2
from utils import service_pb2_grpc

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

        self.client_message_queues = {}
        self.executor = ThreadPoolExecutor(max_workers=1)

        self.grpc = True
        self.server_grpc = None

        print("Server host:", self.host)
        print("Server port:", self.port)

        self.start()

    class MessageServiceServicer(service_pb2_grpc.MessageServiceServicer):
        def __init__(self, server):
            self.server = server

        def Register(self, request, context):
            client_id = str(uuid.uuid4())
            print("[gRPC] Assigned client ID:", client_id)
            return service_pb2.RegisterResponse(client_id=client_id)

        def SendMessage(self, request, context):
            print("[gRPC] Received message:", request.message)
            # Extract registered client ID from context
            # metadata = dict(context.invocation_metadata())
            # client_id = metadata.get('client-id')

            message = MSG.Message.from_bytes(request.message, self.server)
            if message.valid():
                message_type, message_content = message.unpack()
                message_args = MSG.MessageArgs.to_arglist(message_content)

                # Now we have a unique client ID from the metadata
                print(f"Received message type {message_type} from client: {message_content}")
                
                # Perform the action described by the message for this client and return responses
                return self.server.perform_action(message_type, message_args)
            else:
                return service_pb2.MessageResponse(response=['Error'])

    def start_grpc(self):
        self.server_grpc = grpc.server(ThreadPoolExecutor(max_workers=10))
        service_pb2_grpc.add_MessageServiceServicer_to_server(
            self.MessageServiceServicer(self), self.server_grpc
        )
        self.server_grpc.add_insecure_port('[::]:' + str(self.port))
        self.server_grpc.start()
        print(f"[Server] gRPC server started on {self.host}:{self.port}")

        try:
            self.server_grpc.wait_for_termination()
        except Exception as e:
            print("[Server] gRPC stopped:", e)

    def start(self):
        """Start the server and accept client connections."""
        if self.grpc:
            self.start_grpc()
            return

        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[Server] Server started on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"[Server] New connection from {addr}")

            # Each client has its own message queue
            client_message_queue = queue.Queue()
            self.client_message_queues[client_socket] = client_message_queue

            threading.Thread(target=self.recv_client_message, args=(client_socket, addr), daemon=True).start()
            threading.Thread(target=self.process_queued_messages, args=(client_socket,), daemon=True).start()

    def send_client_message(self, client_socket, message: MSG.Message):
        """Send a message to the client."""
        if self.grpc:
            self.send_client_message_grpc(client_socket, message)
            return
        try:
            if message.valid():
                encoded_message = message.encode()
                length = len(encoded_message)
                client_socket.sendall(length.to_bytes(4, 'big'))
                client_socket.sendall(encoded_message)
        except Exception as e:
            print("[Server] Error sending message to client:", e)

    def recv_client_message(self, client_socket, addr) -> bool:
        """Handle client messages."""
        try:
            while True:
                # First read the message length (4 bytes)
                length_bytes = utils.recv_all(client_socket, 4)
                if length_bytes is None:
                    print(f"[Server] Client {addr} disconnected.")
                    break
                message_length = int.from_bytes(length_bytes, 'big')

                # Now read the actual message
                message_bytes = utils.recv_all(client_socket, message_length)
                if message_bytes is None:
                    print(f"[Server] Client {addr} disconnected.")
                    break

                # And process it
                message = MSG.Message.from_bytes(message_bytes.decode("utf-8"), self)
                if message.valid():
                    message_type, message_content = message.unpack()
                    # print(f"Received message type {message_type} from {addr}: {message_content}")
                    message_args = MSG.MessageArgs.to_arglist(message_content)

                    self.client_message_queues[client_socket].put((message_type, message_args))
                else:
                    # Ignore invalid messages.
                    pass
        except ConnectionResetError:
            print(f"[Server] Client {addr} disconnected.")
        except Exception as e:
            print("[Server] Message reception error due to:", e)
        finally:
            if client_socket in self.client_message_queues:
                del self.client_message_queues[client_socket]
                client_socket.close()

    def process_queued_messages(self, client_socket):
        """Processes messages from a specific client's serverside message queue (serially)."""
        while client_socket in self.client_message_queues:
            try:
                message_type, message_args = self.client_message_queues[client_socket].get()
                future = self.executor.submit(self.perform_action, message_type, message_args, client_socket)
                future.result()
            except queue.Empty:
                continue  # No messages, spin
            except Exception as e:
                print("[Server] Message process error due to: ", e)
                break  # Client was disconnected

    def perform_action(self, message_type: str, message_args: list[str], client_socket=None):
        """Executes an action and sends back the response as a list of messages."""
        ret_val = self.action_handler.execute_action(message_type, message_args)
        # Ensure ret_val is iterable
        if not hasattr(ret_val, '__iter__'):
            ret_val = [ret_val]
        
        print(f"retval item: {ret_val}")
        ret_val = [str(item) for item in ret_val]

        if self.grpc:
            # If running with gRPC, accumulate each message's string representation
            responses = []
            for item in ret_val:
                print(f"retval item: {item}")
                msg_content = MSG.MessageArgs(item)
                msg = MSG.Message(message_args=msg_content, message_type=message_type, endpoint=self)
                responses.append(msg.message_str())
            # Return the list of responses in the gRPC response
            return service_pb2.MessageResponse(responses=responses)
        else:
            # For socket-based communication, send each message individually
            for item in ret_val:
                print(f"retval item: {item}")
                msg_content = MSG.MessageArgs(item)
                msg = MSG.Message(message_args=msg_content, message_type=message_type, endpoint=self)
                self.send_client_message(client_socket, msg)
            print("[Server] Sent action status update to client.")


if __name__ == "__main__":
    server = Server()
