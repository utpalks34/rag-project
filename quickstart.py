#!/usr/bin/env python
"""
Quick start script to initialize and run the application locally.
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is >= 3.11."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")
    
    try:
        import fastapi
        print("✓ FastAPI")
    except ImportError:
        print("❌ FastAPI not installed")
        return False
    
    try:
        import streamlit
        print("✓ Streamlit")
    except ImportError:
        print("❌ Streamlit not installed")
        return False
    
    try:
        import langchain
        print("✓ LangChain")
    except ImportError:
        print("❌ LangChain not installed")
        return False
    
    try:
        import chromadb
        print("✓ ChromaDB")
    except ImportError:
        print("❌ ChromaDB not installed")
        return False
    
    return True


def check_env_file():
    """Check if .env file exists and has OPENAI_API_KEY."""
    print_header("Checking Environment Configuration")
    
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("   Creating from .env.example...")
        if Path(".env.example").exists():
            with open(".env.example") as f:
                example = f.read()
            with open(".env", "w") as f:
                f.write(example)
            print("✓ .env file created from .env.example")
        else:
            print("❌ .env.example not found either")
            return False
    
    with open(".env") as f:
        content = f.read()
        if "OPENAI_API_KEY" in content and "sk-" in content:
            print("✓ OPENAI_API_KEY configured")
            return True
        else:
            print("❌ OPENAI_API_KEY not configured")
            print("   Please edit .env and add your OpenAI API key")
            return False


def create_directories():
    """Create necessary directories."""
    print_header("Creating Directories")
    
    dirs = [
        "data/uploads",
        "data/chroma_db",
        "logs",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ {dir_path}")


def main():
    """Main quick start flow."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  AI Study Notes Assistant - Quick Start                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Checks
    print_header("System Checks")
    check_python_version()
    
    if not check_dependencies():
        print("\n❌ Please install dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    if not check_env_file():
        print("\n❌ Please configure .env file with OPENAI_API_KEY")
        sys.exit(1)
    
    create_directories()
    
    # Summary
    print_header("Ready to Start")
    
    print("✓ All checks passed!")
    print("\nTo start the application, open two terminals and run:\n")
    print("Terminal 1 (Backend):")
    print("  uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000\n")
    print("Terminal 2 (Frontend):")
    print("  streamlit run frontend/app.py\n")
    print("Then visit: http://localhost:8501\n")
    
    # Offer to start
    response = input("Would you like to start the backend now? (y/n): ").strip().lower()
    
    if response == "y":
        print("\nStarting backend server...")
        try:
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "backend.main:app",
                "--reload",
                "--host", "127.0.0.1",
                "--port", "8000"
            ])
        except KeyboardInterrupt:
            print("\n\nBackend stopped.")


if __name__ == "__main__":
    main()
