import pytest
from unittest.mock import Mock
from your_module import MessageArgs, Message  # Replace 'your_module' with the actual module name

# Test cases for MessageArgs
def test_message_args_initialization():
    args = MessageArgs("hello", "world")
    assert args.args == ("hello", "world")

def test_message_args_with_pipe():
    args = MessageArgs("hello|world")
    assert args.args == ""

def test_message_args_to_string():
    args = MessageArgs("foo", "bar", "baz")
    assert args.to_string() == "foo|bar|baz"

def test_message_args_to_string_empty():
    args = MessageArgs()
    assert args.to_string() == ""

def test_message_args_to_arglist():
    arg_string = "one|two|three"
    assert MessageArgs.to_arglist(arg_string) == ["one", "two", "three"]

def test_message_args_to_arglist_empty():
    assert MessageArgs.to_arglist("") == [""]

# Mock setup for Message tests
@pytest.fixture
def mock_endpoint():
    mock = Mock()
    mock.msg_min_size = 8
    mock.msg_max_size = 100
    mock.msg_magic_size = 8
    mock.msg_type_size = 8
    mock.msg_magic = "MAGIC123"
    
    # Mock action handler
    mock.action_handler = Mock()
    mock.action_handler.action_map = {"TYPE1": "TYPE1"}
    mock.action_handler.inverse_action_map = {"TYPE1": "TYPE1"}
    
    return mock

# Test cases for Message
def test_message_valid(mock_endpoint):
    args = MessageArgs("data1", "data2")
    message = Message(args, "TYPE1", mock_endpoint)
    
    assert message.valid()
    assert message.message_type == "TYPE1"
    assert message.message_content == "data1|data2"
    assert message.message == f"MAGIC123TYPE1data1|data2MAGIC123"

def test_message_invalid_size(mock_endpoint):
    mock_endpoint.msg_max_size = 10  # Too small to fit content

    args = MessageArgs("data1", "data2", "extra")
    message = Message(args, "TYPE1", mock_endpoint)

    assert not message.valid()

def test_message_invalid_type(mock_endpoint):
    args = MessageArgs("data1")
    message = Message(args, "INVALID_TYPE", mock_endpoint)

    assert not message.valid()

def test_message_from_bytes_valid(mock_endpoint):
    valid_message = "MAGIC123TYPE1data1|data2MAGIC123"
    message = Message.from_bytes(valid_message, mock_endpoint)

    assert message.valid()
    assert message.message_type == "TYPE1"
    assert message.message_content == "data1|data2"

def test_message_from_bytes_invalid_magic(mock_endpoint):
    invalid_message = "WRONG123TYPE1data1|data2MAGIC123"
    message = Message.from_bytes(invalid_message, mock_endpoint)

    assert not message.valid()

def test_message_from_bytes_invalid_size(mock_endpoint):
    short_message = "SHORT"
    message = Message.from_bytes(short_message, mock_endpoint)

    assert not message.valid()

def test_message_from_bytes_invalid_type(mock_endpoint):
    invalid_message = "MAGIC123INVALIDdataMAGIC123"
    message = Message.from_bytes(invalid_message, mock_endpoint)

    assert not message.valid()

def test_message_encode(mock_endpoint):
    args = MessageArgs("hello", "world")
    message = Message(args, "TYPE1", mock_endpoint)

    assert message.encode() == b"MAGIC123TYPE1hello|worldMAGIC123"

def test_message_unpack(mock_endpoint):
    args = MessageArgs("some", "data")
    message = Message(args, "TYPE1", mock_endpoint)

    assert message.unpack() == ("TYPE1", "some|data")

def test_message_unpack_invalid(mock_endpoint):
    args = MessageArgs("invalid")
    message = Message(args, "INVALID_TYPE", mock_endpoint)

    assert message.unpack() is None