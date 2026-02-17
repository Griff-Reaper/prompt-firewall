#!/usr/bin/env python3
"""
Prompt Firewall - API Server Startup Script
"""
import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install API dependencies"""
    print("[*] Installing API dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("[✓] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("[!] Failed to install dependencies")
        return False

def main():
    print("\n" + "="*70)
    print(" "*20 + "PROMPT FIREWALL API")
    print("="*70 + "\n")
    
    # Check dependencies
    if not check_dependencies():
        print("[!] Missing dependencies")
        response = input("Install them now? (y/n): ")
        if response.lower() == 'y':
            if not install_dependencies():
                sys.exit(1)
        else:
            print("\n[!] Please install dependencies manually:")
            print("    pip install -r api/requirements.txt\n")
            sys.exit(1)
    
    # Start server
    print("[*] Starting Prompt Firewall API...")
    print("\n" + "-"*70)
    print("    🌐 API:        http://localhost:8000")
    print("    📚 API Docs:   http://localhost:8000/docs")
    print("    📊 Dashboard:  http://localhost:8000/dashboard")
    print("-"*70)
    print("\n[*] Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n[✓] Server stopped")

if __name__ == "__main__":
    main()
