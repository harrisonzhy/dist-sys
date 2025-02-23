import pytest
import time
import hashlib as hasher
import queue

from client import Client

def process_queue_headless(setup_client, poll_queue=False, timeout=2):
    """
    Pops a message off the server_message_queue at least once.
    If poll_queue=True, continues popping until the queue is empty.
    Returns:
        bool: True if no message contains an error code; False otherwise.
    """
    error_codes = ["False"]
    def pop_once(timeout):
        """
        Pops a single message off the queue within 'timeout' seconds.
        Returns:
            bool: True if message does not contain an error code; False otherwise.
        """
        try:
            _, message_args = setup_client.server_message_queue.get(timeout=timeout)
            for e in error_codes:
                if e in message_args:
                    return False
            return True
        except queue.Empty:
            return False

    is_ok = pop_once(timeout)
    if poll_queue:
        while True:
            try:
                _, message_args = setup_client.server_message_queue.get(timeout=timeout)
                for e in error_codes:
                    if e in message_args:
                        is_ok = False
            except queue.Empty:
                break
    return is_ok

def wait_for_condition(condition_func, timeout=2):
    """Waits for a condition function to return True within a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
    return False

def check_condition(queue_list):
    queue_list = list(queue_list.queue)
    if len(queue_list) == 0:
        return False
    _, message_args = queue_list[0]
    print(message_args)
    return True

@pytest.fixture(scope="module")
def setup_client():
    """Fixture to set up and tear down the client."""
    client = Client()
    
    # Wait for the client to establish a connection
    assert wait_for_condition(lambda: client.connected), "Client failed to connect to server."
    
    yield client  # Provide the client instance to tests

def test_create_account(setup_client):
    """Test creating an account."""
    client = setup_client
    hashed_password = hasher.sha256("password1".encode()).hexdigest()
    assert client.action_handler.create_account("testuser", hashed_password)
    assert client.action_handler.create_account("recipientuser", hashed_password)
    # Wait for server response
    wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_login_account(setup_client):
    """Test logging into an existing account."""
    client = setup_client
    hashed_password = hasher.sha256("password1".encode()).hexdigest()
    assert client.action_handler.login_account("testuser", hashed_password)
    # Wait for server response
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_send_message(setup_client):
    """Test sending text messages between two users."""
    client = setup_client
    assert client.action_handler.send_text_message("testuser", "recipientuser", "Hello!")
    assert client.action_handler.send_text_message("testuser", "recipientuser", "World!")
    assert client.action_handler.send_text_message("recipientuser", "testuser", "Hello!")
    assert client.action_handler.send_text_message("recipientuser", "testuser", "World!")
    # Wait for server response
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client, poll_queue=True)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_fetch_messages(setup_client):
    """Test fetching messages for a user."""
    client = setup_client
    # Attempt to fetch the last 5 messages
    assert client.action_handler.fetch_text_messages("recipientuser", 5)
    # Wait for server response
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_delete_text_message(setup_client):
    """Test deleting a text message."""
    client = setup_client
    message_id = "1"  # Assuming "1" is valid for the test
    assert client.action_handler.delete_text_message(message_id)
    # Wait for server response
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

    # Optionally re-fetch messages to ensure it's deleted
    # test_fetch_messages(setup_client)
    # wait_for_condition(lambda: client.server_message_queue.empty())

def test_delete_account(setup_client):
    """Test deleting an existing account."""
    client = setup_client
    assert client.action_handler.delete_account("testuser")
    # Wait for server response
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_create_duplicate_account(setup_client):
    """
    Test creating an account with a username that already exists.
    This should fail or return an error from the server.
    """
    client = setup_client
    hashed_password = hasher.sha256("password1".encode()).hexdigest()
    
    # Create a new user "duplicateuser"
    assert client.action_handler.create_account("duplicateuser", hashed_password)
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client, poll_queue=True)
    wait_for_condition(lambda: client.server_message_queue.empty())

    # Attempt to create the same user again - should fail or return an error
    assert client.action_handler.create_account("duplicateuser", hashed_password)
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert not process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())


def test_login_with_wrong_password(setup_client):
    """
    Test logging in with a wrong password for an existing user.
    This should fail or return an error from the server.
    """
    client = setup_client
    hashed_password = hasher.sha256("password1".encode()).hexdigest()
    
    # Create a user for testing
    assert client.action_handler.create_account("wrongpwduser", hashed_password)
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

    # Now try logging in with incorrect password
    bad_password = hasher.sha256("wrongpassword".encode()).hexdigest()
    assert client.action_handler.login_account("wrongpwduser", bad_password)
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert not process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_send_message_to_non_existent_user(setup_client):
    """
    Test sending a message to a user that doesn't exist.
    This should fail or return an error from the server.
    """
    client = setup_client
    non_existent_user = "no_such_user"
    sender = "recipientuser"  # Re-using from earlier tests or create a new one

    assert client.action_handler.send_text_message(sender, non_existent_user, "Hello?")
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert not process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_fetch_messages_for_non_existent_user(setup_client):
    """
    Test fetching messages for a user that doesn't exist.
    Should return a 'no messages' response.
    """
    client = setup_client
    assert client.action_handler.fetch_text_messages("ghostuser", 5)
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_delete_non_existent_message(setup_client):
    """
    Test attempting to delete a message that doesn't exist.
    """
    client = setup_client
    fake_message_id = "999999"  # Assuming this does not exist

    assert client.action_handler.delete_text_message(fake_message_id)
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert not process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

def test_delete_account_that_does_not_exist(setup_client):
    """
    Test deleting an account that doesn't exist on the server.
    This should fail or return an error from the server.
    """
    client = setup_client
    assert client.action_handler.delete_account("idontexist")
    assert wait_for_condition(lambda: not client.server_message_queue.empty())
    assert not process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty()) 

def test_multiple_users_sending_to_one_recipient(setup_client):
    """
    Test multiple users sending messages to one recipient user.
    """
    client = setup_client
    recipient = "massRecipient"
    r_pass = hasher.sha256("masspass".encode()).hexdigest()
    
    # Create the recipient
    client.action_handler.create_account(recipient, r_pass)
    wait_for_condition(lambda: not client.server_message_queue.empty())
    process_queue_headless(client)
    wait_for_condition(lambda: client.server_message_queue.empty())

    # Create and message from multiple users
    for i in range(3):
        user = f"sender_{i}"
        user_pass = hasher.sha256(f"pass_{i}".encode()).hexdigest()
        client.action_handler.create_account(user, user_pass)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client)
        wait_for_condition(lambda: client.server_message_queue.empty())

        # Login user
        client.action_handler.login_account(user, user_pass)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client)
        wait_for_condition(lambda: client.server_message_queue.empty())

        # Send a message
        client.action_handler.send_text_message(user, recipient, f"Hello from {user}")
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client)
        wait_for_condition(lambda: client.server_message_queue.empty())

def test_send_messages_different_pairs(setup_client):
    """
    Test sending messages between multiple distinct user pairs.
    """
    client = setup_client
    pairs = [("recipientuser", "recipientuser"), ("duplicateuser", "wrongpwduser")]
    for s, r in pairs:
        assert client.action_handler.send_text_message(s, r, f"Hello from {s} to {r}")
        wait_for_condition(lambda: not client.server_message_queue.empty())
        # Adjust if you expect them to all be valid:
        process_queue_headless(client)
        wait_for_condition(lambda: client.server_message_queue.empty())

def test_login_repeatedly_in_loop(setup_client):
    """
    Test logging into the same account multiple times in a tight loop.
    """
    client = setup_client
    username = "looploginuser"
    password = hasher.sha256("looploginpass".encode()).hexdigest()

    # Create account
    client.action_handler.create_account(username, password)
    wait_for_condition(lambda: not client.server_message_queue.empty())
    process_queue_headless(client, poll_queue=True)
    wait_for_condition(lambda: client.server_message_queue.empty())

    for i in range(3):
        client.action_handler.login_account(username, password)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        # Depending on server logic, either each login is fine or it might reject subsequent ones:
        process_queue_headless(client, poll_queue=True)
        wait_for_condition(lambda: client.server_message_queue.empty())

def test_delete_multiple_accounts_in_loop(setup_client):
    """
    Test creating and deleting multiple user accounts in a loop.
    """
    client = setup_client
    for i in range(3):
        user = f"loopdel_{i}"
        pwd = hasher.sha256(f"loopdelpwd{i}".encode()).hexdigest()
        # Create
        client.action_handler.create_account(user, pwd)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client, poll_queue=True)
        wait_for_condition(lambda: client.server_message_queue.empty())

        # Delete
        client.action_handler.delete_account(user)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client, poll_queue=True)
        wait_for_condition(lambda: client.server_message_queue.empty())

def test_create_and_delete_same_user_rapidly(setup_client):
    """
    Create and delete the same user multiple times rapidly to test server stability.
    """
    client = setup_client
    user = "rapid_cycle"
    pwd = hasher.sha256("rapid_cycle_pass".encode()).hexdigest()

    for _ in range(3):
        # Create
        client.action_handler.create_account(user, pwd)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client, poll_queue=True)
        wait_for_condition(lambda: client.server_message_queue.empty())

        # Delete
        client.action_handler.delete_account(user)
        wait_for_condition(lambda: not client.server_message_queue.empty())
        process_queue_headless(client, poll_queue=True)
        wait_for_condition(lambda: client.server_message_queue.empty())
