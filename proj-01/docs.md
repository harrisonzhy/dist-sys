# Project Documentation

This document gives a brief overview of the code layout in this repository as well as the underlying client-server architecture.

## Configuration

The `config.ini` file defines host, port, magic values, and constants, and messaging protocol, agreed upon by client and server. It consists of several sections:

#### `[SERVER]`
Defines the server’s **host** and **port**.
- **`host`**  
  Determines the IP address on which the server listens.  
- **`port`**  
  Determines the TCP port on which the server listens.
#### `[CLIENT]`
Defines the client’s **host** and **port**.
- **`host`**  
  Determines the IP address to which the client attempts to connect.  
- **`port`**  
  Determines the TCP port to which the client connects.
#### `[ACCOUNT]`
- **`db_name`**  
  The filename of the database used for account and message storage.  
- **`max_texts`**  
  The maximum number of text messages to store or process in certain operations.
#### `[MESSAGE]`
- **`msg_magic`**  
  A numeric signature used to validate messages.  
- **`msg_magic_size`** and **`msg_type_size`**  
  Sizes (in bytes) reserved for validating the message header.  
- **`msg_max_size`**  
  The maximum allowed payload size for a single message.
#### `[PROTOCOL]`
- **`protocol`**  
  Specifies how messages are serialized. For instance, `json` indicates JSON-based encoding, and `custom` indicates the default custom protocol.
#### `[ACTIONS]`
- **`actions`**  
  Points to `actions.json`, which defines the available actions and how they are routed or handled by both client and server.

## Actions

The `actions` folder contains the implementation for handling client and server actions in the system. It consists of two key files:

### 1. `actions.json`
This file defines the mapping between action codes and their corresponding action names. It provides a reference for handling actions programmatically. For instance, created mappings are of the form:

```
{
    "00000000": "status",
    "00000001": "create_account",
    "00000002": "delete_account",
    "00000003": "login_account",
    "00000004": "logout_account",
    "00000005": "send_text_message",
    "00000006": "fetch_text_messages",
    "00000007": "delete_text_message"
}
```

### 2. `actions.py`
This file implements action handlers for different system components. It defines three main classes inheriting from **BaseActionHandler**:

#### **BaseActionHandler**
- A generic class that loads action mappings from `actions.json`.
- Provides a method (`execute_action`) to dynamically execute mapped functions.
- Maintains both forward and inverse mappings of action codes for standardizing message type representation.

#### **ClientCallbackHandler**
- Handles client-specific callbacks upon receiving a server response.
- Implements functions to update the UI based on received actions (e.g., `create_account`, `send_text_message`).

#### **ClientActionHandler**
- Implements client-side logic to send action requests to the server.
- Constructs messages using the `utils.message` module and sends them via the client's network endpoint.
- Supports actions such as `create_account`, `delete_account`, `login_account`, and `fetch_text_messages`.

#### **ServerActionHandler**
- Implements server-side logic to process incoming client requests.
- Calls database functions (`account_db`) to perform requested actions.
- Handles user authentication, account management, and message processing.

## Database

The `server_sys` folder contains `db.py`, which implements the account database. It manages user accounts, conversations, and messages through SQLite.

### **Database Structure**
#### Tables:
1. **Users**: Stores user credentials.
2. **Conversations**: Tracks conversations between users.
3. **Messages**: Stores messages exchanged within conversations.

### **Key Functions**
#### **Account Management**
- `create_account(username, hashed_password)`: Registers a new user.
- `login_account(username, hashed_password)`: Authenticates user credentials.

#### **Conversations**
- `create_conversation(username_1, username_2)`: Initializes a chat between two users.

#### **Messaging**
- `send_text_message(username_1, username_2, message_text)`: Sends a message in an existing or new conversation.
- `fetch_text_messages(username, k)`: Retrieves the last `k` messages for a user.

## Testing
The `test_database.py` script uses `pytest` to validate the database functionality.

### **Test Cases**
- **User Account Tests**: Verify account creation, login, and duplicate user handling.
- **Conversation Tests**: Ensure conversations are created and handled properly.
- **Message Tests**: Test sending and retrieving messages.
- **Concurrency Tests**: Ensure correct concurrent access handling.

The `test_db.py` script provides a way to inspect the SQLite database contents for debugging. It prints out all tables and their data for verification.

## Server-Client Architecture

- **Server**:
  - Listens for incoming client connections on a configured host and port.
  - For each connected client, spawns threads to receive messages and queue them for processing.
  - Executes server-side actions based on message types and sends responses back to the client.
  
- **Client**:
  - Connects to the server on a configured host and port.
  - Sends messages (wrapped in a `Message` object) to the server.
  - Receives responses from the server and processes them with client-specific callbacks.

**Data Flow**:
1. **Client** sends a message to the **Server** with a specific message type and arguments.
2. **Server** receives the message, determines the appropriate server-side action, and executes it.
3. **Server** sends a response (which may be one or more messages) back to the **Client**.
4. **Client** processes the response, possibly updating a user interface or performing additional logic.


### Server Components

- **Server** defined in `server.py` orchestrates the entire server lifecycle: accepts connections, reads messages from clients, delegates actions, and returns results back to clients.

**Key Attributes**:
- `host`, `port`: Network details for binding and listening.
- `server_socket`: The main socket that listens for new client connections.
- `client_message_queues`: A dictionary mapping each connected `client_socket` to a `queue.Queue` object containing unprocessed messages.
- `executor`: A `ThreadPoolExecutor` used to run action-related tasks (to avoid blocking the main server loop).
- `action_handler`: An instance of `ServerActionHandler` (from `actions/actions.py`) used to handle server-side actions, like account creation or message forwarding.
- `account_db`: An instance of `db.AccountDatabase` for managing user accounts.

#### Key Methods

1. **`__init__()`**  
   - Initializes server configurations (host, port, DB paths, etc.).
   - Prepares the server socket.
   - Starts the main loop by calling `start()`.

2. **`start()`**  
   - Binds the server socket to the specified host/port and listens for new connections.
   - When a client connects:
     - Creates a dedicated message queue for that client.
     - Spawns:
       - **`recv_client_message(...)`**: continuously receives messages from that client socket.
       - **`process_queued_messages(...)`**: pulls messages from the per-client queue and passes them to the thread pool for processing.

3. **`recv_client_message(client_socket, addr)`**  
   - Reads a 4-byte length header to determine the incoming message size.
   - Reads the message payload based on that length.
   - Decodes the message into a `Message` object.
   - Validates the message; if valid, places it in the client’s message queue.

4. **`process_queued_messages(client_socket)`**  
   - Runs in a loop while the client is connected.
   - Fetches messages from the client’s queue.
   - Submits each message to the thread pool by calling `perform_action(...)`.

5. **`perform_action(message_type, message_args, client_socket)`**  
   - Invokes `action_handler.execute_action(...)` to handle the given `message_type`.
   - Sends the result(s) back to the client using `send_client_message(...)`.

6. **`send_client_message(client_socket, message)`**  
   - Encodes the `Message` and sends a length header followed by the message payload to the client socket.

### Client Components

**Client** defined in `client.py` defines the client’s connection to the server, including sending messages and handling server responses. It also provides a way to integrate UI callbacks (e.g., for updating a GUI output).

**Key Attributes**:
- `host`, `port`: Configured to match the server’s connection details.
- `client_socket`: Socket object for maintaining the client connection.
- `connected`: Flag indicating whether the client is currently connected.
- `server_message_queue`: A queue storing messages received from the server.
- `action_handler`: A `ClientActionHandler` that executes logic on the client side (often minimal).
- `callback_handler`: A `ClientCallbackHandler` that integrates with UI callbacks.
- `executor`: A `ThreadPoolExecutor` for processing messages from the server.

#### Key Methods

1. **`__init__(ui_callback)`**  
   - Sets up client configuration (host, port) from `config.Config()`.
   - Initializes the client socket and attempts to connect to the server.
   - Spawns threads for receiving server messages (`recv_server_message`) and processing them from a queue.

2. **`connect()`**  
   - Connects to the server socket using the provided `host` and `port`.
   - If successful, starts threads for `recv_server_message` and `process_queued_messages`.

3. **`recv_server_message()`**  
   - Continuously reads messages sent by the server.
   - Each message is decoded into a `Message` object and validated.
   - Pushes valid messages onto `server_message_queue`.

4. **`send_server_message(message)`**  
   - Sends a `Message` object to the server (length header plus JSON- or custom-encoded data).
   - Handles exceptions gracefully and disconnects if the server is unreachable.

5. **`process_queued_messages()`**  
   - Serially processes messages from `server_message_queue`.
   - For each message, calls `perform_callback(...)` on the `ClientCallbackHandler`.

6. **`disconnect()`**  
   - Closes the client socket and marks `connected` as `False`.

## Supporting Modules

### `utils/message.py`
- **`Message`** class encapsulates a message’s structure: a “magic” prefix for validation, a message type, and the serialized content.  
- Provides:
  - `encode()`: Converts the message into a parsable string.
  - `decode() / from_bytes()`: Reconstructs a message from raw byte data.
  - `valid()`: Validates that required fields (magic prefix, type) exist.

### `utils/config.py`
- **`Config`** class retrieves user-defined or default settings (e.g. host/port, database file paths, etc.).
- Example usage:
  ```python
  CFG = config.Config()
  server_host = CFG.get_server_config()['host']
  ```
### `utils/utils.py`
- `recv_all(socket, n)` is a helper function to poll until all specified `n` bytes are read from the `socket`.

## UI Documentation

The below provides an overview of the implementation of the MessagingApp, a Tkinter-based messaging application. It describes the structure, UI components, and key functionalities of the application.

The MessagingApp is a graphical user interface (GUI) application built with Tkinter that allows users to log in, send messages, and manage their accounts. The application maintains session state and updates the UI dynamically based on user interactions.

## Configuration

The application initializes with a session state that maintains authentication, messaging, and account-related statuses. Key session state parameters include:

- `logged_in`: Boolean flag indicating login status.
- `username`: Stores the current logged-in username.
- `texts`: Dictionary storing messages per counterparty.
- `max_texts`: Maximum number of texts per sender.
- `current_page`: Tracks the current UI page (e.g., 'auth', 'main', 'settings').
- `auth_status`, `account_status`, `message_status`: Flags indicating the success or failure of various actions.

## UI Components

### 1. Authentication UI

The authentication UI is displayed when a user is not logged in. It includes:

- Username and password entry fields.
- Buttons for creating an account and logging in.
- Status messages for authentication and account creation results.

### 2. Main UI

Upon successful login, the main messaging UI is displayed, containing:

- A welcome message with the logged-in username.
- Buttons for navigating to settings, logging out, and deleting the account.
- Messaging functionalities: sending messages and viewing inbox messages.

### 3. Settings UI

The settings page allows users to adjust message-related preferences:

- Modify the maximum number of texts per sender using a spinbox.
- Save settings and return to the main UI.

### 4. Send Message UI

Users can send messages by:

- Entering the recipient's username.
- Typing the message content.
- Clicking the 'Send' button.
- Receiving feedback on the message status (sent successfully or recipient does not exist).

### 5. Inbox UI

Displays received and sent messages in a chat-style format:

- Messages are shown in aligned chat bubbles (left for received, right for sent).
- Each message has a delete button for removal.
- A filter entry field allows users to search messages by counterparty.
- A refresh button updates the inbox with new messages.

## Functionalities

### 1. User Authentication

#### `handle_login()`
- Hashes the password using SHA-256.
- Calls `action_handler.login_account()` to authenticate the user.
- Updates session state and UI upon successful login.

#### `handle_create_account()`
- Hashes the password using SHA-256.
- Calls `action_handler.create_account()` to create a new user account.
- Displays status messages based on the account creation result.

### 2. Settings Management

#### `save_settings()`
- Updates the `max_texts` setting and displays a confirmation message.

### 3. Messaging System

#### `send_message()`
- Retrieves recipient and message text input.
- Calls `action_handler.send_text_message()` to send the message.
- Refreshes the UI after sending.

#### `update_inbox()`
- Clears previous messages and reloads them in a chat-like format.
- Displays messages with delete buttons aligned by sender status.

#### `delete_message(counterparty, message_id)`
- Removes a message from session storage.
- Calls `action_handler.delete_text_message()` to delete it from the backend.
- Refreshes the inbox UI.

#### `refresh_inbox()`
- Fetches new messages from the server using `action_handler.fetch_text_messages()`.
- Updates the UI after retrieving new messages.

### 4. Account Management

#### `logout()`
- Resets session state.
- Redirects the user to the authentication UI.

#### `delete_account()`
- Calls `action_handler.delete_account()` to remove the user account.
- Displays a confirmation message.
- Logs out the user and resets session state.

## Client-Server Interaction

The application interacts with the backend through `action_handler`, which performs the following operations:

- `login_account(username, password)`: Handles user authentication.
- `create_account(username, password)`: Registers a new user.
- `send_text_message(sender, recipient, text)`: Sends messages between users.
- `fetch_text_messages(username, max_texts)`: Retrieves messages for the user.
- `delete_text_message(message_id)`: Deletes a message from the system.
- `delete_account(username)`: Removes a user account.

## Conclusion

This documentation provides an overview of the MessagingApp, describing its UI structure, functionalities, and interaction with backend services. The application ensures seamless user authentication, messaging, and account management within a simple and intuitive interface.

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
