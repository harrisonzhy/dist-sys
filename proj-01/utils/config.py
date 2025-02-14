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
    
    def get_actions_dict(self):
        """Returns actions dictionary file name."""
        return self.config.get("ACTIONS", "actions")
