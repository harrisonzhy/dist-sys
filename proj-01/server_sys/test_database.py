import pytest
import multiprocessing
from db import AccountDatabase 

@pytest.fixture
def test_db():
    """Fixture to initialize and clean up an in-memory test database."""
    db = AccountDatabase(":memory:")  # Use an in-memory database for testing
    yield db
    db.close()

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

### ---- 2. Conversation Tests ---- ###

def test_create_conversation(test_db):
    test_db.create_account("user1", "pass1")
    test_db.create_account("user2", "pass2")
    assert test_db.create_conversation("user1", "user2") == True

def test_conversation_with_nonexistent_user(test_db):
    test_db.create_account("real_user", "pass")
    assert test_db.create_conversation("real_user", "fake_user") == False

### ---- 3. Message Tests ---- ###

def test_send_message(test_db):
    test_db.create_account("alice", "pass1")
    test_db.create_account("bob", "pass2")
    test_db.create_conversation("alice", "bob")
    assert test_db.send_text_message("alice", "bob", "Hello Bob!") == True

def test_send_message_to_nonexistent_user(test_db):
    test_db.create_account("alice", "pass")
    assert test_db.send_text_message("alice", "unknown_user", "Hello?") == False

def test_fetch_messages(test_db):
    test_db.create_account("alice", "pass1")
    test_db.create_account("bob", "pass2")
    test_db.send_text_message("alice", "bob", "Hello Bob!")
    test_db.send_text_message("bob", "alice", "Hi Alice!")
    assert test_db.fetch_text_messages("alice", "bob", 2) == True

def test_fetch_no_messages(test_db):
    test_db.create_account("user1", "pass1")
    test_db.create_account("user2", "pass2")
    assert test_db.fetch_text_messages("user1", "user2", 5) == False

### ---- 4. Security & Edge Case Tests ---- ###

def test_sql_injection(test_db):
    test_db.create_account("safe_user", "safe_password")
    assert test_db.login_account("safe_user'; --", "irrelevant") == False

def test_concurrent_access(test_db):
    test_db.create_account("multi_user1", "pass1")
    test_db.create_account("multi_user2", "pass2")

    def send_messages():
        for _ in range(10):
            test_db.send_text_message("multi_user1", "multi_user2", "Hello!")

    process1 = multiprocessing.Process(target=send_messages)
    process2 = multiprocessing.Process(target=send_messages)

    process1.start()
    process2.start()
    process1.join()
    process2.join()

    assert test_db.fetch_text_messages("multi_user1", "multi_user2", 1) == True

def test_database_cleanup(test_db):
    test_db.create_account("temp_user", "password")
    test_db.close()
    assert test_db.get_conn() is not None  # Should be able to reopen
