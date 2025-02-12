import unittest
import threading
import time
import hashlib as hasher
from utils import message as MSG
from client import Client

def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """Waits for a condition function to return True within a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False

class TestClientEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        cls.client_thread = threading.Thread(target=cls.client.run_app, daemon=True)
        cls.client_thread.start()
        
        # Wait for the client to establish a connection
        assert wait_for_condition(lambda: cls.client.connected), "Client failed to connect to server."
    
    @classmethod
    def tearDownClass(cls):
        cls.client.disconnect()

    def test_create_account(self):
        """Test creating an account."""
        hashed_password = hasher.sha256("password1".encode()).hexdigest()
        self.assertTrue(self.client.create_account("testuser", hashed_password))
        self.assertTrue(wait_for_condition(lambda: not self.client.server_message_queue.empty()))
    
    def test_login_account(self):
        """Test logging into an existing account."""
        hashed_password = hasher.sha256("password1".encode()).hexdigest()
        self.assertTrue(self.client.login_account("testuser", hashed_password))
        self.assertTrue(wait_for_condition(lambda: not self.client.server_message_queue.empty()))
    
    def test_send_message(self):
        """Test sending a text message."""
        self.assertTrue(self.client.send_text_message("testuser", "recipientuser", "Hello!"))
        self.assertTrue(wait_for_condition(lambda: not self.client.server_message_queue.empty()))

    def test_fetch_messages(self):
        """Test fetching messages."""
        self.assertTrue(self.client.fetch_text_messages("recipientuser", 5))
        self.assertTrue(wait_for_condition(lambda: not self.client.server_message_queue.empty()))

    def test_delete_text_message(self):
        """Test deleting a text message."""
        message_id = "12345"
        self.assertTrue(self.client.delete_text_message(message_id))
        self.assertTrue(wait_for_condition(lambda: not self.client.server_message_queue.empty()))
    
    def test_delete_account(self):
        """Test deleting an account."""
        self.assertTrue(self.client.delete_account("testuser"))
        self.assertTrue(wait_for_condition(lambda: not self.client.server_message_queue.empty()))

if __name__ == "__main__":
    unittest.main()
