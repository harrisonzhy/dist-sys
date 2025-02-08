import json

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
    
    def execute_action(self, action_code: str, args: list[str]) -> bool:
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

        return action_function(*args)  # Actually execute function


class ClientActionHandler(BaseActionHandler):
    """Handles client-specific actions."""
    def __init__(self, client, file_path: str):
        super().__init__(file_path)
        self.client = client

    def reserved(self, display_str: str, iterations: str) -> bool:
        iterations = int(iterations)
        for _ in range(iterations):
            print(f"[Client] {display_str}")
        return True

    def create_account(self, username: str, hashed_password: str) -> bool:
        print(f"[Client] Creating account for {username}...")
        return True

    def delete_account(self, username: str) -> bool:
        print(f"[Client] Deleting account for {username}...")
        return True

    def login_account(self, username: str, hashed_password: str) -> bool:
        print(f"[Client] Logging in {username}...")
        return True

    def logout_account(self) -> bool:
        print("[Client] Logging out...")
        return True

    def send_text_message(self, username1: str, username2: str) -> bool:
        print(f"[Client] Sending text message from {username1} to {username2}...")
        return True

    def fetch_text_messages(self) -> bool:
        print("[Client] Retrieving recent text messages...")
        return True


class ServerActionHandler(BaseActionHandler):
    """Handles server-specific actions."""
    def __init__(self, server, file_path: str):
        super().__init__(file_path)
        self.server = server

    def reserved(self, display_str: str, iterations: str) -> bool:
        iterations = int(iterations)
        for _ in range(iterations):
            print(f"[Server] {display_str}")
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

    def logout_account(self) -> bool:
        print("[Server] Handling logout request...")
        return True

    def send_text_message(self, username1: str, username2: str, message_text: str) -> bool:
        print(f"[Server] Processing text message from {username1} to {username2}...")
        return self.server.account_db.send_text_message(username1, username2, message_text)

    def fetch_text_messages(self, username1: str, username2: str, k: str) -> bool:
        print("[Server] Fetching recent text messages...")
        k = int(k)
        return self.server.account_db.fetch_text_messages(username1, username2, k)
