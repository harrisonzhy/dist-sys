import unittest
from unittest.mock import Mock
from actions import ClientCallbackHandler, ClientActionHandler, ServerActionHandler
import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import your module
from utils import message as MSG

class TestActionHandlers(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.mock_server = Mock()
        self.session_state = {'account_status': False, 'auth_status': False, 'message_status': False, 'texts': {}, 'username': 'test_user'}
        self.client_callback_handler = ClientCallbackHandler(self.mock_client, "mock_file.json", self.session_state)
        self.client_action_handler = ClientActionHandler(self.mock_client, "mock_file.json")
        self.server_action_handler = ServerActionHandler(self.mock_server, "mock_file.json")

    def test_client_callback_create_account(self):
        self.client_callback_handler.create_account("True")
        self.assertTrue(self.session_state['account_status'])
        
        self.client_callback_handler.create_account("False")
        self.assertFalse(self.session_state['account_status'])

    def test_client_callback_login_account(self):
        self.client_callback_handler.login_account("True")
        self.assertTrue(self.session_state['auth_status'])
        
        self.client_callback_handler.login_account("False")
        self.assertFalse(self.session_state['auth_status'])

    def test_client_callback_send_text_message(self):
        self.client_callback_handler.send_text_message("True")
        self.assertTrue(self.session_state['message_status'])
        
        self.client_callback_handler.send_text_message("False")
        self.assertFalse(self.session_state['message_status'])

    def test_client_callback_fetch_text_messages(self):
        self.client_callback_handler.fetch_text_messages("123", "test_user", "friend", "Hello")
        self.assertIn("friend", self.session_state['texts'])
        self.assertEqual(len(self.session_state['texts']['friend']), 1)
        self.assertEqual(self.session_state['texts']['friend'][0]['text'], "Hello")

    def test_client_action_create_account(self):
        self.assertTrue(self.client_action_handler.create_account("test_user", "hashed_pass"))
        self.mock_client.send_server_message.assert_called()

    def test_client_action_login_account(self):
        self.assertTrue(self.client_action_handler.login_account("test_user", "hashed_pass"))
        self.mock_client.send_server_message.assert_called()

    def test_client_action_send_text_message(self):
        self.assertTrue(self.client_action_handler.send_text_message("test_user", "friend", "Hello"))
        self.mock_client.send_server_message.assert_called()

    def test_client_action_fetch_text_messages(self):
        self.assertTrue(self.client_action_handler.fetch_text_messages("test_user", 10))
        self.mock_client.send_server_message.assert_called()

    def test_client_action_delete_text_message(self):
        self.assertTrue(self.client_action_handler.delete_text_message("123"))
        self.mock_client.send_server_message.assert_called()

    def test_server_action_create_account(self):
        self.server_action_handler.create_account("test_user", "hashed_pass")
        self.mock_server.account_db.create_account.assert_called_with("test_user", "hashed_pass")

    def test_server_action_delete_account(self):
        self.server_action_handler.delete_account("test_user")
        self.mock_server.account_db.delete_account.assert_called_with("test_user")

    def test_server_action_login_account(self):
        self.server_action_handler.login_account("test_user", "hashed_pass")
        self.mock_server.account_db.login_account.assert_called_with("test_user", "hashed_pass")

    def test_server_action_send_text_message(self):
        self.server_action_handler.send_text_message("test_user", "friend", "Hello")
        self.mock_server.account_db.send_text_message.assert_called_with("test_user", "friend", "Hello")

    def test_server_action_fetch_text_messages(self):
        self.server_action_handler.fetch_text_messages("test_user", "10")
        self.mock_server.account_db.fetch_text_messages.assert_called_with("test_user", 10)

    def test_server_action_delete_text_message(self):
        self.server_action_handler.delete_text_message("123")
        self.mock_server.account_db.delete_text_message.assert_called_with("123")

if __name__ == "__main__":
    unittest.main()
