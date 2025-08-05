#!/usr/bin/env python3
"""
SX Bet Vig Tracker Launcher
Choose which version of the vig tracker to run
"""

import subprocess
import sys
import os

def main():
    print("🎯 SX Bet Live Vig Tracker")
    print("=" * 40)
    print("Choose which version to run:")
    print("1. Basic Web Dashboard")
    print("2. Advanced WebSocket Tracker")
    print("3. Command Line Interface")
    print("4. Simple CLI (Minimal Dependencies)")
    print("5. Install Dependencies")
    print("6. Exit")
    print("=" * 40)
    
    while True:
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                print("Starting Basic Web Dashboard...")
                subprocess.run(["python3", "-m", "streamlit", "run", "sx_bet_vig_tracker.py"])
                break
                
            elif choice == "2":
                print("Starting Advanced WebSocket Tracker...")
                subprocess.run(["python3", "-m", "streamlit", "run", "sx_bet_websocket_tracker.py"])
                break
                
            elif choice == "3":
                print("Starting Command Line Interface...")
                print("Use --help for available options")
                subprocess.run(["python3", "sx_vig_cli.py", "--help"])
                break
                
            elif choice == "4":
                print("Starting Simple CLI (Minimal Dependencies)...")
                print("Use --help for available options")
                subprocess.run(["python3", "sx_vig_simple.py", "--help"])
                break
                
            elif choice == "5":
                print("Installing dependencies...")
                print("Choose installation type:")
                print("1. Full dependencies (for web dashboard)")
                print("2. Minimal dependencies (for CLI only)")
                dep_choice = input("Enter choice (1-2): ").strip()
                
                if dep_choice == "1":
                    subprocess.run(["python3", "-m", "pip", "install", "-r", "requirements.txt"])
                elif dep_choice == "2":
                    subprocess.run(["python3", "-m", "pip", "install", "-r", "requirements_minimal.txt"])
                else:
                    print("Invalid choice, installing minimal dependencies...")
                    subprocess.run(["python3", "-m", "pip", "install", "-r", "requirements_minimal.txt"])
                
                print("Dependencies installed successfully!")
                continue
                
            elif choice == "6":
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter a number between 1-6.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main() 