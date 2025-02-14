# AccountDatabase Test Documentation

## Overview

This document describes the test suite for the `AccountDatabase` class. The suite ensures the correctness, reliability, and security of user account management, conversation handling, message exchange, and database integrity.

## Setup and Initialization

### Test Database Setup

A temporary SQLite database file is used for testing to ensure data integrity and isolation.

```python
import multiprocessing
import tempfile
import os
from db import AccountDatabase
import pytest

TEMP_DB_PATH = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name  

@pytest.fixture(scope="session")
def test_db():
    """Fixture to initialize and clean up a file-based test database for multiprocessing support."""
    db = AccountDatabase(TEMP_DB_PATH)
    yield db
    db.close()
    os.remove(TEMP_DB_PATH)
```

## Test Categories

### 1. User Account Tests

- **Create an account**
- **Prevent duplicate account creation**
- **Successful login**
- **Incorrect password login attempt**
- **Nonexistent user login attempt**
- **Empty username or password rejection**
- **Allow special characters in usernames**

### 2. Conversation Management Tests

- **Create a conversation between users**
- **Prevent duplicate conversation creation**
- **Prevent conversation with nonexistent users**
- **Prevent self-conversation**

### 3. Message Handling Tests

- **Send a message successfully**
- **Auto-create conversation when sending a message**
- **Prevent sending a message to a nonexistent user**
- **Prevent empty messages**
- **Retrieve messages in the correct order**
- **Handle retrieval when no messages exist**

### 4. Message Deletion Tests

- **Delete a specific message**
- **Prevent deletion of nonexistent messages**
- **Delete the last message should remove conversation**

### 5. Security and Edge Cases

- **Prevent SQL injection attacks**
- **Ensure concurrent access integrity**

### 6. Account Deletion Tests

- **Delete an account successfully**
- **Prevent deletion of nonexistent accounts**
- **Ensure deleting an account removes conversations**

### 7. Advanced Message Tests

- **Prevent sending messages with invalid sender/receiver**
- **Bulk message deletion test**

### 8. Message Retrieval Tests

- **Ensure ordering of fetched messages (latest first)**
- **Ensure message retrieval respects limits**

### 9. Edge Cases

- **Fetch messages from an empty database**
- **Handle messages containing special characters**
- **Database cleanup verification**

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