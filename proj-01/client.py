import socket
import threading
import hashlib as hasher
import queue
from concurrent.futures import ThreadPoolExecutor

from utils import message as MSG
from utils import config
from utils import utils
from actions import actions

import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext

class Client:
    def __init__(self, ui_callback):
        CFG = config.Config()
        self.action_dict_name = CFG.get_actions_dict()

        self.msg_magic = CFG.get_msg_magic()
        self.msg_magic_size = CFG.get_msg_magic_size()
        self.msg_type_size = CFG.get_msg_type_size()

        self.msg_min_size = self.msg_magic_size + self.msg_type_size + self.msg_magic_size
        self.msg_max_size = CFG.get_msg_max_size()

        self.host = CFG.get_client_config()['host']
        self.port = CFG.get_client_config()['port']
        self.connected = False

        self.action_handler = actions.ClientActionHandler(self, self.action_dict_name)
        self.callback_handler = actions.ClientCallbackHandler(self, self.action_dict_name)
        self.server_message_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=1)

        print("Client host:", self.host)
        print("Client port:", self.port)

        self.connect()

    def send_server_message(self, message: MSG.Message):
        """Send a message to the server."""
        if self.connected:
            try:
                if message.valid():
                    # Send message to server
                    # print("Send message to server...")
                    encoded_message = message.encode()
                    length = len(encoded_message)
                    self.client_socket.sendall(length.to_bytes(4, 'big'))
                    self.client_socket.sendall(encoded_message)
            except Exception as e:
                print("[Client] Failed to send message. Connection lost:", e)
                self.disconnect()
        else:
            print("[Client] Not connected to server.")

    def recv_server_message(self):
        """Handle server messages."""
        try:
            while self.connected:
                # First read the message length (4 bytes)

                length_bytes = utils.recv_all(self.client_socket, 4)
                if length_bytes is None:
                    break
                message_length = int.from_bytes(length_bytes, 'big')

                # Now read the actual message
                message_bytes = utils.recv_all(self.client_socket, message_length)
                if message_bytes is None:
                    break
                
                message = MSG.Message.from_bytes(message_bytes.decode("utf-8"), self)
                if message.valid():
                    message_type, message_content = message.unpack()
                    message_args = MSG.MessageArgs.to_arglist(message_content)
                    # print(f"[Client] Received message type {message_type}")

                    # Push server response to job queue
                    self.server_message_queue.put((message_type, message_args))
                else:
                    # Ignore invalid messages.
                    # print("Invalid message.")
                    pass
        except Exception as e:
            print("[Client] Lost connection to server due to:", e)
        self.disconnect()

    def connect(self):
        """Establish a connection with the server."""
        if self.connected:
            print("[Client] Already connected to the server.")
            return
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            print("[Client] Connected to the server.")
            self.connected = True
            threading.Thread(target=self.recv_server_message, daemon=True).start()
            self.process_queued_messages()
            # threading.Thread(target=self.process_queued_messages, daemon=True).start()
        except Exception as e:
            print("[Client] Failed to connect to the server due to:", e)

    def disconnect(self):
        """Disconnect from the server."""
        if self.client_socket:
            self.client_socket.close()
            self.connected = False
            print("[Client] Disconnected from the server.")

    def run_app(self):
        process_queue = self.process_queued_messages
        action_handler = self.action_handler
        callback_handler = self.callback_handler

        class MessagingApp(tk.Tk):
            def __init__(self):
                super().__init__()
                self.session_state = {
                    "logged_in": False,
                    "username": None,
                    "texts": {},
                    "max_texts": 5,
                    "current_page": "auth",
                    "auth_status": None,
                    "account_status": None,
                    "message_status": None,
                }

                callback_handler.session_state = self.session_state

                self.title("Messaging App")
                self.geometry("500x500")

                update_ui()

            def update_ui(self):
                process_queue()

                if self.session_state['logged_in'] == False:
                    self.show_auth_ui()  

                else: 
                    self.show_main_ui()

                self.after(2000, update_label)  # Call update_ui again after 1 second

            def clear_window(self):
                """Remove all widgets from the window before switching pages."""
                for widget in self.winfo_children():
                    widget.destroy()

            def show_auth_ui(self):
                """Show authentication (login/signup) UI."""
                self.clear_window()
                tk.Label(self, text="Welcome! Please Log In or Create an Account", font=("Arial", 12)).pack(pady=10)

                tk.Label(self, text="Username:").pack()
                self.username_entry = tk.Entry(self, width=30)
                self.username_entry.pack()

                tk.Label(self, text="Password:").pack()
                self.password_entry = tk.Entry(self, width=30, show="*")
                self.password_entry.pack()

                frame = tk.Frame(self)
                frame.pack(pady=10)

                btn_create = tk.Button(frame, text="Create Account", command=self.handle_create_account, width=15)
                btn_create.grid(row=0, column=0, padx=5)

                btn_login = tk.Button(frame, text="Log In", command=self.handle_login, width=15)
                btn_login.grid(row=0, column=1, padx=5)

                if self.session_state['account_status'] != None:
                    if self.session_state.get("account_status", False):
                        error_label = tk.Label(self, text="Error: Username already exists.", fg="red")
                        error_label.pack(pady=5)
                    elif self.session_state.get("account_status", True):
                        success_label = tk.Label(self, text="Account creation successful! Please log in.", fg="green")
                        success_label.pack(pady=5)
                    self.session_state['account_status'] = None

                if self.session_state['auth_status'] != None:
                    if self.session_state.get("auth_status", False):
                        error_label = tk.Label(self, text="Error: Invalid credentials. Try again.", fg="red")
                        error_label.pack(pady=5)
                    elif self.session_state.get("auth_status", True):
                        success_label = tk.Label(self, text="Login successful! Welcome.", fg="green")
                        success_label.pack(pady=5)
                        self.session_state["logged_in"] = True
                        self.session_state["current_page"] = "main"
                        self.after(400, self.show_main_ui)
                    self.session_state['auth_status'] = None

            def handle_login(self):
                """Handle user login."""
                username = self.username_entry.get()
                password = hasher.sha256(self.password_entry.get().encode()).hexdigest()
                action_handler.login_account(username, password)
                self.session_state["username"] = username

            def handle_create_account(self):
                """Handle user account creation."""
                username = self.username_entry.get()
                password = hasher.sha256(self.password_entry.get().encode()).hexdigest()

                if username and password and '|' not in username:
                    self.client.action_handler.create_account(username, password)

            def show_settings_ui(self):
                """Show settings page to adjust max messages per sender."""
                self.clear_window()
                tk.Label(self, text="⚙️ Settings", font=("Arial", 14)).pack(pady=10)

                tk.Label(self, text="Max number of texts per sender:").pack()
                self.max_texts_var = tk.IntVar(value=self.session_state["max_texts"])
                tk.Spinbox(self, from_=1, to=50, textvariable=self.max_texts_var).pack()

                btn_save = tk.Button(self, text="Save Settings", command=self.save_settings, width=20)
                btn_save.pack(pady=5)

                btn_back = tk.Button(self, text="Go Back", command=self.show_main_ui, width=20)
                btn_back.pack(pady=5)

            def save_settings(self):
                """Save settings and go back to main UI."""
                self.session_state["max_texts"] = self.max_texts_var.get()
                messagebox.showinfo("Success", "Settings updated!")
                self.show_main_ui()

            def show_main_ui(self):
                """Show main messaging interface."""
                self.clear_window()
                tk.Label(self, text=f"Hello, {self.session_state['username']}! 👋", font=("Arial", 12)).pack(pady=10)

                frame = tk.Frame(self)
                frame.pack()

                btn_settings = tk.Button(frame, text="⚙️ Settings", command=self.show_settings_ui, width=15)
                btn_settings.grid(row=0, column=0, padx=5)

                btn_logout = tk.Button(frame, text="Log Out", command=self.logout, width=15)
                btn_logout.grid(row=0, column=1, padx=5)

                btn_delete = tk.Button(frame, text="Delete Account", command=self.delete_account, width=15)
                btn_delete.grid(row=0, column=2, padx=5)

                self.show_send_message_ui()
                self.show_inbox_ui()

            def logout(self):
                """Log out the user."""
                self.session_state["logged_in"] = False
                self.session_state["username"] = None
                self.show_auth_ui()

            def delete_account(self):
                """Delete user account."""
                self.client.action_handler.delete_account(self.session_state["username"])
                self.logout()
                messagebox.showinfo("Account Deleted", "Your account has been deleted.")

            def show_send_message_ui(self):
                """Show send message interface."""
                tk.Label(self, text="📩 Send a Text", font=("Arial", 12)).pack(pady=10)

                frame = tk.Frame(self)
                frame.pack()

                tk.Label(frame, text="Recipient:").grid(row=0, column=0)
                self.recipient_entry = tk.Entry(frame, width=30)
                self.recipient_entry.grid(row=0, column=1)

                self.text_entry = tk.Text(self, width=40, height=4)
                self.text_entry.pack(pady=5)

                btn_send = tk.Button(self, text="Send", command=self.send_message, width=20)
                btn_send.pack(pady=5)

            def send_message(self):
                """Send a text message."""
                recipient = self.recipient_entry.get()
                text = self.text_entry.get("1.0", tk.END).strip()
                self.client.action_handler.send_text_message(self.session_state["username"], recipient, text)
                messagebox.showinfo("Message Sent", "Your message has been sent.")

            def show_inbox_ui(self):
                """Display messages in the inbox."""
                tk.Label(self, text="📥 Inbox", font=("Arial", 12)).pack(pady=10)
                self.inbox_frame = tk.Frame(self)
                self.inbox_frame.pack()

                self.filter_entry = tk.Entry(self, width=30)
                self.filter_entry.pack()
                self.filter_entry.bind("<KeyRelease>", self.update_inbox)

                self.inbox_text = scrolledtext.ScrolledText(self, width=50, height=10, state=tk.DISABLED)
                self.inbox_text.pack()

                self.update_inbox()

            def update_inbox(self, event=None):
                """Update inbox based on search filter."""
                self.inbox_text.config(state=tk.NORMAL)
                self.inbox_text.delete("1.0", tk.END)

                filter_text = self.filter_entry.get().lower()
                for sender, texts in self.session_state["texts"].items():
                    if filter_text in sender.lower():
                        self.inbox_text.insert(tk.END, f"📨 Chat with {sender}:\n")
                        for txt in texts[:self.session_state["max_texts"]]:
                            self.inbox_text.insert(tk.END, f"  - {txt['text']}\n")
                        self.inbox_text.insert(tk.END, "\n")

                self.inbox_text.config(state=tk.DISABLED)

        app = MessagingApp()
        app.mainloop()
    
    def process_queued_messages(self):
        """Processes messages from the server message queue (serially)."""
        while True:
            try:
                message_type, message_args = self.server_message_queue.get()
                self.perform_callback(message_type, message_args)
            except queue.Empty:
                pass
            except Exception as e:
                print("[Client] Message process error due to:", e)

    def perform_callback(self, message_type: str, message_args: list[str]):
        action_status = self.callback_handler.execute_action(message_type, message_args)
        if action_status:
            # print("[Client] Action OK.")
            pass
        else:
            print(f"[Client] Action {message_type} Unsuccessful.")

def test_end_to_end(client):
    def hash_function(s: str):
        return hasher.sha256(s.encode()).hexdigest()

    msg_content = MSG.MessageArgs("Hello World")
    msg = MSG.Message(message_args=msg_content, message_type="status", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("alice", hash_function("password1"))
    msg = MSG.Message(message_args=msg_content, message_type="create_account", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", hash_function("password2"))
    msg = MSG.Message(message_args=msg_content, message_type="create_account", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("alice", "bob", "Hi Bob!")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", "alice", "Hello Alice!")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("alice", "bob", "How are you?")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", "alice", "Good how about you?")
    msg = MSG.Message(message_args=msg_content, message_type="send_text_message", endpoint=client)
    client.send_server_message(msg)

    msg_content = MSG.MessageArgs("bob", "alice", 3)
    msg = MSG.Message(message_args=msg_content, message_type="fetch_text_messages", endpoint=client)
    client.send_server_message(msg)


if __name__ == "__main__":
    raise RuntimeError("You should not run this script directly. Import it as a module instead.")
    # client = Client()
    # test_end_to_end(client)
    # while True:
    #     pass
