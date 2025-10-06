"""
Configuration settings for vuDataSim Web UI
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
CONF_D_DIR = BASE_DIR.parent / "conf.d"
BIN_DIR = BASE_DIR.parent / "bin"
LOGS_DIR = BASE_DIR / "logs"
BACKUPS_DIR = BASE_DIR / "backups"

# Binary configuration
PRIMARY_BINARY = "vuDataSim"
SUPPORTED_BINARIES = ["vuDataSim", "RakvuDataSim", "finalvudatasim"]

# YAML configuration
MAIN_CONFIG_FILE = CONF_D_DIR / "conf.yml"
MODULE_CONFIG_FILE = "conf.yml"  # Relative to module directory

# Process management
DEFAULT_TIMEOUT = 300  # 5 minutes default
GRACEFUL_SHUTDOWN_TIMEOUT = 10  # seconds

# EPS calculation
DEFAULT_UNIQUE_KEY = 1
MAX_UNIQUE_KEY = 1000000000  # 1e9 as mentioned in requirements

# UI configuration
STREAMLIT_PORT = 8501
STREAMLIT_ADDRESS = "0.0.0.0"

# Logging
LOG_FILE = LOGS_DIR / "vudatasim-webui.log" if LOGS_DIR.exists() else None
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Backup configuration
BACKUP_RETENTION_DAYS = 7

# Remote SSH configuration for binary execution
REMOTE_HOST = "216.48.191.10"
REMOTE_USER = "vunet"
REMOTE_SSH_KEY_PATH = "~/.ssh/id_rsa"  # Update this path as needed
REMOTE_BINARY_DIR = "/home/vunet/vuDataSim/vuDataSim/bin"
REMOTE_TIMEOUT = 300  # 5 minutes default for remote execution