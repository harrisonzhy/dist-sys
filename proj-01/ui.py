import streamlit as st
from client import Client
import hashlib as hasher

def update_ui_state(key, value):
    if key == 'fetched_messages':
        m_id, sender, text = value.split('|')
        if st.session_state['texts'][sender]:
            st.session_state['texts'][sender].append({'id': m_id, 'text': text})
        else:
            st.session_state['texts'][sender] = [{'id': m_id, 'text': text}]
    else:
        st.session_state[key] = value
    st.rerun()

if "client" not in st.session_state:
    st.session_state["client"] = Client(update_ui_state)

# Initialize session state for user authentication
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

if "texts" not in st.session_state:
    st.session_state["texts"] = {}

if "max_texts" not in st.session_state:
    st.session_state["max_texts"] = 5  # Default max number of texts per sender

### **Settings Page**
def show_settings_ui():
    st.title("⚙️ Settings")
    st.subheader("Configure Maximum Texts Shown Per Sender")

    max_texts = st.number_input(
        "Max number of texts per sender", min_value=1, max_value=50, value=st.session_state["max_texts"]
    )

    if st.button("Save Settings", use_container_width=True):
        st.session_state["max_texts"] = max_texts
        st.success("Settings updated!")
        st.rerun()

    if st.button("Go Back", use_container_width=True):
        st.session_state["current_page"] = "main"
        st.rerun()

### **🔹 Authentication Page (Login / Signup)**
def show_auth_ui():
    st.title("Welcome! Please Log In or Create an Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Create Account", use_container_width=True):
            if username and password and ('|' not in username):
                st.session_state["username"] = username
                st.session_state["client"].ClientActionHandler.create_account(username, hasher.sha256(password.encode()).hexdigest())
            else:
                st.error("Enter a valid username and password. Cannot include '|' in username.")

    with col2:
        if st.button("Log In", use_container_width=True):
            st.session_state["username"] = username 
            st.session_state["client"].ClientActionHandler.login_account(username, hasher.sha256(password.encode()).hexdigest())
            if username in st.session_state["texts"]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Logged in as {username}")
                st.rerun()
            else:
                st.error("Invalid credentials")

    if "account_status" in st.session_state:
        if st.session_state["account_status"] == 'False':
            st.error(st.session_state["❌ Account Creation Failed. Username already exists."])
        else:
            st.success("✅ Account Created.")
        del st.session_state['account_status']

    if "auth_status" in st.session_state:
        if st.session_state["auth_status"] == 'False':
            st.error(st.session_state["❌ Incorrect credentials."])
        else:
            st.success("✅ Login successful.")
        del st.session_state['login_status']
        st.session_state["logged_in"] = True

### **🔹 Main Page (Messaging UI)**
def show_main_ui():
    st.title(f"Hello, {st.session_state['username']}! 👋")

    if st.button("⚙️ Settings", key="settings", use_container_width=True):
        st.session_state["current_page"] = "settings"
        st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Log Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.rerun()

    with col2:
        if st.button("Delete Account", key="delete_account", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.session_state["client"].ClientActionHandler.delete_account(username)
            st.success("Account deleted")
            st.rerun()

    # Styled Text Input
    st.subheader("📩 Send a Text")
    with st.container(border=True):
        recipient = st.text_input("Recipient Username", placeholder="Enter recipient...")
        text = st.text_area("Text", placeholder="Type your text here...")

        if st.button("Send", use_container_width=True):
            st.session_state["client"].ClientActionHandler.send_text_message(st.session_state['username'], recipient, text)
            
        if "message_status" in st.session_state:
            if st.session_state["message_status"] == 'False':
                st.error("❌ Recipient does not exist!")
            else:
                st.success("✅ Text sent!")
            del st.session_state['message_status']                

    # Styled Inbox with Filtered Chats
    st.subheader("📥 Inbox")
    filter_pattern = st.text_input("Filter Chats", "")
    filtered_chats = {sender: texts for sender, texts in st.session_state["texts"].items() if filter_pattern.lower() in sender.lower()}
    with st.container(border=True):
        if filtered_chats:
            for sender, texts in filtered_chats.items():
                if texts:
                    st.markdown(f"### 📨 Chat with **{sender}**")
                    for txt in texts[:st.session_state["max_texts"]]:
                        col1, col2 = st.columns([9, 1])
                        with col1:
                            with st.chat_message("user"):
                                st.write(txt['text'])
                        with col2:
                            with st.container():
                                if st.button("🗑️", key=f"{sender}_{txt}", use_container_width=True):
                                    st.session_state["texts"][sender].remove(txt)
                                    st.session_state["client"].ClientActionHandler.delete_text_message(txt['id'])
                                    if not st.session_state["texts"][sender]:
                                        del st.session_state["texts"][sender]
                                    st.success("Text deleted!")
                                    st.rerun()
        else:
            st.info("No texts match your search.")

### **UI Routing Based on Login Status**
if st.session_state["current_page"] == "settings":
    show_settings_ui()
elif not st.session_state["logged_in"]:
    show_auth_ui()
else:
    show_main_ui()