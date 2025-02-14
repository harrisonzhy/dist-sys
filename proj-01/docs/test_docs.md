# Test Suite Documentation

## [Account Database Test Suite Documentation]

## Overview

This document outlines the test suite for the `AccountDatabase` class, ensuring the correctness of user account management, conversations, messaging, message deletion, and security against edge cases such as SQL injection and concurrent access.

## Test Setup

The test suite uses `pytest` and a temporary file-based database to allow multiprocessing support.

## Dependencies

- `pytest`
- `multiprocessing`
- `tempfile`
- `os`
- `db.AccountDatabase`

## Database Initialization

A temporary database file is created for testing:

```python
TEMP_DB_PATH = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name  
```

A `pytest` fixture initializes and cleans up the database:

```python
@pytest.fixture(scope="session")
def test_db():
    db = AccountDatabase(TEMP_DB_PATH)
    yield db
    db.close()
    os.remove(TEMP_DB_PATH)
```

## Test Categories

### 1. User Account Tests

**Test Cases:**

- `test_create_account`: Ensures a user account can be successfully created.
- `test_duplicate_account`: Checks that duplicate accounts cannot be created.
- `test_successful_login`: Validates login with correct credentials.
- `test_incorrect_password`: Verifies login failure with incorrect passwords.
- `test_nonexistent_user`: Ensures login attempts with non-existent users fail.
- `test_empty_username`: Tests account creation with an empty username.
- `test_empty_password`: Tests account creation with an empty password.
- `test_special_characters_username`: Ensures accounts with special character usernames can be created.

### 2. Conversation Tests

**Test Cases:**

- `test_create_conversation`: Validates conversation creation between two users.
- `test_duplicate_conversation`: Ensures duplicate conversations are not allowed.
- `test_conversation_with_nonexistent_user`: Prevents conversations with non-existent users.
- `test_conversation_with_self`: Ensures self-conversations are disallowed.

### 3. Message Tests

**Test Cases:**

- `test_send_message`: Checks if users can send messages after creating a conversation.
- `test_send_message_creates_conversation`: Ensures a conversation is auto-created if it does not exist.
- `test_send_message_to_nonexistent_user`: Prevents sending messages to a non-existent user.
- `test_send_empty_message`: Ensures empty messages are not allowed.
- `test_fetch_messages`: Validates retrieval of messages.
- `test_fetch_no_messages`: Checks for proper behavior when no messages exist.

### 4. Message Deletion Tests

**Test Cases:**

- `test_delete_message`: Ensures successful deletion of a message.
- `test_delete_nonexistent_message`: Verifies handling of invalid message deletion attempts.
- `test_delete_last_message_deletes_conversation`: Ensures that deleting the last message removes the conversation.

### 5. Security & Edge Case Tests

**Test Cases:**

- `test_sql_injection`: Checks resilience against SQL injection attempts.
- `test_concurrent_access`: Simulates concurrent messaging to validate database integrity.
- `test_database_cleanup`: Ensures the database can be properly closed and reopened.

### 6. Account Deletion Tests

**Test Cases:**

- Delete an account successfully
- Prevent deletion of nonexistent accounts
- Ensure deleting an account removes conversations

### 7. Advanced Message Tests

**Test Cases:**

- Prevent sending messages with invalid sender/receiver
- Bulk message deletion test

### 8. Message Retrieval Tests

**Test Cases:**

- Ensure ordering of fetched messages (latest first)
- Ensure message retrieval respects limits

### 9. Edge Cases

**Test Cases:**

- Fetch messages from an empty database
- Handle messages containing special characters
- Database cleanup verification

## Sample Test Implementation

```python
def test_create_account(test_db):
    assert test_db.create_account("test_user", "hashed_password") == True

def test_duplicate_account(test_db):
    test_db.create_account("duplicate_user", "password")
    assert test_db.create_account("duplicate_user", "password") == False

def test_successful_login(test_db):
    test_db.create_account("login_user", "correct_hash")
    assert test_db.login_account("login_user", "correct_hash") == True
```

This expanded test documentation ensures thorough verification of `AccountDatabase` functionalities, covering both common and edge cases.

## [Client-Server Integration Test Suite Documentation]

## Overview

This document outlines the test suite for the **client-server** integration tests found in `client_server_unittest.py`. The primary goal is to verify that the client (implemented in `client.py`) correctly interacts with the server by creating accounts, logging in, sending/receiving messages, and handling errors or invalid inputs as expected.

The test suite ensures that:

- Valid account credentials successfully create and authenticate users.
- Messages are correctly sent, fetched, and deleted.
- Error-handling logic correctly responds to invalid user actions (e.g., duplicate users, wrong passwords, non-existent users).

## Prerequisites
Ensure that the server is online and the intermediary database is reset to a clean slate:
```sh
rm <intermediary_db>.py
python3 server.py
```

## Test Setup

1. **Pytest Fixture**:  
   - `setup_client` (scope="module"):  
     Creates a `Client` instance.
     - Asserts that the client successfully connects to the server.
     - Tears down the client after all tests in the module complete.

2. **Utility Functions**:  
   - `process_queue_headless(setup_client, poll_queue=False, timeout=2)`  
     Pops messages off a `server_message_queue` to confirm server responses.  
     Returns `True` if **no** messages contain an error code, otherwise `False`.
   - `wait_for_condition(condition_func, timeout=2)`  
     Polls a condition until it becomes `True` or times out.  
     Used extensively to wait for server responses.
   - `check_condition(queue_list)`  
     Debug utility to print queued messages (used internally).

## Dependencies

- **pytest**: for running the test functions.
- **time**: used in `wait_for_condition`.
- **hashlib**: for hashing passwords (SHA-256).
- **queue**: for message queuing and synchronization.
- **client.py**: the client implementation that interfaces with the server.

## Test Categories

### 1. Account Management Tests

1. **`test_create_account`**  
   Verifies account creation with a valid username and hashed password.  
   - Creates `"testuser"` and `"recipientuser"` with a SHA-256-hashed password.  
   - Asserts the server successfully processes the creation.

2. **`test_delete_account`**  
   Ensures that an existing account can be deleted.  
   - Deletes `"testuser"` and checks the server response.

3. **`test_create_duplicate_account`**  
   Ensures an error is returned when trying to create a user that already exists.  
   - Creates `"duplicateuser"`, then attempts to create `"duplicateuser"` again.  
   - Expects an error message from the server.

4. **`test_delete_account_that_does_not_exist`**  
   Verifies that attempting to delete a non-existent account returns an error.  

### 2. Authentication Tests

1. **`test_login_account`**  
   Verifies login for an existing user with the correct hashed password.

2. **`test_login_with_wrong_password`**  
   Checks that the server returns an error for a valid user with an incorrect password.  

3. **`test_login_repeatedly_in_loop`**  
   Tests logging into the same account multiple times in quick succession to check server stability.

### 3. Messaging Tests

1. **`test_send_message`**  
   Validates sending text messages between two users.  
   - Sends multiple messages from `"testuser"` to `"recipientuser"` and vice versa.

2. **`test_fetch_messages`**  
   Confirms that a user can fetch the last N messages.  

3. **`test_delete_text_message`**  
   Ensures a message can be deleted by its ID.  
   - Verifies server response to confirm deletion.

4. **`test_send_message_to_non_existent_user`**  
   Ensures sending a message to a non-existent user fails with an error.

5. **`test_fetch_messages_for_non_existent_user`**  
   Checks that fetching messages for a non-existent user returns a “no messages” response or equivalent.

6. **`test_delete_non_existent_message`**  
   Verifies an error is returned if a client attempts to delete a message that does not exist.

### 4. Additional Flow Tests

1. **`test_multiple_users_sending_to_one_recipient`**  
   Tests how the server handles multiple senders sending messages to a single recipient (`"massRecipient"`).

2. **`test_send_messages_different_pairs`**  
   Sends messages between various user pairs to ensure the server handles parallel messaging correctly.

3. **`test_delete_multiple_accounts_in_loop`**  
   Creates and deletes multiple accounts in a loop to verify server stability and cleanup.

4. **`test_create_and_delete_same_user_rapidly`**  
   Continuously creates and deletes the same user (`"rapid_cycle"`) to test robustness under rapid changes.

# Running the Test Suites

To run the test suites, navigate to the directory containing `<test_suite>.py` and execute:
```sh
pytest <test_suite>.py
```
