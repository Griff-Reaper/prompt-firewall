#!/usr/bin/env python3
"""
Quick Setup and Test Script
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run command and show output"""
    print(f"\n[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[✓] {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"[!] {description} - FAILED")
            if result.stderr:
                print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"[!] Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print(" "*20 + "PROMPT FIREWALL - SETUP")
    print("="*70)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("\n[!] Python 3.8+ required")
        sys.exit(1)
    
    print(f"\n[✓] Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("\n[!] Installation failed. Try manually:")
        print("    pip install pyyaml")
        sys.exit(1)
    
    # Run demo
    print("\n" + "="*70)
    print(" "*20 + "RUNNING DEMO")
    print("="*70)
    
    run_command("cd examples && python cli_demo.py", "Running CLI demo")
    
    print("\n" + "="*70)
    print(" "*20 + "SETUP COMPLETE!")
    print("="*70)
    
    print("\n[✓] Prompt Firewall is ready!")
    print("\nNext steps:")
    print("  1. Review demo_logs/ for audit logs")
    print("  2. Customize policies in policies/default.yaml")
    print("  3. Integrate into your application")
    print("\nDocumentation: README.md\n")

if __name__ == "__main__":
    main()
