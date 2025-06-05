import os
from dotenv import load_dotenv

load_dotenv()

# Try to import Streamlit for secrets management
try:
    import streamlit as st
    _has_streamlit = True
except ImportError:
    _has_streamlit = False

def get_config_value(key: str, default: str = None):
    """Get configuration value from environment or Streamlit secrets"""
    # First try environment variables
    value = os.getenv(key, default)
    
    # If running in Streamlit and value not found, try secrets
    if not value and _has_streamlit:
        try:
            value = st.secrets.get(key, default)
        except:
            value = default
    
    return value

class Config:
    """Configuration class for the Page Crawler Service"""
    
    # Azure OpenAI API Configuration
    AZURE_OPENAI_API_KEY = get_config_value("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = get_config_value("AZURE_OPENAI_ENDPOINT", "https://testsamet.cognitiveservices.azure.com")
    AZURE_OPENAI_API_VERSION = get_config_value("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = get_config_value("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    
    # Authentication Configuration
    APP_PASSWORD = get_config_value("APP_PASSWORD", "GeneticCrawler2024!")
    
    # Crawler Configuration
    MAX_PAGES_PER_DOMAIN = 10
    CRAWLER_DELAY = 1  # seconds between requests
    MAX_CONTENT_LENGTH = 50000  # characters
    
    # Supported languages for content extraction
    SUPPORTED_LANGUAGES = ["en", "tr"]
    
    # Web scraping configuration
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    REQUEST_TIMEOUT = 30
    
    # Streamlit configuration
    PAGE_TITLE = "Genetic Page Crawler Service"
    PAGE_ICON = "🕷️"
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        if not cls.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
        if not cls.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        return True 