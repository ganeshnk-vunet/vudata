"""
Configuration settings for vuDataSim Web UI
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager that loads settings from YAML file"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_file = self.base_dir / "config.yaml"
        self._config_data = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                # Return default configuration if file doesn't exist
                return self._get_default_config()
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration as fallback"""
        return {
            'network': {
                'remote_host': '216.48.191.10',
                'remote_user': 'vunet',
                'streamlit_port': 8501,
                'streamlit_address': '0.0.0.0'
            },
            'paths': {
                'remote_ssh_key': '~/.ssh/id_rsa',
                'remote_binary_dir': '/home/vunet/vuDataSim/vuDataSim/bin/',
                'local_logs_dir': 'logs',
                'local_backups_dir': 'backups'
            },
            'binaries': {
                'primary_binary': 'vuDataSim',
                'supported_binaries': ['vuDataSim', 'RakvuDataSim', 'finalvudatasim', 'gvudatsim']
            },
            'process': {
                'default_timeout': 300,
                'graceful_shutdown_timeout': 10,
                'remote_timeout': 300
            },
            'eps': {
                'default_unique_key': 1,
                'max_unique_key': 1000000000
            },
            'logging': {
                'log_file': 'vudatasim-webui.log',
                'log_max_size': 10485760,
                'log_backup_count': 5
            },
            'backup': {
                'retention_days': 7
            }
        }
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'network.remote_host')"""
        keys = key_path.split('.')
        value = self._config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def reload(self):
        """Reload configuration from YAML file"""
        self._config_data = self._load_config()
        return self._config_data
    
    def update_value(self, key_path: str, value):
        """Update a configuration value and save to YAML file"""
        keys = key_path.split('.')
        config_dict = self._config_data.copy()
        
        # Navigate to the correct nested location
        current = config_dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save to file
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            self._config_data = config_dict
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

# Create global config instance
_config = Config()

# Function to get config instance
def get_config():
    """Get the global configuration instance"""
    return _config

# Base paths
BASE_DIR = _config.base_dir
BIN_DIR = BASE_DIR.parent / "bin"
LOGS_DIR = BASE_DIR / _config.get('paths.local_logs_dir', 'logs')
BACKUPS_DIR = BASE_DIR / _config.get('paths.local_backups_dir', 'backups')

# Binary configuration
PRIMARY_BINARY = _config.get('binaries.primary_binary', 'vuDataSim')
SUPPORTED_BINARIES = _config.get('binaries.supported_binaries', ['vuDataSim'])

# YAML configuration (keeping for backward compatibility)
CONF_D_DIR = BASE_DIR.parent / "conf.d"
MAIN_CONFIG_FILE = CONF_D_DIR / "conf.yml"
MODULE_CONFIG_FILE = "conf.yml"

# Process management
DEFAULT_TIMEOUT = _config.get('process.default_timeout', 300)
GRACEFUL_SHUTDOWN_TIMEOUT = _config.get('process.graceful_shutdown_timeout', 10)

# EPS calculation
DEFAULT_UNIQUE_KEY = _config.get('eps.default_unique_key', 1)
MAX_UNIQUE_KEY = _config.get('eps.max_unique_key', 1000000000)

# UI configuration
STREAMLIT_PORT = _config.get('network.streamlit_port', 8501)
STREAMLIT_ADDRESS = _config.get('network.streamlit_address', '0.0.0.0')

# Logging
LOG_FILE = LOGS_DIR / _config.get('logging.log_file', 'vudatasim-webui.log') if LOGS_DIR.exists() else None
LOG_MAX_SIZE = _config.get('logging.log_max_size', 10485760)
LOG_BACKUP_COUNT = _config.get('logging.log_backup_count', 5)

# Backup configuration
BACKUP_RETENTION_DAYS = _config.get('backup.retention_days', 7)

# Remote SSH configuration for binary execution
REMOTE_HOST = _config.get('network.remote_host', '216.48.191.10')
REMOTE_USER = _config.get('network.remote_user', 'vunet')
REMOTE_SSH_KEY_PATH = _config.get('paths.remote_ssh_key', '~/.ssh/id_rsa')
REMOTE_BINARY_DIR = _config.get('paths.remote_binary_dir', '/home/vunet/vuDataSim/vuDataSim/bin/')
REMOTE_TIMEOUT = _config.get('process.remote_timeout', 300)