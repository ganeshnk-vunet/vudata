#!/usr/bin/env python3
"""
Configuration management utility for vuDataSim Web UI
"""
import sys
import yaml
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.config import get_config

def show_current_config():
    """Display current configuration"""
    config = get_config()
    print("Current Configuration:")
    print("=" * 50)
    print(f"Remote Host: {config.get('network.remote_host')}")
    print(f"Remote User: {config.get('network.remote_user')}")
    print(f"Remote Binary Directory: {config.get('paths.remote_binary_dir')}")
    print(f"SSH Key Path: {config.get('paths.remote_ssh_key')}")
    print(f"Streamlit Port: {config.get('network.streamlit_port')}")
    print(f"Streamlit Address: {config.get('network.streamlit_address')}")
    print(f"Default Timeout: {config.get('process.default_timeout')}")
    print("=" * 50)

def update_network_settings():
    """Update network settings interactively"""
    config = get_config()
    
    print("Update Network Settings:")
    print("-" * 30)
    
    current_host = config.get('network.remote_host')
    new_host = input(f"Remote Host [{current_host}]: ").strip()
    if new_host:
        config.update_value('network.remote_host', new_host)
        print(f"✓ Updated remote host to: {new_host}")
    
    current_user = config.get('network.remote_user')
    new_user = input(f"Remote User [{current_user}]: ").strip()
    if new_user:
        config.update_value('network.remote_user', new_user)
        print(f"✓ Updated remote user to: {new_user}")
    
    current_port = config.get('network.streamlit_port')
    new_port = input(f"Streamlit Port [{current_port}]: ").strip()
    if new_port:
        try:
            port_num = int(new_port)
            config.update_value('network.streamlit_port', port_num)
            print(f"✓ Updated streamlit port to: {port_num}")
        except ValueError:
            print("❌ Invalid port number")

def update_path_settings():
    """Update path settings interactively"""
    config = get_config()
    
    print("Update Path Settings:")
    print("-" * 30)
    
    current_binary_dir = config.get('paths.remote_binary_dir')
    new_binary_dir = input(f"Remote Binary Directory [{current_binary_dir}]: ").strip()
    if new_binary_dir:
        config.update_value('paths.remote_binary_dir', new_binary_dir)
        print(f"✓ Updated remote binary directory to: {new_binary_dir}")
    
    current_ssh_key = config.get('paths.remote_ssh_key')
    new_ssh_key = input(f"SSH Key Path [{current_ssh_key}]: ").strip()
    if new_ssh_key:
        config.update_value('paths.remote_ssh_key', new_ssh_key)
        print(f"✓ Updated SSH key path to: {new_ssh_key}")

def main():
    """Main configuration management menu"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            show_current_config()
            return
        elif sys.argv[1] == "network":
            update_network_settings()
            return
        elif sys.argv[1] == "paths":
            update_path_settings()
            return
    
    print("vuDataSim Configuration Manager")
    print("=" * 40)
    print("1. Show current configuration")
    print("2. Update network settings")
    print("3. Update path settings")
    print("4. Exit")
    print()
    
    while True:
        try:
            choice = input("Select option (1-4): ").strip()
            
            if choice == "1":
                show_current_config()
            elif choice == "2":
                update_network_settings()
            elif choice == "3":
                update_path_settings()
            elif choice == "4":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-4.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
