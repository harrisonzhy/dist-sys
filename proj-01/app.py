import streamlit as st
import os
from pyngrok import ngrok

# Set up Ngrok tunnel
ngrok.set_auth_token("YOUR_AUTH_TOKEN")  # Only run once
port = 8501  # Streamlit default port
public_url = ngrok.connect(port).public_url  # Get public URL
