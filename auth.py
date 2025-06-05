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

def show_login_form():
    """Display the login form"""
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 50vh;">
        <div style="text-align: center; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h1>🕷️ Genetic Page Crawler Service</h1>
            <h3>🔐 Authentication Required</h3>
            <p>Please enter the password to access the application</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered columns for the form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            password = st.text_input(
                "Password", 
                type="password",
                placeholder="Enter application password",
                help="Contact administrator if you don't have the password"
            )
            
            submit_button = st.form_submit_button("🚀 Access Application", use_container_width=True)
            
            if submit_button:
                if check_password(password):
                    st.session_state.authenticated = True
                    st.success("✅ Authentication successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Please try again.")
                    st.warning("⚠️ Contact administrator if you need access.")

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def logout():
    """Logout the user"""
    st.session_state.authenticated = False
    st.rerun()

def show_logout_option():
    """Show logout option in sidebar"""
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Logout", help="Logout from the application"):
            logout()

def require_authentication(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_form()
            return None
        return func(*args, **kwargs)
    return wrapper 