# Configuration Management

The vuDataSim Web UI now uses a YAML-based configuration system for managing all settings including IP addresses, paths, and other configuration parameters.

## Configuration File

The main configuration file is `config.yaml` located in the root directory of the project. This file contains all the settings organized into logical sections:

```yaml
# Network Configuration
network:
  remote_host: "216.48.191.10"
  remote_user: "vunet"
  streamlit_port: 8501
  streamlit_address: "0.0.0.0"

# Path Configuration
paths:
  remote_ssh_key: "~/.ssh/id_rsa"
  remote_binary_dir: "/home/vunet/vuDataSim/vuDataSim/bin/"
  local_logs_dir: "logs"
  local_backups_dir: "backups"

# Binary Configuration
binaries:
  primary_binary: "vuDataSim"
  supported_binaries:
    - "vuDataSim"
    - "RakvuDataSim" 
    - "finalvudatasim"
    - "gvudatsim"

# Process Configuration
process:
  default_timeout: 300
  graceful_shutdown_timeout: 10
  remote_timeout: 300

# EPS Configuration  
eps:
  default_unique_key: 1
  max_unique_key: 1000000000

# Logging Configuration
logging:
  log_file: "vudatasim-webui.log"
  log_max_size: 10485760  # 10MB in bytes
  log_backup_count: 5

# Backup Configuration
backup:
  retention_days: 7
```

## Managing Configuration

### 1. Direct File Editing

You can directly edit the `config.yaml` file with any text editor:

```bash
nano config.yaml
# or
vim config.yaml
```

### 2. Using the Configuration Manager

A interactive configuration manager is provided for easy updates:

```bash
# Show current configuration
python3 config_manager.py show

# Interactive configuration menu
python3 config_manager.py

# Update specific sections
python3 config_manager.py network
python3 config_manager.py paths
```

### 3. Programmatic Updates

You can also update configuration programmatically:

```python
from core.config import get_config

config = get_config()

# Update a value
config.update_value('network.remote_host', '192.168.1.100')

# Get a value
host = config.get('network.remote_host')
```

## Configuration Sections

### Network Settings
- `remote_host`: IP address of the remote server
- `remote_user`: SSH username for remote connections
- `streamlit_port`: Port for the web interface
- `streamlit_address`: Address to bind the web interface

### Path Settings
- `remote_ssh_key`: Path to SSH private key
- `remote_binary_dir`: Directory containing binaries on remote server
- `local_logs_dir`: Local directory for log files
- `local_backups_dir`: Local directory for backup files

### Binary Settings
- `primary_binary`: Default binary to use
- `supported_binaries`: List of supported binary names

### Process Settings
- `default_timeout`: Default timeout for operations (seconds)
- `graceful_shutdown_timeout`: Timeout for graceful shutdown (seconds)
- `remote_timeout`: Timeout for remote operations (seconds)

## Notes

- The application will automatically reload configuration when the file is modified
- If the configuration file is missing, default values will be used
- Always backup your configuration before making changes
- The configuration manager validates input values where possible
