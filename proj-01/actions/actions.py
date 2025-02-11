import json
from utils import message as MSG

class BaseActionHandler:
    """Base class for client and server action implementations."""
    
    def __init__(self, file_path: str):
        """Load action mappings from a JSON file when an instance is created."""
        self.action_map = self.load_action_map(file_path)
        self.inverse_action_map = {v: k for k, v in self.action_map.items()}

    def load_action_map(self, file_path: str):
        """Load action mappings from a JSON file and return as a dictionary."""
        try:
            with open(file_path, "r") as file:
                print("[Base] Loaded action mappings.")
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Base] Error loading action map: {e}")
            return {}
    
    def execute_action(self, action_code: str, args: list[str]):
        """Dynamically execute an action on `this` handler."""
        # print("[Base] Action map loaded:", self.action_map)
        action_name = self.action_map.get(action_code)
        if not action_name:
            print("[Base] Action execution was unsuccessful.")
            return False

        action_function = getattr(self, action_name, None)
        if not action_function:
            print(f"[Base] Function {action_name} not found in {self.__class__.__name__}")
            return False

        return action_function(*args)  # Execute function

class ClientCallbackHandler(BaseActionHandler):
    """Handles client-specific action callbacks once a server response is received."""
    def __init__(self, client, file_path: str, ui_callback):
        super().__init__(file_path)
        self.client = client
        self.ui_callback = ui_callback

    def status(self, contents: str):
        print(f"[Client Callback] Status: {contents}")
        return True

    def create_account(self, contents: str):
        print(f"[Client Callback] Created account: {contents}")
        self.update_ui("account_status", contents)
        return True

    def login_account(self, contents: str):
        print(f"[Client Callback] Logged in: {contents}")
        self.update_ui("auth_status", contents)
        return True

    def send_text_message(self, contents: str):
        print(f"[Client Callback] Sent text message: {contents}")
        self.update_ui("message_status", contents)
        return True

    def fetch_text_messages(self, contents: str):
        print(f"[Client Callback] Retrieved recent text messages: {contents}")
        self.update_ui("fetched_messages", contents)
        return True

    def update_ui(self, key, value):
        """Update session state through UI callback."""
        if self.ui_callback:
            self.ui_callback(key, value)

class ClientActionHandler(BaseActionHandler):
    """Handles client-specific actions."""
    def __init__(self, client, file_path: str):
        super().__init__(file_path)
        self.client = client

    def status(self, contents: str) -> bool:
        print(f"[Client] Status: {contents}")
        return True

    def create_account(self, username: str, hashed_password: str) -> bool:
        print(f"[Client] Creating account for {username}...")
        msg_content = MSG.MessageArgs(username, hashed_password)
        msg = MSG.Message(message_args=msg_content, message_type="create_account", endpoint=self.client)
        self.client.send_server_message(msg)
        return True

    def delete_account(self, username: str) -> bool:
        print(f"[Client] Deleting account for {username}...")
        msg_content = MSG.MessageArgs(username)
        msg = MSG.Message(message_args=msg_content, message_type="delete_account", endpoint=self.client)
        self.client.send_server_message(msg)
        return True

    def login_account(self, username: str, hashed_password: str) -> bool:
        print(f"[Client] Logging in {username}...")
        msg_content = MSG.MessageArgs(username, hashed_password)
        msg = MSG.Message(message_args=msg_content, message_type="login_account", endpoint=self.client)
        self.client.send_server_message(msg)
        return True

    def send_text_message(self, username1: str, username2: str, message_text: str) -> bool:
        print(f"[Client] Sending text message from {username1} to {username2}...")
        msg_content = MSG.MessageArgs(username1, username2, message_text)
        msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=self.client)
        self.client.send_server_message(msg)
        return True
    
    def fetch_text_messages(self, username1: str, username2: str, k: int) -> bool:
        print("[Client] Retrieving recent text messages...")
        msg_content = MSG.MessageArgs(username1, username2, str(k))
        msg = MSG.Message(message_args=msg_content, message_type="fetch_text_messages", endpoint=self.client)
        self.client.send_server_message(msg)
        return True

class ServerActionHandler(BaseActionHandler):
    """Handles server-specific actions."""
    def __init__(self, server, file_path: str):
        super().__init__(file_path)
        self.server = server

    def status(self, contents: str) -> bool:
        print(f"[Server] Status: {contents}")
        return True

    def create_account(self, username: str, hashed_password: str) -> bool:
        print(f"[Server] Creating account for {username}...")
        return self.server.account_db.create_account(username, hashed_password)

    def delete_account(self, username: str) -> bool:
        print(f"[Server] Deleting account for {username}...")
        return self.server.account_db.delete_account(username)

    def login_account(self, username: str, hashed_password: str) -> bool:
        print(f"[Server] Handling login request for {username}...")
        return self.server.account_db.login_account(username, hashed_password)

    def send_text_message(self, username1: str, username2: str, message_text: str) -> bool:
        print(f"[Server] Processing text message from {username1} to {username2}...")
        return self.server.account_db.send_text_message(username1, username2, message_text)

    def fetch_text_messages(self, username1: str, username2: str, k: str) -> list[str]:
        print("[Server] Fetching recent text messages...")
        k = int(k)
        return self.server.account_db.fetch_text_messages(username1, username2, k)

    def delete_text_message(self, message_id: str) -> bool:
        print("[Server] Deleting text message...")
        return self.server.account_db.delete_text_message(message_id)