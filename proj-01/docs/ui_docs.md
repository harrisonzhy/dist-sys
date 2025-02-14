# UI Documentation

## Components

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
