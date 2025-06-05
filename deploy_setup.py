#!/usr/bin/env python3
"""
Quick deployment setup script for Genetic Page Crawler Service
"""

import os
import shutil
from pathlib import Path

def setup_streamlit_deployment():
    """Setup files for Streamlit Community Cloud deployment"""
    print("🚀 Setting up for Streamlit Community Cloud deployment...")
    
    # Create .streamlit directory if it doesn't exist
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # Check if secrets.toml exists
    secrets_file = streamlit_dir / "secrets.toml"
    if not secrets_file.exists():
        print("⚠️  Please create .streamlit/secrets.toml with your Azure OpenAI credentials")
        print("Example content:")
        print("""
AZURE_OPENAI_API_KEY = "your-key-here"
AZURE_OPENAI_ENDPOINT = "https://your-endpoint.openai.azure.com"
AZURE_OPENAI_DEPLOYMENT_NAME = "your-deployment-name"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        """)
    
    print("✅ Streamlit deployment files ready!")
    print("Next steps:")
    print("1. Create a GitHub repository")
    print("2. Push your code: git add . && git commit -m 'Initial commit' && git push")
    print("3. Go to https://share.streamlit.io")
    print("4. Connect your GitHub repo and deploy")

def setup_docker_deployment():
    """Setup files for Docker deployment"""
    print("🐳 Setting up for Docker deployment...")
    
    if not Path("Dockerfile").exists():
        print("❌ Dockerfile not found!")
        return
    
    print("✅ Docker deployment files ready!")
    print("To build and run locally:")
    print("docker build -t genetic-page-crawler .")
    print("docker run -p 8080:8080 --env-file .env genetic-page-crawler")

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        "streamlit_app.py",
        "config.py", 
        "sectors.csv",
        "requirements_deploy.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("✅ All required files present!")
    return True

def main():
    """Main deployment setup function"""
    print("""
🕷️ Genetic Page Crawler Service - Deployment Setup
=================================================
    """)
    
    if not check_requirements():
        print("Please ensure all required files are present before deploying.")
        return
    
    print("Choose deployment option:")
    print("1. Streamlit Community Cloud (FREE)")
    print("2. Docker/Container deployment")
    print("3. Show all deployment options")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        setup_streamlit_deployment()
    elif choice == "2":
        setup_docker_deployment()
    elif choice == "3":
        print("📖 Check DEPLOYMENT_GUIDE.md for all deployment options")
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main() 