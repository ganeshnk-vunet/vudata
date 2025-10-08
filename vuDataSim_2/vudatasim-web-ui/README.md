# vuDataSim Web UI

A comprehensive web-based management platform for vuDataSim data simulation system with advanced YAML configuration management, EPS (Events Per Second) optimization, and real-time process control.

## 🎯 What This Tool Does

The vuDataSim Web UI is a sophisticated management interface that provides complete control over data simulation processes. It allows users to:

1. **Manage Data Simulation Processes**: Start, stop, and monitor vuDataSim binaries with configurable timeouts and remote execution capabilities
2. **Configure Data Generation**: Edit YAML configurations safely while preserving formatting and comments
3. **Optimize Performance**: Calculate and tune Events Per Second (EPS) for optimal data throughput
4. **Monitor Real-time Metrics**: Track system performance and data generation rates
5. **Ensure Data Integrity**: Maintain configuration backups and prevent concurrent modification conflicts

## 🏗️ System Architecture

The system is built with a modular architecture separating concerns between UI, core logic, and configuration management:

```
vuDataSim Web UI
├── Web Interface Layer (Streamlit)
├── Core Business Logic
│   ├── Configuration Management (YAML-based)
│   ├── Process Management (Local & Remote)
│   ├── EPS Calculation Engine
│   ├── Safe YAML Editor
│   └── Monitoring & Analytics
└── External Integrations
    ├── vuDataSim Binaries
    ├── ClickHouse Database
    └── Remote SSH Execution
```

## 🚀 Core Features & Capabilities

### 🔧 Binary Process Management
- **Multi-Binary Support**: Manage different vuDataSim variants (vuDataSim, RakvuDataSim, finalvudatasim, gvudatsim)
- **Local & Remote Execution**: Run binaries locally or on remote servers via SSH
- **Process Lifecycle Control**: Start, stop, restart, and monitor process status
- **Timeout Management**: Configurable execution timeouts with graceful shutdown
- **Log Management**: Automatic log file generation and rotation

### ⚙️ Configuration Management System
- **YAML-Based Configuration**: Centralized configuration using `config.yaml`
- **Safe Editing**: Preserve YAML formatting, comments, and structure during edits
- **Backup & Rollback**: Automatic timestamped backups with restore capabilities
- **Conflict Detection**: Prevent concurrent modifications using file checksums
- **Live Reload**: Dynamic configuration updates without service restart

### 📊 EPS Calculation & Optimization
- **Real-time EPS Calculation**: Advanced algorithms to calculate Events Per Second
- **Module-Level Tuning**: Adjust unique keys and periods for optimal performance
- **Submodule Support**: Fine-grained control over submodule configurations
- **Auto-Tuner**: Intelligent suggestions for achieving target EPS rates
- **Performance Preview**: Live calculation preview before applying changes

### 🔍 Monitoring & Analytics
- **System Status Dashboard**: Real-time overview of all system components
- **Performance Metrics**: Track EPS, process status, and resource utilization
- **ClickHouse Integration**: Direct database monitoring for Kafka metrics
- **Historical Data**: Backup retention and historical configuration tracking

## 📋 Requirements & Dependencies

### System Requirements
- **Python**: 3.8+ with pip package manager
- **Operating System**: Linux, macOS, or Windows with SSH capabilities
- **Memory**: Minimum 4GB RAM for optimal performance
- **Disk Space**: 1GB for application, logs, and backups

### External Dependencies
- **vuDataSim Binaries**: Located in `../bin/` directory
- **Configuration Files**: YAML files in `../conf.d/` directory structure
- **SSH Access**: For remote binary execution (optional)
- **ClickHouse Database**: For real-time monitoring (optional)

### Python Dependencies
```bash
streamlit>=1.28.0          # Web UI framework
pyyaml>=6.0.1             # YAML parsing and manipulation
ruamel.yaml>=0.18.0       # Advanced YAML processing with comment preservation
psutil>=5.9.0             # System and process utilities
paramiko>=3.4.0           # SSH client for remote execution
clickhouse-driver>=0.2.7  # ClickHouse database connectivity
python-dateutil>=2.8.0    # Date/time utilities
dill>=0.3.7               # Advanced object serialization
```

## � Complete File Structure & Component Details

### Project Directory Layout
```
vudatasim-web-ui/
├── 📄 main.py                   # Application entry point
├── 📄 config.yaml              # Central configuration file
├── 📄 config_manager.py        # Interactive configuration manager
├── 📄 requirements.txt         # Python dependencies
├── 📄 CONFIG.md               # Configuration documentation
├── 📄 README.md               # This comprehensive guide
├── 📁 src/                    # Source code directory
│   ├── 📁 core/               # Core business logic modules
│   │   ├── 📄 config.py       # Configuration management system
│   │   ├── 📄 binary_manager.py # Process lifecycle management
│   │   ├── 📄 yaml_editor.py  # Safe YAML editing engine
│   │   ├── 📄 eps_calculator.py # EPS calculation algorithms
│   │   ├── 📄 diff_viewer.py  # Change preview system
│   │   ├── 📄 clickhouse_monitor.py # Database monitoring
│   │   └── 📄 audit_logger.py # Audit trail system
│   └── 📁 ui/                 # User interface layer
│       └── 📄 app.py          # Streamlit web application
├── 📁 logs/                   # Application and process logs
├── 📁 backups/               # Configuration file backups
└── 📁 __pycache__/           # Python bytecode cache

External Dependencies:
../bin/                        # vuDataSim binary executables
../conf.d/                     # Module configuration files
    ├── conf.yml              # Main configuration file
    └── ModuleName/           # Individual module directories
        ├── conf.yml          # Module-specific configuration
        └── submodule.yml     # Submodule configurations
```

## 🛠️ Installation & Setup

### 1. Environment Preparation
```bash
# Navigate to project directory
cd vudatasim-web-ui

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import streamlit, yaml, paramiko; print('Dependencies installed successfully')"
```

### 3. Configuration Setup
```bash
# Initialize configuration (if needed)
python config_manager.py show

# Edit configuration as needed
nano config.yaml
# or use interactive manager
python config_manager.py
```

### 4. Directory Structure Verification
```bash
# Ensure external directories exist
mkdir -p ../bin ../conf.d logs backups

# Set appropriate permissions
chmod +x ../bin/*  # Make binaries executable
chmod 755 logs backups  # Ensure write access
```

## 📄 Detailed File Analysis & Logic Explanation

### 1. 📄 main.py - Application Entry Point
```python
#!/usr/bin/env python3
"""
Main entry point for vuDataSim Web UI
Handles application startup, logging configuration, and error management
"""
```

**Purpose**: Bootstrap the entire application with proper error handling and logging setup.

**Key Functions**:
- `main()`: Initializes logging, sets up Python path, imports and starts Streamlit app
- **Error Handling**: Catches import errors, keyboard interrupts, and general exceptions
- **Logging Configuration**: Sets up structured logging with timestamps and levels
- **Path Management**: Ensures proper module imports by adding src directory to Python path

**Logic Flow**:
1. Configure basic logging to stdout with structured format
2. Add src directory to Python path for module imports
3. Import and execute the Streamlit UI application
4. Handle various error conditions gracefully with user-friendly messages

### 2. 📄 config.yaml - Central Configuration Hub
```yaml
# Network, path, binary, process, EPS, logging, and backup configurations
# Organized in logical sections for easy management
```

**Purpose**: Single source of truth for all application settings, replacing hardcoded values.

**Configuration Sections**:
- **Network**: Remote host details, SSH configuration, web server settings
- **Paths**: File system locations, SSH keys, binary directories
- **Binaries**: Supported binary names and primary binary selection
- **Process**: Timeout values, execution parameters
- **EPS**: Calculation parameters and limits
- **Logging**: Log file settings, rotation, size limits
- **Backup**: Retention policies and cleanup settings

**Key Benefits**:
- Centralized configuration management
- Easy customization without code changes
- Environment-specific settings support
- Version control friendly format

### 3. 📄 config_manager.py - Interactive Configuration Tool
```python
"""Configuration management utility for vuDataSim Web UI"""
```

**Purpose**: Command-line interface for managing configuration settings interactively.

**Key Functions**:
- `show_current_config()`: Display all current configuration values
- `update_network_settings()`: Interactive network configuration updates
- `update_path_settings()`: Interactive path configuration updates
- `main()`: Menu-driven interface for configuration management

**Usage Modes**:
```bash
python config_manager.py show      # Display current settings
python config_manager.py network   # Update network settings
python config_manager.py paths     # Update path settings
python config_manager.py          # Interactive menu
```

**Logic Features**:
- Input validation and error handling
- Confirmation prompts for changes
- Real-time configuration file updates
- Fallback to current values if no input provided

### 4. 📄 src/core/config.py - Configuration Management System
```python
"""Configuration settings for vuDataSim Web UI"""
class Config:
    """Configuration manager that loads settings from YAML file"""
```

**Purpose**: Core configuration management with YAML loading, validation, and runtime updates.

**Key Classes & Methods**:
- **Config Class**: Main configuration manager
  - `__init__()`: Initialize and load configuration from YAML
  - `_load_config()`: Load and parse YAML configuration file
  - `_get_default_config()`: Provide fallback default values
  - `get(key_path, default)`: Retrieve configuration values using dot notation
  - `reload()`: Refresh configuration from file
  - `update_value(key_path, value)`: Update and persist configuration changes

**Global Variables**: Exports all configuration values as module-level constants for backward compatibility:
- Network settings (REMOTE_HOST, REMOTE_USER, STREAMLIT_PORT, etc.)
- Path configurations (BIN_DIR, LOGS_DIR, BACKUPS_DIR, etc.)
- Process parameters (DEFAULT_TIMEOUT, GRACEFUL_SHUTDOWN_TIMEOUT, etc.)
- Binary settings (PRIMARY_BINARY, SUPPORTED_BINARIES, etc.)

**Logic Features**:
- Dot notation access (e.g., 'network.remote_host')
- Automatic fallback to defaults if YAML file missing
- Runtime configuration updates with file persistence
- Type-safe configuration access

### 5. 📄 src/core/binary_manager.py - Process Lifecycle Management
```python
"""Binary process management for vuDataSim"""
class ProcessManager:
    """Manages vuDataSim binary processes"""
```

**Purpose**: Complete process lifecycle management for vuDataSim binaries with local and remote execution support.

**Key Classes & Methods**:
- **ProcessManager Class**: Core process management functionality
  - `__init__()`: Initialize process tracking and log counter
  - `start_binary(binary_name, timeout)`: Launch binary with configurable timeout
  - `stop_binary(binary_name, graceful_timeout)`: Gracefully terminate process
  - `get_status(binary_name)`: Retrieve detailed process status
  - `list_binaries()`: Discover available binary files
  - `cleanup_finished_processes()`: Clean up completed processes
  - Remote execution methods for SSH-based binary control

**Process Management Logic**:
1. **Binary Discovery**: Scans bin directory for executable files
2. **Process Launching**: Uses subprocess.Popen with proper stdout/stderr redirection
3. **Timeout Handling**: Automatic process termination after specified duration
4. **Status Tracking**: Real-time monitoring of process state, PID, runtime
5. **Log Management**: Unique log file generation with timestamps
6. **Graceful Shutdown**: SIGTERM followed by SIGKILL if necessary
7. **Remote Execution**: SSH-based binary control for distributed deployments

**Advanced Features**:
- Process state persistence across operations
- Automatic cleanup of finished processes
- Comprehensive error handling and logging
- SSH key-based authentication for remote execution
- Process timeout with graceful degradation

### 6. 📄 src/core/yaml_editor.py - Safe YAML Editing Engine
```python
"""Safe YAML editor that preserves formatting and comments"""
class SafeYAMLEditor:
    """Safe YAML editor that preserves formatting and comments"""
```

**Purpose**: Advanced YAML editing system that maintains file formatting, comments, and structure integrity.

**Key Classes & Methods**:
- **SafeYAMLEditor Class**: Core YAML manipulation engine
  - `__init__()`: Initialize ruamel.yaml with preservation settings
  - `_calculate_checksum(file_path)`: Generate MD5 checksums for conflict detection
  - `_create_backup(file_path)`: Create timestamped backup files
  - `_parse_duration(duration_str)`: Convert duration strings to seconds
  - `_format_duration(seconds)`: Convert seconds back to duration format
  - `read_main_config()`: Load main configuration with checksum
  - `write_main_config()`: Save main configuration with backup
  - `read_module_config()`: Load module-specific configuration
  - `write_module_config()`: Save module configuration safely
  - `read_submodule_config()`: Load submodule configuration
  - `write_submodule_config()`: Save submodule configuration

**Safety Features**:
1. **Comment Preservation**: Uses ruamel.yaml to maintain YAML comments and formatting
2. **Atomic Writes**: Uses temporary files and atomic moves to prevent corruption
3. **Backup Creation**: Automatic timestamped backups before any changes
4. **Checksum Validation**: Detects concurrent modifications using MD5 checksums
5. **Error Recovery**: Rollback capabilities on write failures
6. **Token-Level Editing**: Precise editing of specific values without affecting structure

**Duration Parsing Logic**:
- Supports multiple formats: ms (milliseconds), s (seconds), m (minutes), h (hours)
- Bidirectional conversion between duration strings and numeric seconds
- Input validation with comprehensive error handling

### 7. 📄 src/core/eps_calculator.py - EPS Calculation Algorithms
```python
"""EPS (Events Per Second) calculation engine"""
class EPSCalculator:
    """Calculates EPS for modules and submodules"""
```

**Purpose**: Advanced EPS calculation system for optimizing data generation performance.

**Key Classes & Methods**:
- **EPSCalculator Class**: Core EPS calculation engine
  - `get_module_list()`: Discover available modules from conf.d directory
  - `get_submodules(module_name)`: Find submodules within a module
  - `get_module_config(module_name)`: Load module configuration with defaults
  - `get_submodule_config(module_name, submodule_name)`: Load submodule configuration
  - `calculate_eps(module_name, ...)`: Calculate EPS with optional overrides
  - `calculate_eps_for_all_modules()`: Calculate EPS across all modules
  - `find_optimal_config(target_eps, module_name)`: Auto-tuner algorithm

**EPS Calculation Formula**:
```
EPS = (ModuleLevelUniqueKeys × Sum(submodule contributions)) / periodSeconds
```

**Where**:
- **ModuleLevelUniqueKeys**: `uniquekey.NumUniqKey` from module config (default: 1)
- **Submodule contributions**: Each submodule's `NumUniqKey × multiplier` (default: 1)
- **periodSeconds**: Period converted to seconds (e.g., "1s" = 1, "250ms" = 0.25)

**Advanced Logic**:
1. **Module Discovery**: Scans conf.d directory for valid module structures
2. **Configuration Loading**: Reads YAML configurations with fallback defaults
3. **Submodule Processing**: Aggregates contributions from all submodules
4. **Period Conversion**: Handles various time formats (ms, s, m, h)
5. **EPS Optimization**: Auto-tuner suggests optimal configurations for target EPS
6. **Batch Calculation**: Efficient calculation across multiple modules

### 8. 📄 src/core/diff_viewer.py - Change Preview System
```python
"""Diff preview system for YAML changes"""
class DiffViewer:
    """Generate and display diffs for YAML changes"""
```

**Purpose**: Advanced diff generation system for previewing configuration changes before applying them.

**Key Classes & Methods**:
- **DiffViewer Class**: Change preview and diff generation
  - `generate_yaml_diff(original, new)`: Create unified diff between YAML strings
  - `generate_token_diff(module_name, changes)`: Generate targeted diffs for specific changes
  - `preview_module_changes(module_name, ...)`: Preview module configuration changes
  - `preview_submodule_changes(module_name, ...)`: Preview submodule changes
  - `_extract_key_changes(full_diff, changes)`: Extract relevant change sections
  - `_generate_change_summary(changes)`: Create human-readable change summaries

**Diff Generation Logic**:
1. **Unified Diff**: Uses difflib.unified_diff for standard diff format
2. **Token-Level Precision**: Focuses on specific changed values
3. **Context Preservation**: Maintains surrounding lines for context
4. **Change Extraction**: Identifies and highlights only relevant modifications
5. **Summary Generation**: Creates concise descriptions of changes
6. **Error Handling**: Graceful degradation on diff generation failures

### 9. 📄 src/core/clickhouse_monitor.py - Real-time Database Monitoring
```python
"""ClickHouse monitoring module for live EPS tracking"""
class ClickHouseMonitor:
    """Monitor ClickHouse for Kafka metrics via direct connection"""
```

**Purpose**: Real-time monitoring of ClickHouse database for Kafka metrics and EPS tracking.

**Key Classes & Methods**:
- **ClickHouseMonitor Class**: Database connectivity and monitoring
  - `__init__(host, port, database, user, password)`: Initialize connection parameters
  - `connect()`: Establish ClickHouse database connection
  - `disconnect()`: Close database connection properly
  - `execute_query(query)`: Execute SQL queries with error handling
  - `get_eps_for_topic(topic)`: Retrieve EPS metrics for specific Kafka topics
  - `get_topic_list()`: List available Kafka topics
  - `get_historical_eps(topic, duration)`: Retrieve historical EPS data

**Monitoring Features**:
1. **Direct Connection**: Uses clickhouse-driver for native database connectivity
2. **Real-time Queries**: Executes SQL queries for live metric retrieval
3. **Kafka Integration**: Monitors kafka_Broker_Topic_Metrics_data table
4. **Error Handling**: Comprehensive connection and query error management
5. **Data Formatting**: Processes query results for UI consumption
6. **Connection Pooling**: Efficient connection management for performance

## 🎯 Application Usage & Interface Guide

### Starting the Application
```bash
# Navigate to project directory
cd vudatasim-web-ui

# Activate virtual environment (if using one)
source venv/bin/activate

# Start the web interface
python main.py

# Alternative direct launch
streamlit run src/ui/app.py --server.port 8501
```

The web interface will be available at: **http://localhost:8501**

### 📊 Dashboard Interface - System Overview
**Location**: Main page after startup
**Purpose**: Comprehensive system status and quick access to key metrics

**Dashboard Components**:
1. **System Metrics Cards**: Total modules, aggregate EPS, binary count, backup files
2. **Recent Activity**: Latest process starts, configuration changes, errors
3. **Quick Actions**: Direct access to most common operations
4. **Status Indicators**: Visual indicators for system health and process status
5. **Performance Graphs**: Real-time EPS trends and historical data

**Real-time Updates**: Dashboard refreshes automatically to show current system state

### 🔧 Binary Control Interface - Process Management
**Location**: Sidebar → "Binary Control"
**Purpose**: Complete lifecycle management of vuDataSim binaries

**Binary Control Features**:
1. **Binary Selection**: 
   - Dropdown menu of available binaries (vuDataSim, RakvuDataSim, etc.)
   - Auto-detection of executables in bin directory
   - Primary binary selection from configuration

2. **Process Operations**:
   - **Start**: Launch binary with optional timeout configuration
   - **Stop**: Graceful shutdown with configurable grace period
   - **Restart**: Stop and start sequence with status monitoring
   - **Kill**: Force termination for unresponsive processes

3. **Status Monitoring**:
   - **Process ID (PID)**: Current process identifier
   - **Runtime**: Elapsed execution time
   - **Status**: Running, stopped, timeout, error states
   - **Log Files**: Direct access to process output logs
   - **Memory Usage**: Resource consumption monitoring

4. **Remote Execution**:
   - SSH-based binary control on remote servers
   - Key-based authentication configuration
   - Remote status monitoring and log retrieval

### 📁 Module Browser Interface - Configuration Overview
**Location**: Sidebar → "Module Browser"
**Purpose**: Navigate and manage module configurations

**Module Browser Features**:
1. **Module Discovery**:
   - Automatic scanning of conf.d directory structure
   - Detection of valid module directories with conf.yml files
   - Hierarchical display of modules and submodules

2. **Module Status Management**:
   - Enable/disable modules via conf.d/conf.yml editing
   - Bulk operations for multiple modules
   - Status filtering (enabled only, all modules)

3. **EPS Preview**:
   - Real-time EPS calculation for each module
   - Aggregate EPS across all enabled modules
   - Performance impact analysis

4. **Configuration Access**:
   - Direct links to module configuration editors
   - Quick view of key configuration parameters
   - Change history and backup access

### 🎛️ EPS Tuner Interface - Performance Optimization
**Location**: Sidebar → "EPS Tuner"
**Purpose**: Optimize data generation performance through EPS tuning

**EPS Tuner Features**:
1. **Manual Tuning**:
   - **Unique Keys Adjustment**: Slider/input for module-level unique keys
   - **Period Configuration**: Time period input with format validation
   - **Live Calculation**: Real-time EPS preview as values change
   - **Submodule Overrides**: Fine-grained control over submodule parameters

2. **Auto-Tuner Algorithm**:
   - **Target EPS Input**: Specify desired events per second
   - **Optimization Engine**: Intelligent calculation of optimal parameters
   - **Multiple Solutions**: Algorithm provides several configuration options
   - **Constraint Handling**: Respects minimum/maximum value limits

3. **Performance Analysis**:
   - **Before/After Comparison**: Show current vs. proposed EPS
   - **Impact Assessment**: Calculate performance improvements
   - **Resource Estimation**: Predict resource usage at new EPS levels
   - **Validation**: Ensure configurations are within acceptable ranges

4. **Batch Operations**:
   - **Multi-Module Tuning**: Apply optimizations across multiple modules
   - **Profile Management**: Save and load tuning profiles
   - **Template Application**: Apply proven configurations to new modules

### ⚙️ Configuration Editor Interface - Safe YAML Editing
**Location**: Sidebar → "Configuration Editor"
**Purpose**: Safe editing of YAML configuration files with integrity preservation

**Configuration Editor Features**:
1. **Module Configuration Editing**:
   - **Target Selection**: Choose module and configuration file
   - **Key Parameter Editing**: Focus on uniquekey.NumUniqKey and period values
   - **Live Validation**: Real-time syntax and value validation
   - **Format Preservation**: Maintains YAML comments and formatting

2. **Safety Features**:
   - **Backup Creation**: Automatic timestamped backups before changes
   - **Conflict Detection**: Checksums prevent concurrent modification issues
   - **Rollback Capability**: Restore from any previous backup
   - **Atomic Operations**: All-or-nothing file updates

3. **Preview System**:
   - **Diff Display**: Visual representation of proposed changes
   - **Change Summary**: Human-readable description of modifications
   - **Impact Analysis**: Show EPS and performance implications
   - **Confirmation Prompts**: User confirmation before applying changes

4. **Advanced Editing**:
   - **Submodule Support**: Edit individual submodule configurations
   - **Bulk Operations**: Apply changes across multiple files
   - **Template System**: Use predefined configuration templates
   - **Validation Engine**: Comprehensive configuration validation

### 📊 System Status Interface - Comprehensive Monitoring
**Location**: Sidebar → "System Status"
**Purpose**: Detailed system monitoring and performance analysis

**System Status Features**:
1. **Detailed Metrics**:
   - **Module Status Table**: Comprehensive view of all modules
   - **Binary Status**: Current state of all managed processes
   - **Configuration Health**: Validation status of all configurations
   - **Performance Metrics**: EPS, resource usage, throughput statistics

2. **Real-time Monitoring**:
   - **Live Updates**: Automatic refresh of status information
   - **Alert System**: Notifications for errors and status changes
   - **Performance Graphs**: Visual representation of metrics over time
   - **Resource Tracking**: CPU, memory, and disk usage monitoring

3. **Historical Analysis**:
   - **Backup History**: List of all configuration backups
   - **Change Log**: Audit trail of all system modifications
   - **Performance Trends**: EPS and performance over time
   - **Error History**: Log of errors and resolution status

### 🔍 ClickHouse Monitor Interface - Database Integration
**Location**: Sidebar → "ClickHouse Monitor"
**Purpose**: Real-time monitoring of ClickHouse database for Kafka metrics

**ClickHouse Monitor Features**:
1. **Database Connectivity**:
   - **Connection Management**: Establish and manage ClickHouse connections
   - **Query Execution**: Run custom SQL queries for data retrieval
   - **Connection Testing**: Verify database connectivity and permissions

2. **Kafka Metrics**:
   - **Topic Monitoring**: Track EPS for specific Kafka topics
   - **Broker Metrics**: Monitor Kafka broker performance
   - **Historical Data**: Retrieve historical EPS and performance data

3. **Data Visualization**:
   - **Real-time Charts**: Live graphing of EPS and performance metrics
   - **Comparison Views**: Compare performance across topics and time periods
   - **Export Capabilities**: Download metrics data for external analysis

## ⚙️ Configuration Architecture & File Formats

### 1. Central Configuration File - config.yaml
**Location**: `/vudatasim-web-ui/config.yaml`
**Purpose**: Single source of truth for all application settings

```yaml
# Network Configuration - Connection and communication settings
network:
  remote_host: "216.48.191.10"        # Target server IP for remote operations
  remote_user: "vunet"                # SSH username for remote connections
  streamlit_port: 8501                # Web interface port
  streamlit_address: "0.0.0.0"        # Bind address (0.0.0.0 = all interfaces)

# Path Configuration - File system locations and directories
paths:
  remote_ssh_key: "~/.ssh/id_rsa"     # SSH private key for authentication
  remote_binary_dir: "/home/vunet/vuDataSim/vuDataSim/bin/"  # Remote binary location
  local_logs_dir: "logs"              # Local log file directory
  local_backups_dir: "backups"        # Configuration backup directory

# Binary Configuration - Supported executables and defaults
binaries:
  primary_binary: "vuDataSim"         # Default binary to use
  supported_binaries:                 # List of supported binary names
    - "vuDataSim"                     # Main production binary
    - "RakvuDataSim"                  # Alternative implementation
    - "finalvudatasim"                # Final version binary
    - "gvudatsim"                     # GUI version binary

# Process Configuration - Execution parameters and timeouts
process:
  default_timeout: 300                # Default execution timeout (seconds)
  graceful_shutdown_timeout: 10       # Grace period for process shutdown
  remote_timeout: 300                 # Timeout for remote operations

# EPS Configuration - Performance calculation parameters
eps:
  default_unique_key: 1               # Default unique key value
  max_unique_key: 1000000000          # Maximum allowed unique key value

# Logging Configuration - Log management settings
logging:
  log_file: "vudatasim-webui.log"     # Main application log file
  log_max_size: 10485760              # Maximum log file size (10MB)
  log_backup_count: 5                 # Number of backup log files to keep

# Backup Configuration - Backup retention and cleanup
backup:
  retention_days: 7                   # Days to keep configuration backups
```

### 2. Module System Configuration Files

#### Main Module Registry - ../conf.d/conf.yml
**Purpose**: Central registry for enabling/disabling modules

```yaml
# Main configuration file that controls which modules are active
include_module_dirs:
  WebLogModule:                       # Example web log generation module
    enabled: true                     # Module is active and will be processed
  DatabaseModule:                     # Example database simulation module
    enabled: false                    # Module is disabled, will be skipped
  NetworkTrafficModule:               # Example network traffic module
    enabled: true                     # Module is active
  SecurityEventModule:                # Example security event module
    enabled: true                     # Module is active
```

#### Individual Module Configuration - ../conf.d/ModuleName/conf.yml
**Purpose**: Module-specific configuration with EPS parameters

```yaml
# Module configuration file - controls data generation parameters
enabled: true                         # Local module enable/disable flag

# Unique key configuration - primary EPS control parameter
uniquekey:
  name: "host"                        # Field name for unique key generation
  DataType: IPv4                      # Data type (IPv4, String, Integer, etc.)
  ValueType: "RandomFixed"            # Generation method (RandomFixed, Sequential, etc.)
  Value: "10.10.10.1"                # Base or example value
  NumUniqKey: 25000                   # PRIMARY EPS PARAMETER - number of unique keys

# Period configuration - timing control parameter
period: 1s                            # PRIMARY EPS PARAMETER - generation frequency

# Additional module-specific settings
output_format: "json"                 # Output format specification
compression: "gzip"                   # Compression method if applicable
batch_size: 1000                      # Number of events per batch

# Advanced configuration parameters
advanced:
  threading: true                     # Enable multi-threaded processing
  memory_buffer: "100MB"              # Memory buffer size
  disk_cache: "1GB"                   # Disk cache allocation
```

#### Submodule Configuration - ../conf.d/ModuleName/submodule.yml
**Purpose**: Fine-grained control over submodule behavior

```yaml
# Submodule configuration - additional EPS contributors
enabled: true                         # Submodule enable flag

# Submodule unique key configuration
uniquekey:
  name: "fields,instance"             # Composite field name
  DataType: String                    # Data type for this submodule
  ValueType: RandomFixed              # Value generation method
  Value: "default_value"              # Default or base value
  NumUniqKey: 3                       # SUBMODULE EPS CONTRIBUTION - unique key count

# Submodule-specific parameters
multiplier: 1                         # EPS calculation multiplier
weight: 1.0                          # Relative weight in EPS calculation
priority: "normal"                    # Processing priority (low, normal, high)

# Data generation parameters
generation:
  pattern: "random"                   # Generation pattern
  seed: 12345                        # Random seed for reproducibility
  distribution: "uniform"             # Statistical distribution
```

## 📊 EPS Calculation System - Deep Dive

### Core EPS Formula
The system uses a sophisticated EPS calculation algorithm:

```
EPS = (ModuleLevelUniqueKeys × ∑(SubmoduleContributions)) / periodSeconds
```

### Detailed Component Analysis

#### 1. ModuleLevelUniqueKeys
- **Source**: `uniquekey.NumUniqKey` from module `conf.yml`
- **Default**: 1 (if not specified)
- **Range**: 1 to 1,000,000,000 (configurable maximum)
- **Impact**: Primary multiplier for all EPS calculations

#### 2. SubmoduleContributions Calculation
```python
# Pseudocode for submodule contribution calculation
total_submodule_contribution = 0
for each submodule in module:
    if submodule.enabled:
        contribution = submodule.NumUniqKey × submodule.multiplier × submodule.weight
        total_submodule_contribution += contribution

# If no submodules exist or none are enabled, default to 1
if total_submodule_contribution == 0:
    total_submodule_contribution = 1
```

#### 3. Period Conversion Logic
```python
# Duration parsing with multiple format support
def parse_duration_to_seconds(duration_str):
    patterns = {
        'ms': 0.001,    # milliseconds
        's': 1.0,       # seconds  
        'm': 60.0,      # minutes
        'h': 3600.0     # hours
    }
    
    # Examples:
    # "250ms" → 0.25 seconds
    # "1s" → 1.0 seconds
    # "5m" → 300.0 seconds
    # "2h" → 7200.0 seconds
```

### EPS Calculation Examples

#### Example 1: Simple Module
```yaml
# Module config
uniquekey:
  NumUniqKey: 1000
period: 1s

# No submodules
# EPS = 1000 × 1 / 1 = 1000 events/second
```

#### Example 2: Module with Submodules
```yaml
# Module config
uniquekey:
  NumUniqKey: 500
period: 2s

# Submodule 1
uniquekey:
  NumUniqKey: 10
multiplier: 1

# Submodule 2  
uniquekey:
  NumUniqKey: 5
multiplier: 2

# Calculation:
# SubmoduleContribution = (10 × 1) + (5 × 2) = 20
# EPS = 500 × 20 / 2 = 5000 events/second
```

#### Example 3: High-Frequency Generation
```yaml
# Module config
uniquekey:
  NumUniqKey: 100
period: 250ms  # 0.25 seconds

# Submodules contribute 50 total
# EPS = 100 × 50 / 0.25 = 20,000 events/second
```

### Auto-Tuner Algorithm Logic

The auto-tuner uses advanced algorithms to calculate optimal configurations:

```python
def find_optimal_config(target_eps, module_name):
    """
    Calculate optimal configuration for target EPS
    """
    current_config = get_module_config(module_name)
    submodule_contribution = calculate_submodule_contribution(module_name)
    
    # Calculate required parameters
    for period in ["250ms", "500ms", "1s", "2s", "5s"]:
        period_seconds = parse_duration_to_seconds(period)
        required_unique_keys = (target_eps * period_seconds) / submodule_contribution
        
        # Validate against constraints
        if MIN_UNIQUE_KEYS <= required_unique_keys <= MAX_UNIQUE_KEYS:
            yield {
                "unique_keys": int(required_unique_keys),
                "period": period,
                "predicted_eps": calculate_eps_with_params(
                    module_name, required_unique_keys, period
                ),
                "efficiency_score": calculate_efficiency(required_unique_keys, period)
            }
```

### Performance Optimization Strategies

#### 1. EPS Scaling Approaches
- **Vertical Scaling**: Increase NumUniqKey values for higher EPS
- **Horizontal Scaling**: Add more submodules with distributed contributions
- **Temporal Scaling**: Reduce period values for increased frequency
- **Hybrid Scaling**: Combine multiple approaches for optimal performance

#### 2. Resource Efficiency Considerations
- **Memory Impact**: Higher unique keys require more memory
- **CPU Usage**: Shorter periods increase CPU utilization
- **I/O Throughput**: Balance EPS with storage and network capabilities
- **System Limits**: Respect operating system and hardware constraints

## 🔒 Advanced Safety & Security Features

### 1. Safe YAML Editing System
The application implements a sophisticated YAML editing system that ensures data integrity:

#### Token-Based Precision Editing
```python
# Example of token-based editing logic
def update_specific_value(file_path, key_path, new_value):
    """
    Updates only the specific value while preserving all formatting
    """
    # Load YAML with structure preservation
    yaml_data = ruamel.yaml.load(file_content, Loader=ruamel.yaml.RoundTripLoader)
    
    # Navigate to specific key without affecting surrounding structure
    keys = key_path.split('.')
    current = yaml_data
    for key in keys[:-1]:
        current = current[key]
    
    # Update only the target value
    current[keys[-1]] = new_value
    
    # Write back with preserved formatting, comments, and whitespace
    with open(file_path, 'w') as f:
        ruamel.yaml.dump(yaml_data, f, Dumper=ruamel.yaml.RoundTripDumper)
```

#### Format and Comment Preservation Features
- **Comment Retention**: All YAML comments are preserved during edits
- **Whitespace Maintenance**: Original indentation and spacing maintained
- **Structure Integrity**: YAML structure and hierarchy preserved
- **Quote Preservation**: Original quote types (single/double) maintained
- **Order Maintenance**: Key order in YAML files preserved

### 2. Comprehensive Backup & Rollback System

#### Automatic Backup Creation
```python
def create_backup(file_path):
    """
    Creates timestamped backup before any modification
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.name}.bak.{timestamp}"
    backup_path = BACKUPS_DIR / backup_name
    
    # Create backup with metadata
    shutil.copy2(file_path, backup_path)
    
    # Store backup metadata
    metadata = {
        "original_file": str(file_path),
        "backup_time": timestamp,
        "file_size": file_path.stat().st_size,
        "checksum": calculate_md5_checksum(file_path)
    }
    
    return backup_path, metadata
```

#### Backup Management Features
- **Timestamped Backups**: Format: `filename.bak.YYYYMMDD_HHMMSS`
- **Retention Policy**: Configurable retention period (default: 7 days)
- **Metadata Storage**: Backup creation time, file size, checksums
- **Compression**: Optional compression for large configuration files
- **Restore Validation**: Verify backup integrity before restoration

#### Rollback Capabilities
```python
def rollback_to_backup(original_file, backup_file):
    """
    Safe rollback with validation
    """
    # Validate backup integrity
    if not validate_backup_integrity(backup_file):
        raise BackupCorruptedException("Backup file is corrupted")
    
    # Create backup of current state before rollback
    emergency_backup = create_emergency_backup(original_file)
    
    try:
        # Perform atomic replacement
        shutil.copy2(backup_file, original_file)
        validate_yaml_syntax(original_file)
        return True
    except Exception as e:
        # Restore from emergency backup if rollback fails
        shutil.copy2(emergency_backup, original_file)
        raise RollbackFailedException(f"Rollback failed: {e}")
```

### 3. Conflict Detection & Resolution

#### Checksum-Based Change Detection
```python
class FileIntegrityManager:
    """
    Manages file integrity and detects concurrent modifications
    """
    def __init__(self):
        self.file_checksums = {}
    
    def calculate_checksum(self, file_path):
        """Calculate MD5 checksum for change detection"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def detect_external_changes(self, file_path, expected_checksum):
        """Detect if file was modified externally"""
        current_checksum = self.calculate_checksum(file_path)
        return current_checksum != expected_checksum
```

#### Conflict Resolution Strategies
- **Detection**: MD5 checksums detect external file modifications
- **User Notification**: Clear alerts about concurrent changes
- **Resolution Options**: Reload, merge, or overwrite conflict resolution
- **Change Tracking**: Audit trail of all modifications
- **Lock Prevention**: Advisory locking to prevent simultaneous edits

### 4. Atomic Operations & Transaction Safety

#### Atomic File Operations
```python
def atomic_file_write(file_path, content):
    """
    Atomic file write using temporary files and atomic moves
    """
    temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
    
    try:
        # Write to temporary file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        
        # Validate written content
        validate_yaml_syntax(temp_file)
        
        # Atomic move (rename is atomic on most filesystems)
        temp_file.replace(file_path)
        
    except Exception as e:
        # Clean up temporary file on error
        if temp_file.exists():
            temp_file.unlink()
        raise AtomicWriteException(f"Atomic write failed: {e}")
```

## 📝 Comprehensive Logging & Audit System

### 1. Multi-Level Logging Architecture

#### Application Logs - Main System Activity
**Location**: `logs/vudatasim-webui.log`
**Purpose**: Primary application logging with structured format

```python
# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vudatasim-webui.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Example log entries
2025-10-06 10:15:23,456 - core.binary_manager - INFO - Started binary vuDataSim with PID 12345
2025-10-06 10:15:24,789 - core.yaml_editor - INFO - Created backup: backups/conf.yml.bak.20251006_101524
2025-10-06 10:15:25,123 - core.eps_calculator - INFO - Calculated EPS for WebLogModule: 5000.0 events/sec
2025-10-06 10:15:26,456 - ui.app - WARNING - Configuration checksum mismatch detected for DatabaseModule
```

#### Binary Process Logs - Individual Process Output
**Location**: `logs/ui-<timestamp>-<counter>.log`
**Purpose**: Capture stdout/stderr from vuDataSim binary processes

```bash
# Example binary log file: logs/ui-20251006_101523-1.log
[2025-10-06 10:15:23] vuDataSim v2.1.0 starting...
[2025-10-06 10:15:23] Loading configuration from /path/to/conf.d/
[2025-10-06 10:15:24] Initialized WebLogModule with 25000 unique keys
[2025-10-06 10:15:24] Starting data generation at 5000 EPS
[2025-10-06 10:15:25] Generated 5000 events in period 1s
[2025-10-06 10:15:26] Generated 5000 events in period 1s
```

#### Audit Trail Logs - Configuration Changes
**Location**: `logs/audit-<date>.log`
**Purpose**: Track all configuration modifications for compliance

```python
# Audit log entry structure
{
    "timestamp": "2025-10-06T10:15:23.456Z",
    "user": "system",
    "action": "config_update",
    "target": "/conf.d/WebLogModule/conf.yml",
    "changes": {
        "uniquekey.NumUniqKey": {"old": 1000, "new": 25000},
        "period": {"old": "2s", "new": "1s"}
    },
    "eps_impact": {"old": 500.0, "new": 25000.0},
    "backup_created": "backups/conf.yml.bak.20251006_101523"
}
```

### 2. Log Rotation & Management

#### Automatic Log Rotation
```python
class LogRotationManager:
    """
    Manages log file rotation and cleanup
    """
    def __init__(self, max_size=10*1024*1024, backup_count=5):
        self.max_size = max_size  # 10MB default
        self.backup_count = backup_count
    
    def rotate_if_needed(self, log_file):
        """Rotate log file if size exceeds maximum"""
        if log_file.stat().st_size > self.max_size:
            # Rotate existing backups
            for i in range(self.backup_count - 1, 0, -1):
                old_backup = log_file.with_suffix(f'.{i}')
                new_backup = log_file.with_suffix(f'.{i+1}')
                if old_backup.exists():
                    old_backup.rename(new_backup)
            
            # Create new backup from current log
            log_file.rename(log_file.with_suffix('.1'))
            
            # Create new empty log file
            log_file.touch()
```

### 3. Error Handling & Recovery

#### Comprehensive Error Logging
```python
def log_error_with_context(logger, error, context):
    """
    Log errors with comprehensive context information
    """
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context,
        "timestamp": datetime.utcnow().isoformat(),
        "system_info": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "memory_usage": psutil.virtual_memory()._asdict()
        }
    }
    
    logger.error(f"Error occurred: {json.dumps(error_info, indent=2)}")
```

#### Recovery Procedures
- **Automatic Recovery**: System attempts automatic recovery from common errors
- **Graceful Degradation**: Continues operation with reduced functionality when possible
- **Error Reporting**: Detailed error reports for debugging and troubleshooting
- **State Preservation**: Maintains system state during error conditions

## 🚨 Comprehensive Troubleshooting Guide

### 1. Common Issues & Solutions

#### Binary Management Issues

**Issue**: "Binary not found" Error
```bash
# Symptoms
ERROR - Binary not found: /path/to/bin/vuDataSim
FileNotFoundError: Binary file does not exist
```

**Solutions**:
```bash
# 1. Verify binary location
ls -la ../bin/
# Should show executable vuDataSim files

# 2. Check file permissions
chmod +x ../bin/vuDataSim
chmod +x ../bin/RakvuDataSim
chmod +x ../bin/finalvudatasim

# 3. Verify binary functionality
../bin/vuDataSim --version
```

**Issue**: Process Fails to Start
```bash
# Symptoms
ERROR - Failed to start binary vuDataSim
Process exited with code 1
```

**Diagnostic Steps**:
```bash
# 1. Check binary dependencies
ldd ../bin/vuDataSim
# Verify all shared libraries are available

# 2. Test manual execution
cd ../bin/
./vuDataSim
# Check for error messages

# 3. Review process logs
tail -f logs/ui-*.log
# Look for specific error messages
```

#### Configuration File Issues

**Issue**: "Configuration file not found"
```bash
# Symptoms
ERROR - Main config file not found: /path/to/conf.d/conf.yml
FileNotFoundError: Configuration directory missing
```

**Solutions**:
```bash
# 1. Create configuration structure
mkdir -p ../conf.d/WebLogModule
mkdir -p ../conf.d/DatabaseModule

# 2. Create main configuration file
cat > ../conf.d/conf.yml << EOF
include_module_dirs:
  WebLogModule:
    enabled: true
  DatabaseModule:
    enabled: true
EOF

# 3. Create module configuration
cat > ../conf.d/WebLogModule/conf.yml << EOF
enabled: true
uniquekey:
  name: "host"
  DataType: IPv4
  ValueType: "RandomFixed"
  Value: "10.10.10.1"
  NumUniqKey: 1000
period: 1s
EOF
```

**Issue**: YAML Syntax Errors
```bash
# Symptoms
ERROR - YAML parsing failed
ruamel.yaml.scanner.ScannerError: found character that cannot start any token
```

**Diagnostic & Repair**:
```bash
# 1. Validate YAML syntax
python3 -c "
import yaml
with open('../conf.d/conf.yml', 'r') as f:
    try:
        yaml.safe_load(f)
        print('YAML syntax is valid')
    except yaml.YAMLError as e:
        print(f'YAML syntax error: {e}')
"

# 2. Use backup for recovery
ls -la backups/
# Find latest backup
cp backups/conf.yml.bak.20251006_101523 ../conf.d/conf.yml
```

#### Network & Connectivity Issues

**Issue**: "Port already in use"
```bash
# Symptoms
ERROR - Port 8501 is already in use
OSError: [Errno 98] Address already in use
```

**Solutions**:
```bash
# 1. Find process using port
sudo netstat -tlnp | grep :8501
# or
sudo lsof -i :8501

# 2. Kill existing process
sudo kill -9 <PID>

# 3. Change port in configuration
python3 config_manager.py network
# Set new port value

# 4. Alternative: Use different port
streamlit run src/ui/app.py --server.port 8501
```

**Issue**: SSH Connection Failures (Remote Execution)
```bash
# Symptoms
ERROR - Failed to connect to remote host 216.48.191.10
paramiko.ssh_exception.AuthenticationException: Authentication failed
```

**Solutions**:
```bash
# 1. Test SSH connectivity
ssh -i ~/.ssh/id_rsa vunet@216.48.191.10
# Should connect without password

# 2. Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# 3. Update SSH key path in configuration
python3 config_manager.py paths
# Set correct SSH key path

# 4. Add SSH key to remote server
ssh-copy-id -i ~/.ssh/id_rsa.pub vunet@216.48.191.10
```

#### Permission & Access Issues

**Issue**: "Permission denied" Errors
```bash
# Symptoms
ERROR - Permission denied: logs/vudatasim-webui.log
PermissionError: [Errno 13] Permission denied
```

**Solutions**:
```bash
# 1. Set directory permissions
chmod 755 logs/ backups/
chmod 644 config.yaml

# 2. Check file ownership
ls -la logs/ backups/
# Ensure files are owned by current user

# 3. Fix ownership if needed
sudo chown -R $USER:$USER logs/ backups/

# 4. Create directories if missing
mkdir -p logs backups
chmod 755 logs backups
```

### 2. Advanced Debugging Techniques

#### Enable Comprehensive Debug Logging
```python
# Add to main.py or src/ui/app.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Enable debug for specific modules
logging.getLogger('core.binary_manager').setLevel(logging.DEBUG)
logging.getLogger('core.yaml_editor').setLevel(logging.DEBUG)
logging.getLogger('core.eps_calculator').setLevel(logging.DEBUG)
```

#### System Diagnostics Script
```python
#!/usr/bin/env python3
"""
System diagnostics script for vuDataSim Web UI
"""
import sys
import os
from pathlib import Path
import subprocess
import yaml

def run_diagnostics():
    """Run comprehensive system diagnostics"""
    print("=== vuDataSim Web UI Diagnostics ===\n")
    
    # 1. Python environment
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # 2. Directory structure
    print("\n=== Directory Structure ===")
    for path in ['../bin', '../conf.d', 'logs', 'backups']:
        if Path(path).exists():
            print(f"✓ {path} exists")
        else:
            print(f"✗ {path} missing")
    
    # 3. Binary availability
    print("\n=== Binary Status ===")
    bin_dir = Path('../bin')
    if bin_dir.exists():
        for binary in bin_dir.glob('*'):
            if binary.is_file() and os.access(binary, os.X_OK):
                print(f"✓ {binary.name} (executable)")
            else:
                print(f"✗ {binary.name} (not executable)")
    
    # 4. Configuration validation
    print("\n=== Configuration Status ===")
    config_files = [
        'config.yaml',
        '../conf.d/conf.yml'
    ]
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                yaml.safe_load(f)
            print(f"✓ {config_file} (valid YAML)")
        except FileNotFoundError:
            print(f"✗ {config_file} (missing)")
        except yaml.YAMLError as e:
            print(f"✗ {config_file} (invalid YAML: {e})")
    
    # 5. Dependencies check
    print("\n=== Dependencies Status ===")
    required_packages = [
        'streamlit', 'yaml', 'ruamel.yaml', 'psutil', 
        'paramiko', 'clickhouse_driver', 'dateutil'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
    
    # 6. Port availability
    print("\n=== Network Status ===")
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 8501))
            if result == 0:
                print("✗ Port 8501 is in use")
            else:
                print("✓ Port 8501 is available")
    except Exception as e:
        print(f"? Port check failed: {e}")

if __name__ == "__main__":
    run_diagnostics()
```

#### Performance Monitoring & Analysis
```python
def monitor_performance():
    """Monitor system performance and resource usage"""
    import psutil
    import time
    
    print("=== Performance Monitoring ===")
    
    # CPU and Memory usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Memory Usage: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
    print(f"Disk Usage: {disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")
    
    # Process monitoring
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        if 'vuDataSim' in proc.info['name'] or 'python' in proc.info['name']:
            print(f"Process: {proc.info['name']} (PID: {proc.info['pid']}) - CPU: {proc.info['cpu_percent']}% - Memory: {proc.info['memory_percent']:.1f}%")
```

### 3. Log Analysis & Error Investigation

#### Log Analysis Commands
```bash
# 1. Recent errors
grep -i error logs/vudatasim-webui.log | tail -20

# 2. EPS calculation issues
grep -i "eps" logs/vudatasim-webui.log | tail -10

# 3. Configuration changes
grep -i "config\|backup\|yaml" logs/vudatasim-webui.log | tail -15

# 4. Binary process issues
grep -i "binary\|process\|pid" logs/vudatasim-webui.log | tail -10

# 5. Real-time log monitoring
tail -f logs/vudatasim-webui.log
```

#### Automated Error Detection
```bash
#!/bin/bash
# error_detector.sh - Automated error detection script

echo "=== Error Detection Report ==="
echo "Generated: $(date)"
echo

# Check for critical errors
echo "=== Critical Errors ==="
grep -i "critical\|fatal\|exception" logs/vudatasim-webui.log | tail -5

# Check for warnings
echo -e "\n=== Recent Warnings ==="
grep -i "warning\|warn" logs/vudatasim-webui.log | tail -5

# Check binary status
echo -e "\n=== Binary Process Status ==="
pgrep -f vuDataSim && echo "vuDataSim processes running" || echo "No vuDataSim processes found"

# Check configuration integrity
echo -e "\n=== Configuration Integrity ==="
python3 -c "
import yaml
try:
    with open('../conf.d/conf.yml', 'r') as f:
        yaml.safe_load(f)
    print('✓ Main configuration is valid')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"

# Check disk space
echo -e "\n=== Disk Space Status ==="
df -h . | awk 'NR==2 {print "Disk usage: " $5 " of " $2 " used"}'
```

### 4. Recovery Procedures

#### Emergency Recovery Steps
```bash
#!/bin/bash
# emergency_recovery.sh - Emergency system recovery

echo "=== Emergency Recovery Procedure ==="

# 1. Stop all processes
echo "Stopping all vuDataSim processes..."
pkill -f vuDataSim
pkill -f streamlit

# 2. Backup current state
echo "Creating emergency backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp -r ../conf.d "../conf.d.emergency_backup_$timestamp"

# 3. Restore from latest backup
echo "Restoring from latest backup..."
latest_backup=$(ls -t backups/*.bak.* | head -1)
if [ -n "$latest_backup" ]; then
    cp "$latest_backup" ../conf.d/conf.yml
    echo "Restored from: $latest_backup"
else
    echo "No backups found - manual intervention required"
fi

# 4. Validate restoration
echo "Validating restored configuration..."
python3 -c "
import yaml
try:
    with open('../conf.d/conf.yml', 'r') as f:
        yaml.safe_load(f)
    print('✓ Restoration successful')
except Exception as e:
    print(f'✗ Restoration failed: {e}')
"

# 5. Restart system
echo "Restarting system..."
python3 main.py &
echo "System recovery complete"
```

## 🔄 Development Guide & Architecture

### 1. Project Architecture & Design Patterns

#### Modular Architecture Overview
The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────┐
│                Web Interface Layer              │
│  (Streamlit UI - src/ui/app.py)                │
├─────────────────────────────────────────────────┤
│              Business Logic Layer               │
│  ┌─────────────┬─────────────┬─────────────────┐ │
│  │   Process   │    YAML     │      EPS        │ │
│  │ Management  │   Editor    │   Calculator    │ │
│  └─────────────┴─────────────┴─────────────────┘ │
├─────────────────────────────────────────────────┤
│            Configuration Layer                  │
│  (YAML-based configuration management)         │
├─────────────────────────────────────────────────┤
│              External Integration               │
│  ┌─────────────┬─────────────┬─────────────────┐ │
│  │   Binary    │     SSH     │   ClickHouse    │ │
│  │ Execution   │  Remote     │   Database      │ │
│  └─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────┘
```

#### Design Patterns Used
- **Singleton Pattern**: Configuration manager, process manager instances
- **Factory Pattern**: Binary process creation and management
- **Observer Pattern**: Real-time UI updates and status monitoring
- **Strategy Pattern**: Different EPS calculation algorithms
- **Command Pattern**: Configuration update operations with undo/redo
- **Repository Pattern**: Configuration file access and manipulation

### 2. Detailed Source Code Structure

#### Core Business Logic Modules (`src/core/`)

**config.py** - Configuration Management System
```python
"""
Responsibilities:
1. YAML configuration loading and parsing
2. Runtime configuration updates
3. Default value management
4. Configuration validation
"""

class Config:
    # Configuration loading with fallback defaults
    # Dot notation access (e.g., 'network.remote_host')
    # Runtime updates with persistence
    # Type-safe configuration access

# Global configuration constants for backward compatibility
PRIMARY_BINARY = _config.get('binaries.primary_binary', 'vuDataSim')
REMOTE_HOST = _config.get('network.remote_host', '216.48.191.10')
# ... additional configuration exports
```

**binary_manager.py** - Process Lifecycle Management
```python
"""
Responsibilities:
1. Binary process lifecycle (start/stop/monitor)
2. Process status tracking and reporting
3. Log file management
4. Remote execution via SSH
5. Timeout and resource management
"""

class ProcessManager:
    def __init__(self):
        self.processes: Dict[str, Dict[str, Any]] = {}
        # Process tracking dictionary structure:
        # {
        #     "binary_name": {
        #         "process": subprocess.Popen,
        #         "start_time": datetime,
        #         "log_file": Path,
        #         "timeout": int,
        #         "status": str
        #     }
        # }
    
    # Methods: start_binary(), stop_binary(), get_status(), 
    #          list_binaries(), cleanup_finished_processes()
```

**yaml_editor.py** - Safe YAML Editing Engine
```python
"""
Responsibilities:
1. YAML file reading with structure preservation
2. Atomic file operations for data integrity
3. Backup creation and management
4. Conflict detection via checksums
5. Duration parsing and formatting
"""

class SafeYAMLEditor:
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096
        # ruamel.yaml configuration for preservation
    
    # Methods: read_module_config(), write_module_config(),
    #          _create_backup(), _calculate_checksum()
```

**eps_calculator.py** - EPS Calculation Algorithms
```python
"""
Responsibilities:
1. Module and submodule discovery
2. EPS calculation using complex formulas
3. Configuration parsing and validation
4. Auto-tuner optimization algorithms
5. Batch EPS calculation across modules
"""

class EPSCalculator:
    # EPS Formula Implementation:
    # EPS = (ModuleLevelUniqueKeys × ∑(SubmoduleContributions)) / periodSeconds
    
    def calculate_eps(self, module_name, module_uniquekey=None, 
                     module_period=None, submodule_overrides=None):
        # Complex calculation logic with override support
        # Submodule aggregation and contribution calculation
        # Period conversion and validation
```

**diff_viewer.py** - Change Preview System
```python
"""
Responsibilities:
1. Unified diff generation between configurations
2. Token-level change highlighting
3. Change summary generation
4. Preview before apply functionality
"""

class DiffViewer:
    # Methods: generate_yaml_diff(), preview_module_changes(),
    #          _extract_key_changes(), _generate_change_summary()
```

**clickhouse_monitor.py** - Database Integration
```python
"""
Responsibilities:
1. ClickHouse database connectivity
2. Real-time metrics query execution
3. Kafka topic monitoring
4. Historical data retrieval
"""

class ClickHouseMonitor:
    # Methods: connect(), execute_query(), get_eps_for_topic(),
    #          get_historical_eps()
```

#### User Interface Layer (`src/ui/`)

**app.py** - Streamlit Web Application
```python
"""
Responsibilities:
1. Web interface layout and navigation
2. User interaction handling
3. Real-time data display
4. Form processing and validation
5. Integration with core business logic
"""

# Main application structure:
def main():
    # Application configuration and setup
    # Sidebar navigation
    # Page routing to different interfaces
    
def show_dashboard():
    # System overview and metrics
    
def show_binary_control():
    # Process management interface
    
def show_module_browser():
    # Configuration navigation
    
def show_eps_tuner():
    # Performance optimization interface
    
def show_config_editor():
    # Safe configuration editing
```

### 3. Adding New Features

#### Step-by-Step Development Process

**1. Core Logic Implementation**
```python
# Example: Adding new monitoring feature
# File: src/core/monitoring.py

"""
New monitoring system for advanced metrics
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AdvancedMonitor:
    """Advanced monitoring capabilities"""
    
    def __init__(self):
        self.metrics_cache = {}
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        # Implementation here
        pass
        
    def analyze_performance_trends(self) -> List[Dict]:
        """Analyze performance over time"""
        # Implementation here
        pass

# Global instance
advanced_monitor = AdvancedMonitor()
```

**2. Configuration Updates**
```yaml
# Add to config.yaml
monitoring:
  enabled: true
  collection_interval: 30  # seconds
  retention_period: "7d"
  alert_thresholds:
    cpu_usage: 80
    memory_usage: 85
    disk_usage: 90
```

**3. UI Integration**
```python
# Add to src/ui/app.py
def show_advanced_monitoring():
    """Advanced monitoring interface"""
    st.header("📈 Advanced Monitoring")
    
    # Real-time metrics display
    metrics = advanced_monitor.collect_system_metrics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CPU Usage", f"{metrics.get('cpu', 0):.1f}%")
    with col2:
        st.metric("Memory Usage", f"{metrics.get('memory', 0):.1f}%")
    with col3:
        st.metric("Disk Usage", f"{metrics.get('disk', 0):.1f}%")
    
    # Performance trends
    trends = advanced_monitor.analyze_performance_trends()
    if trends:
        st.line_chart(pd.DataFrame(trends))

# Add to navigation
if page == "Advanced Monitoring":
    show_advanced_monitoring()
```

### 4. Code Style & Standards

#### Python Code Style Guidelines
```python
"""
Code style requirements and examples
"""
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ExampleClass:
    """
    Example class demonstrating code style standards
    
    Attributes:
        attribute_name (str): Description of attribute
        another_attribute (int): Another attribute description
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        """
        Initialize class with required parameters
        
        Args:
            param1 (str): Required string parameter
            param2 (Optional[int]): Optional integer parameter
            
        Raises:
            ValueError: If param1 is empty
        """
        if not param1:
            raise ValueError("param1 cannot be empty")
            
        self.attribute_name = param1
        self.another_attribute = param2 or 0
        
    def example_method(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Example method with proper type hints and documentation
        
        Args:
            input_data (Dict[str, Any]): Input data dictionary
            
        Returns:
            List[str]: Processed data as list of strings
            
        Raises:
            TypeError: If input_data is not a dictionary
        """
        try:
            # Implementation with proper error handling
            result = []
            for key, value in input_data.items():
                processed_value = self._process_value(value)
                result.append(f"{key}:{processed_value}")
                
            logger.info(f"Processed {len(result)} items successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            raise
            
    def _process_value(self, value: Any) -> str:
        """
        Private method for value processing
        
        Args:
            value (Any): Value to process
            
        Returns:
            str: Processed value as string
        """
        return str(value).strip()
```

#### Configuration Code Standards
```python
# Configuration access patterns
def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Standard pattern for configuration access
    
    Args:
        key_path (str): Dot notation key path (e.g., 'network.remote_host')
        default (Any): Default value if key not found
        
    Returns:
        Any: Configuration value or default
    """
    config = get_config()
    return config.get(key_path, default)

# Error handling standards
def safe_operation_with_logging():
    """Standard error handling pattern"""
    try:
        # Operation logic here
        result = perform_operation()
        logger.info("Operation completed successfully")
        return result
        
    except SpecificException as e:
        logger.error(f"Specific error occurred: {e}")
        # Handle specific error
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        # Handle general error
        raise RuntimeError(f"Operation failed: {e}") from e
```

#### Testing Standards
```python
"""
Testing standards and examples
File: tests/test_example.py
"""
import pytest
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.example import ExampleClass

class TestExampleClass(unittest.TestCase):
    """Test cases for ExampleClass"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.example = ExampleClass("test_param")
        
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.example.attribute_name, "test_param")
        self.assertEqual(self.example.another_attribute, 0)
        
    def test_example_method_success(self):
        """Test successful method execution"""
        input_data = {"key1": "value1", "key2": "value2"}
        result = self.example.example_method(input_data)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn("key1:value1", result)
        
    def test_example_method_error_handling(self):
        """Test error handling in method"""
        with self.assertRaises(TypeError):
            self.example.example_method("invalid_input")
            
    @patch('src.core.example.logger')
    def test_logging(self, mock_logger):
        """Test proper logging behavior"""
        input_data = {"test": "data"}
        self.example.example_method(input_data)
        
        mock_logger.info.assert_called_once()
        
if __name__ == '__main__':
    unittest.main()
```

### 5. Performance Optimization Guidelines

#### Memory Management
```python
def memory_efficient_processing(large_dataset: List[Dict]) -> None:
    """
    Example of memory-efficient processing
    """
    # Use generators for large datasets
    def process_chunk(chunk):
        for item in chunk:
            yield process_item(item)
    
    # Process in chunks to avoid memory issues
    chunk_size = 1000
    for i in range(0, len(large_dataset), chunk_size):
        chunk = large_dataset[i:i + chunk_size]
        for processed_item in process_chunk(chunk):
            handle_processed_item(processed_item)
```

#### Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def async_operation():
    """Example of async operation for better performance"""
    loop = asyncio.get_event_loop()
    
    # CPU-bound operations in thread pool
    with ThreadPoolExecutor() as executor:
        tasks = []
        for item in items_to_process:
            task = loop.run_in_executor(executor, cpu_intensive_function, item)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
```

### 6. Security Considerations

#### Input Validation
```python
def validate_configuration_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize configuration input
    """
    validated = {}
    
    # Validate numeric ranges
    if 'unique_key' in data:
        unique_key = int(data['unique_key'])
        if not (1 <= unique_key <= MAX_UNIQUE_KEY):
            raise ValueError(f"unique_key must be between 1 and {MAX_UNIQUE_KEY}")
        validated['unique_key'] = unique_key
    
    # Validate string formats
    if 'period' in data:
        period = str(data['period']).strip()
        if not re.match(r'^\d+(ms|s|m|h)$', period):
            raise ValueError("Invalid period format")
        validated['period'] = period
    
    return validated
```

#### File System Security
```python
def secure_file_operation(file_path: Path) -> None:
    """
    Secure file operations with proper validation
    """
    # Validate path is within allowed directories
    allowed_dirs = [BASE_DIR, CONF_D_DIR, LOGS_DIR, BACKUPS_DIR]
    if not any(file_path.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs):
        raise SecurityError(f"Access denied to path: {file_path}")
    
    # Check file permissions
    if file_path.exists() and not os.access(file_path, os.R_OK | os.W_OK):
        raise PermissionError(f"Insufficient permissions for: {file_path}")
```

## 📄 Project Licensing & Support

### License Information
This project is part of the vuDataSim ecosystem. The software is proprietary and subject to the terms and conditions specified in your organization's licensing agreement.

### Support Channels

#### 1. Self-Service Resources
- **Documentation**: This comprehensive README
- **Configuration Guide**: `CONFIG.md` for detailed configuration help
- **Troubleshooting**: Extensive troubleshooting section above
- **Log Analysis**: Application logs in `logs/` directory

#### 2. Diagnostic Tools
```bash
# Run system diagnostics
python3 diagnostics.py

# Check configuration status
python3 config_manager.py show

# Monitor system performance
python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"
```

#### 3. Issue Escalation Process
1. **Level 1**: Check logs and run diagnostics
2. **Level 2**: Review configuration and validate setup
3. **Level 3**: Create detailed issue report with:
   - Error messages and stack traces
   - Configuration files (sanitized)
   - System diagnostic output
   - Steps to reproduce the issue

---

**🚀 Happy Data Simulating with vuDataSim Web UI!**

*"Empowering data simulation through intelligent configuration management and real-time performance optimization."*