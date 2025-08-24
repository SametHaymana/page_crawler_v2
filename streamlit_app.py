import sys
from pathlib import Path
import os
import subprocess
import streamlit as st

@st.cache_resource
def install_playwright_browsers():
    """Install Playwright browsers if they are not already installed."""
    print("Attempting to install Playwright browsers...")
    try:
        # Use sys.executable to ensure we use the same python env as streamlit
        command = [sys.executable, "-m", "playwright", "install"]
        process = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Playwright browsers installed successfully.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("Error installing Playwright browsers:", e)
        if hasattr(e, 'stderr'):
            print(e.stderr)
        st.error("Failed to install required browser dependencies for the web crawler. The app cannot continue.")
        st.stop()
        return False

# Run the installation
install_playwright_browsers()

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

# Now that the path is set, we can import and run the main app
from main_app import main

if __name__ == "__main__":
    main()
