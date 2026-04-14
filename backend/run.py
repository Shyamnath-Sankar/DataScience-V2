"""
Run script for the DataSci AI backend.
Installs dependencies if needed and starts the FastAPI server.
"""

import subprocess
import sys
import os

def check_and_install_deps():
    """Install requirements if not already installed."""
    try:
        import fastapi
        import uvicorn
        import pandas
        import openai
        print("[OK] Dependencies already installed")
    except ImportError:
        print("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"
        ])
        print("[OK] Dependencies installed")

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    check_and_install_deps()

    print("")
    print("Starting DataSci AI Backend...")
    print("   Server: http://localhost:8000")
    print("   Docs:   http://localhost:8000/docs")
    print("   Press Ctrl+C to stop")
    print("")

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
