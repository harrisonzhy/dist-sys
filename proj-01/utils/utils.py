import configparser

class Config:
    def __init__(self, config_file="config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_server_config(self):
        """Returns server configuration as a dictionary."""
        return {
            "host": self.config.get("SERVER", "host"),
            "port": self.config.getint("SERVER", "port"),
        }

    def get_client_config(self):
        """Returns client configuration as a dictionary."""
        return {
            "host": self.config.get("CLIENT", "host"),
            "port": self.config.getint("CLIENT", "port"),
        }

    def get_account_db(self):
        """Returns account database file name."""
        return self.config.get("ACCOUNT", "db_name")

    def get_msg_magic(self):
        """Returns message magic string."""
        return self.config.get("MESSAGE", "msg_magic") 
    
    def get_msg_magic_size(self):
        """Returns message magic string size."""
        return int(self.config.get("MESSAGE", "msg_magic_size"))
    
    def get_msg_type_size(self):
        """Returns message type size."""
        return int(self.config.get("MESSAGE", "msg_type_size"))
     
    def get_msg_max_size(self):
        """Returns message maximum size."""
        return int(self.config.get("MESSAGE", "msg_max_size")) 

class Message:
    """
    Handles message creation and parsing.
    Structure: [Magic (8)] [Message Type (8)] [Content (0-1000)] [Magic (8)]
    """

    # Constructor for sending messages
    def __init__(self, message_content: str, message_type: str, endpoint):
        self.endpoint = endpoint
        self.message_type = message_type
        self.message_valid = False
        self.message = None

        assert len(self.message_type) == self.endpoint.msg_type_size, "Invalid message type size"

        if self.endpoint.msg_min_size + len(message_content) <= self.endpoint.msg_max_size:
            self.message_content = message_content
            self.message = (
                self.endpoint.msg_magic +
                self.message_type +
                self.message_content +
                self.endpoint.msg_magic
            )
            self.message_valid = True
        else:
            self.message_valid = False

    # Alternative constructor for receiving messages
    @classmethod
    def from_bytes(cls, message_bytes: str, endpoint):
        instance = cls.__new__(cls)
        instance.endpoint = endpoint
        instance.message_valid = False
        instance.message = None

        if endpoint.msg_min_size <= len(message_bytes) <= endpoint.msg_max_size:
            message_header = message_bytes[:endpoint.msg_magic_size]
            message_footer = message_bytes[-endpoint.msg_magic_size:]
            message_type = message_bytes[endpoint.msg_magic_size:endpoint.msg_magic_size + endpoint.msg_type_size]

            if message_header == endpoint.msg_magic and message_footer == endpoint.msg_magic:
                instance.message_type = message_type
                instance.message_content = message_bytes[endpoint.msg_magic_size + endpoint.msg_type_size:-endpoint.msg_magic_size]
                instance.message = message_bytes
                instance.message_valid = True
        return instance
          
    def encode(self):
        return self.message.encode("utf-8")

    def valid(self): 
        return self.message_valid

    def unpack(self):
        if not self.valid():
            return None
        message_type = self.message_type
        message_content = self.message[self.endpoint.msg_magic_size + self.endpoint.msg_type_size:-self.endpoint.msg_magic_size]
        return message_type, message_content