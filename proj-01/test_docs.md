# Account Database Test Suite Documentation

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

## Running the Tests

To execute the test suite, run the following command in the project directory:

```sh
pytest
```

To run specific tests:

```sh
pytest -k "test_name"
```

## Conclusion

This test suite provides comprehensive coverage for account management, messaging, and database security. Ensuring all tests pass guarantees the reliability and robustness of the `AccountDatabase` implementation.
