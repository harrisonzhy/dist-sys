
class MessageArgs:
    def __init__(self, *args):
        """Initialize with multiple arguments."""
        for arg in args:
            if "|" in str(arg):
                self.args = ""
                break
        self.args = args

    def to_string(self) -> str:
        """Returns the arguments as a string separated by '|'."""
        return "|".join(map(str, self.args))

    @classmethod
    def to_arglist(cls, arg_string: str):
        """Parses a string separated by '|' and returns an argument list."""
        args = arg_string.split("|")
        return args

class Message:
    """
    Handles message creation and parsing.
    Structure: [Magic (8)] [Message Type (8)] [Content (0-1000)] [Magic (8)]
    """

    def __init__(self, message_args: MessageArgs, message_type: str, endpoint):
        """
        Constructor for sending messages.
        Ensures message validity before storing.
        """
        self.endpoint = endpoint
        self.message_type = ""
        self.message_content = ""
        self.message = ""
        self.message_valid = False

        message_content = message_args.to_string()

        if self.endpoint.msg_min_size + len(message_content) <= self.endpoint.msg_max_size \
            and message_type in self.endpoint.action_handler.inverse_action_map:
            self.message_type = self.endpoint.action_handler.inverse_action_map[message_type]
            self.message_content = message_content
            self.message = (
                self.endpoint.msg_magic +
                self.message_type +
                self.message_content +
                self.endpoint.msg_magic
            )
            self.message_valid = True
        else:
            print("[Message] Invalid size or type.")
            self.message_valid = False

    @classmethod
    def from_bytes(cls, message_bytes: str, endpoint):
        """
        Alternative constructor for receiving messages.
        Validates message integrity before returning an instance.
        """

        instance = cls.__new__(cls)
        instance.endpoint = endpoint
        instance.message_type = ""
        instance.message_content = ""
        instance.message = ""
        instance.message_valid = False

        if not (instance.endpoint.msg_min_size <= len(message_bytes) <= instance.endpoint.msg_max_size):
            instance.message_valid = False
            print("[Message] Invalid size.")
            return instance
        
        message_header = message_bytes[:endpoint.msg_magic_size]
        message_footer = message_bytes[-endpoint.msg_magic_size:]
        if message_header != endpoint.msg_magic or message_footer != endpoint.msg_magic:
            instance.message_valid = False
            print("[Message] Invalid magic values.")
            return instance

        message_type = message_bytes[endpoint.msg_magic_size:endpoint.msg_magic_size + endpoint.msg_type_size]
        # TODO: Check message type
        if message_type not in instance.endpoint.action_handler.action_map:
            instance.message_valid = False
            print("[Message] Invalid type.")
            return instance
        
        message_content = message_bytes[endpoint.msg_magic_size + endpoint.msg_type_size:-endpoint.msg_magic_size]

        instance.message_type = message_type
        instance.message_content = message_content
        instance.message = message_bytes
        instance.message_valid = True

        # print("[Message] Content:", instance.message_content)

        return instance

    def encode(self) -> bytes:
        """Encodes the message into bytes (UTF-8)."""
        return self.message.encode("utf-8")

    def valid(self) -> bool:
        """Returns whether the message is valid."""
        return self.message_valid

    def unpack(self):
        """Unpacks the message into its type and content."""
        if not self.valid():
            return None
        return self.message_type, self.message_content
