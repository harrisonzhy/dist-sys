import multiprocessing
import tempfile
import os
import pytest

from db import AccountDatabase

def send_messages(db_path):
    """Each process should create its own connection to the database."""
    test_db = AccountDatabase(db_path)  # New connection for each process
    for _ in range(10):
        test_db.send_text_message("multi_user1", "multi_user2", "Hello!")
    test_db.close()

TEMP_DB_PATH = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name  

@pytest.fixture(scope="session")
def test_db():
    """Fixture to initialize and clean up a file-based test database for multiprocessing support."""
    db = AccountDatabase(TEMP_DB_PATH)  # Use file-based database
    yield db
    db.close()
    os.remove(TEMP_DB_PATH)  # Cleanup after tests

### ---- 1. User Account Tests ---- ###

def test_create_account(test_db):
    assert test_db.create_account("test_user", "hashed_password") == True

def test_duplicate_account(test_db):
    test_db.create_account("duplicate_user", "password")
    assert test_db.create_account("duplicate_user", "password") == False

def test_successful_login(test_db):
    test_db.create_account("login_user", "correct_hash")
    assert test_db.login_account("login_user", "correct_hash") == True

def test_incorrect_password(test_db):
    test_db.create_account("secure_user", "secure_hash")
    assert test_db.login_account("secure_user", "wrong_hash") == False

def test_nonexistent_user(test_db):
    assert test_db.login_account("nonexistent", "random_hash") == False

def test_empty_username(test_db):
    assert test_db.create_account("", "password") == False

def test_empty_password(test_db):
    assert test_db.create_account("user_no_pass", "") == False

def test_special_characters_username(test_db):
    assert test_db.create_account("user@name", "secure_pass") == True

### ---- 2. Conversation Tests ---- ###

def test_create_conversation(test_db):
    test_db.create_account("user1", "pass1")
    test_db.create_account("user2", "pass2")
    assert test_db.create_conversation("user1", "user2") == True

def test_duplicate_conversation(test_db):
    test_db.create_account("userA", "passA")
    test_db.create_account("userB", "passB")
    test_db.create_conversation("userA", "userB")
    assert test_db.create_conversation("userA", "userB") == False  # Conversation should not be duplicated

def test_conversation_with_nonexistent_user(test_db):
    test_db.create_account("real_user", "pass")
    assert test_db.create_conversation("real_user", "fake_user") == False

def test_conversation_with_self(test_db):
    test_db.create_account("self_user", "pass")
    assert test_db.create_conversation("self_user", "self_user") == False  # Should not allow self-chat

### ---- 3. Message Tests ---- ###

def test_send_message(test_db):
    test_db.create_account("alice", "pass1")
    test_db.create_account("bob", "pass2")
    test_db.create_conversation("alice", "bob")
    assert test_db.send_text_message("alice", "bob", "Hello Bob!") == True

def test_send_message_creates_conversation(test_db):
    test_db.create_account("alice", "pass1")
    test_db.create_account("bob", "pass2")
    assert test_db.send_text_message("alice", "bob", "Hello Bob!") == True  # Should auto-create conversation

def test_send_message_to_nonexistent_user(test_db):
    test_db.create_account("alice", "pass")
    assert test_db.send_text_message("alice", "unknown_user", "Hello?") == False

def test_send_empty_message(test_db):
    test_db.create_account("alice", "pass")
    test_db.create_account("bob", "pass")
    test_db.create_conversation("alice", "bob")
    assert test_db.send_text_message("alice", "bob", "") == False  # Should not allow empty messages

def test_fetch_messages(test_db):
    test_db.create_account("alice", "pass1")
    test_db.create_account("bob", "pass2")
    test_db.send_text_message("alice", "bob", "Hello Bob!")
    test_db.send_text_message("bob", "alice", "Hi Alice!")
    messages = test_db.fetch_text_messages("alice", 2)
    assert len(messages) == 2  # Should return both messages

def test_fetch_no_messages(test_db):
    test_db.create_account("user1", "pass1")
    test_db.create_account("user2", "pass2")
    messages = test_db.fetch_text_messages("user1", 5)
    assert messages == [''] or messages == ['|||']  # Should return empty list

### ---- 4. Message Deletion Tests ---- ###

def test_delete_message(test_db):
    test_db.create_account("alice", "pass1")
    test_db.create_account("bob", "pass2")
    test_db.send_text_message("alice", "bob", "This is a test message")
    messages = test_db.fetch_text_messages("alice", 1)
    
    message_id = int(messages[0].split('|')[0])  # Extract message ID
    assert test_db.delete_text_message(message_id) == True

def test_delete_nonexistent_message(test_db):
    assert test_db.delete_text_message(99999) == False  # Message ID doesn't exist

def test_delete_last_message_deletes_conversation(test_db):
    test_db.create_account("daniel", "pass1")
    test_db.create_account("ron", "pass2")
    test_db.send_text_message("daniel", "ron", "Only message")
    messages = test_db.fetch_text_messages("daniel", 1)
    
    message_id = int(messages[0].split('|')[0])
    test_db.delete_text_message(message_id)

    messages_after = test_db.fetch_text_messages("daniel", 1)
    assert messages_after == [''] or messages_after == ['|||']  # Should return empty list

### ---- 5. Security & Edge Case Tests ---- ###

def test_sql_injection(test_db):
    test_db.create_account("safe_user", "safe_password")
    assert test_db.login_account("safe_user'; --", "irrelevant") == False

def test_concurrent_access(test_db):
    """Test concurrent access by multiple processes sending messages."""
    test_db.create_account("multi_user1", "pass1")
    test_db.create_account("multi_user2", "pass2")

    process1 = multiprocessing.Process(target=send_messages, args=(TEMP_DB_PATH,))
    process2 = multiprocessing.Process(target=send_messages, args=(TEMP_DB_PATH,))

    process1.start()
    process2.start()
    process1.join()
    process2.join()

    messages = test_db.fetch_text_messages("multi_user1", 20)
    assert len(messages) == 20  # Expecting exactly 20 messages from concurrent writes

### ---- 6. Account Deletion Tests ---- ###

def test_delete_account(test_db):
    test_db.create_account("delete_me", "password")
    assert test_db.delete_account("delete_me") == True  # Account should be deleted
    assert test_db.login_account("delete_me", "password") == False  # Login should fail

def test_delete_nonexistent_account(test_db):
    assert test_db.delete_account("ghost_user") == False  # Should fail

def test_delete_account_removes_conversations(test_db):
    test_db.create_account("rohan", "pass")
    test_db.create_account("rachna", "pass")
    test_db.create_conversation("rohan", "rachna")
    assert test_db.delete_account("rohan") == True  # Should delete account and conversation
    assert test_db.create_conversation("rohan", "rachna") == False  

# ### ---- 7. Advanced Message Tests ---- ###

def test_send_message_invalid_data(test_db):
    test_db.create_account("charlie", "pass")
    assert test_db.send_text_message("charlie", "", "Hello") == False  # Invalid receiver
    assert test_db.send_text_message("", "charlie", "Hello") == False  # Invalid sender
    assert test_db.send_text_message("charlie", "nonexistent", "Hello") == False  # Receiver does not exist

def test_delete_multiple_messages(test_db):
    test_db.create_account("dan", "pass")
    test_db.create_account("eve", "pass")
    test_db.create_conversation("dan", "eve")
    
    test_db.send_text_message("dan", "eve", "Message 1")
    test_db.send_text_message("eve", "dan", "Message 2")
    test_db.send_text_message("dan", "eve", "Message 3")
    
    messages = test_db.fetch_text_messages("dan", 10)
    
    message_ids = [int(msg.split('|')[0]) for msg in messages]
    for msg_id in message_ids:
        test_db.delete_text_message(msg_id)
    
    fetched = test_db.fetch_text_messages("dan", 10)
    assert fetched == [''] or fetched == ['|||']  # No messages should be left

# ### ---- 8. Ordering & Limits Tests ---- ###

def test_fetch_messages_ordering(test_db):
    test_db.create_account("frank", "pass")
    test_db.create_account("grace", "pass")
    test_db.create_conversation("frank", "grace")
    
    test_db.send_text_message("frank", "grace", "First Message")
    test_db.send_text_message("frank", "grace", "Second Message")
    test_db.send_text_message("grace", "frank", "Third Message")
    
    messages = test_db.fetch_text_messages("frank", 3)
    
    assert "Third Message" in messages[0]  # Most recent first
    assert "Second Message" in messages[1]
    assert "First Message" in messages[2]

def test_fetch_messages_limit(test_db):
    test_db.create_account("henry", "pass")
    test_db.create_account("isla", "pass")
    test_db.create_conversation("henry", "isla")
    
    for i in range(10):
        test_db.send_text_message("henry", "isla", f"Message {i}")
    
    messages = test_db.fetch_text_messages("henry", 5)
    assert len(messages) == 5  # Should return exactly 5 messages

# ### ---- 9. Edge Cases ---- ###

def test_empty_database_fetch(test_db):
    fetched = test_db.fetch_text_messages("empty_user", 5)
    assert fetched == [''] or fetched == ['|||']  # No messages should be left

def test_special_character_messages(test_db):
    test_db.create_account("joker", "pass")
    test_db.create_account("batman", "pass")
    test_db.create_conversation("joker", "batman")
    
    special_message = "Hello! @#$%^&*()_+"  # Message with special characters
    assert test_db.send_text_message("joker", "batman", special_message) == True
    messages = test_db.fetch_text_messages("joker", 1)
    assert special_message in messages[0]  # Message should be retrievable correctly

def test_database_cleanup(test_db):
    test_db.create_account("temp_user", "password")
    test_db.close()
    assert test_db.get_conn() is not None  # Should be able to reopen
