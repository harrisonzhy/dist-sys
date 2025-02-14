# AccountDatabase Class Documentation

## Overview

The `AccountDatabase` class provides functionality for managing user accounts, conversations, and messages in a SQLite database. It supports user authentication, conversation management, and message handling in a thread-safe manner.

## Initialization

### `__init__(self, db_name)`

Initializes the `AccountDatabase` with the specified database name.

**Parameters:**

- `db_name` (str): The name of the SQLite database file.

**Usage:**

```python
db = AccountDatabase("chat_database.db")
```

### `init_db(self)`

Creates the necessary tables (`users`, `conversations`, `messages`) if they do not exist.

## Database Connection

### `get_conn(self)`

Returns a thread-local SQLite connection.

**Returns:**

- `sqlite3.Connection`: SQLite connection object.

## User Management

### `create_account(self, username: str, hashed_password: str) -> bool`

Creates a new user account.

**Parameters:**

- `username` (str): Unique username.
- `hashed_password` (str): Hashed password.

**Returns:**

- `True` if account creation is successful.
- `False` if username already exists or invalid input is given.

### `login_account(self, username: str, hashed_password: str) -> bool`

Authenticates a user based on username and password.

**Parameters:**

- `username` (str): Username.
- `hashed_password` (str): Hashed password.

**Returns:**

- `True` if login is successful.
- `False` otherwise.

### `delete_account(self, username: str) -> bool`

Deletes a user account and all associated conversations and messages.

**Parameters:**

- `username` (str): Username of the account to delete.

**Returns:**

- `True` if deletion is successful.
- `False` if the user does not exist.

## Conversation Management

### `create_conversation(self, username_1: str, username_2: str) -> bool`

Creates a conversation between two users.

**Parameters:**

- `username_1` (str): First user.
- `username_2` (str): Second user.

**Returns:**

- `True` if the conversation is successfully created.
- `False` if the users are the same or already have a conversation.

## Messaging

### `send_text_message(self, username_1: str, username_2: str, message_text: str) -> bool`

Sends a message from one user to another.

**Parameters:**

- `username_1` (str): Sender.
- `username_2` (str): Receiver.
- `message_text` (str): Message content.

**Returns:**

- `True` if message is sent successfully.
- `False` if message is empty or conversation creation fails.

### `fetch_text_messages(self, username_1: str, k: int) -> list[str]`

Retrieves the `k` most recent messages involving a user.

**Parameters:**

- `username_1` (str): Username.
- `k` (int): Number of messages to fetch.

**Returns:**

- List of messages as strings in the format `message_id|sender|receiver|text`.

### `delete_text_message(self, message_id: int) -> bool`

Deletes a message and removes the conversation if it becomes empty.

**Parameters:**

- `message_id` (int): ID of the message to delete.

**Returns:**

- `True` if the message is deleted.
- `False` if the message is not found.

## Cleanup

### `close(self)`

Closes the SQLite connection for the current thread.

## Thread Safety

The class uses `threading.local()` for thread-local database connections and `threading.Lock()` to ensure thread-safe database modifications.
