"""
Authentication module for Genetic Page Crawler Service
Simple password-based authentication using Streamlit session state
"""

import streamlit as st
import hashlib
from config import Config

def hash_password(password: str) -> str:
    """Hash password for secure comparison"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(entered_password: str) -> bool:
    """Check if entered password matches the configured password"""
    return entered_password == Config.APP_PASSWORD

def logout():
    """Logout the user"""
    st.session_state.authenticated = False
    st.rerun() 