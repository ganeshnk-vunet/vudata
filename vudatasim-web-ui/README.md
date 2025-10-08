# vuDataSim Web UI

A modern web-based interface for managing vuDataSim binaries and configuration files with safe YAML editing and EPS (Events Per Second) tuning capabilities.

## 🚀 Features

- **Binary Management**: Start, stop, and restart vuDataSim with configurable timeouts
- **Safe YAML Editing**: Preserve formatting and comments when editing configuration files
- **Module Browser**: View and toggle module enabled/disabled status
- **EPS Calculator**: Calculate and visualize Events Per Second for modules and submodules
- **Manual Tuning**: Adjust unique keys and periods with live EPS preview
- **Auto-Tuner**: Automatically suggest optimal configurations for target EPS
- **Backup & Rollback**: Automatic backups with restore capabilities
- **Conflict Detection**: Prevent concurrent modification issues

## 📋 Requirements

- Python 3.8+
- vuDataSim binaries in `../bin/` directory
- Configuration files in `../conf.d/` directory

## 🛠️ Installation

1. **Install dependencies:**
   ```bash
   cd vudatasim-web-ui
   pip install -r requirements.txt
   ```

2. **Verify directory structure:**
   ```
   vudatasim-web-ui/
   ├── src/
   │   ├── core/
   │   │   ├── config.py          # Configuration settings
   │   │   ├── binary_manager.py  # Process management
   │   │   ├── yaml_editor.py     # Safe YAML editing
   │   │   └── eps_calculator.py  # EPS calculations
   │   └── ui/
   │       └── app.py             # Streamlit UI
   ├── logs/                      # Application logs
   ├── backups/                   # Configuration backups
   ├── requirements.txt
   ├── main.py                    # Entry point
   └── README.md

   ../bin/                        # vuDataSim binaries
   ../conf.d/                     # Configuration files
   ```

## 🎯 Usage

### Start the Web Interface

```bash
cd vudatasim-web-ui
python main.py
```

The web interface will be available at: http://localhost:8501

### Using the Interface

#### 1. Dashboard
- View binary status and recent activity
- Monitor total EPS across all modules
- Quick access to recent logs

#### 2. Binary Control
- **Select Binary**: Choose from available binaries (vuDataSim, etc.)
- **Start**: Launch binary with optional timeout
- **Stop**: Gracefully stop running binary
- **Restart**: Stop and start binary
- **Status**: View PID, runtime, and log files

#### 3. Module Browser
- **View Modules**: List all available modules from `conf.d/`
- **Toggle Status**: Enable/disable modules by editing `conf.d/conf.yml`
- **Filter**: Show only enabled or all modules
- **EPS Preview**: See current EPS for each module

#### 4. EPS Tuner
- **Manual Tuning**: Adjust unique keys and periods with live EPS calculation
- **Auto-Tuner**: Set target EPS and get suggested configurations
- **Preview Changes**: See calculated EPS before applying
- **Validation**: Ensure values are within acceptable ranges

#### 5. Configuration Editor
- **Edit Module Configs**: Modify `uniquekey.NumUniqKey` and `period` values
- **Safe Editing**: Preserves YAML formatting and comments
- **Backup Creation**: Automatic backups before any changes
- **Conflict Detection**: Prevents concurrent modification issues

## ⚙️ Configuration

### Main Configuration (`conf.d/conf.yml`)
```yaml
include_module_dirs:
  ModuleName:
    enabled: true  # Toggle module on/off
```

### Module Configuration (`conf.d/ModuleName/conf.yml`)
```yaml
enabled: true
uniquekey:
  name: "host"
  DataType: IPv4
  ValueType: "RandomFixed"
  Value: "10.10.10.1"
  NumUniqKey: 25000  # Edit this value
period: 1s           # Edit this value
```

### Submodule Configuration (`conf.d/ModuleName/submodule.yml`)
```yaml
uniquekey:
  name: "fields,instance"
  DataType: String
  ValueType: RandomFixed
  Value: "value"
  NumUniqKey: 3  # Edit this value
```

## 📊 EPS Calculation

The system calculates EPS using the formula:
```
EPS = (ModuleLevelUniqueKeys * Sum(submodule contributions)) / periodSeconds
```

Where:
- **ModuleLevelUniqueKeys**: `uniquekey.NumUniqKey` from module config (default: 1)
- **Submodule contributions**: Each submodule's `NumUniqKey` * multiplier (default: 1)
- **periodSeconds**: Period converted to seconds (e.g., "1s" = 1, "250ms" = 0.25)

## 🔒 Safety Features

### Safe YAML Editing
- **Token-based editing**: Only changes specific values, preserves all formatting
- **Comment preservation**: Maintains YAML comments and structure
- **Atomic writes**: Uses temporary files and atomic moves
- **Validation**: Validates YAML syntax before writing

### Backup & Rollback
- **Automatic backups**: Creates timestamped backups before any changes
- **Backup location**: `backups/` directory with `.bak.timestamp` naming
- **Rollback capability**: Restore from any backup
- **Retention**: Configurable backup retention period

### Conflict Detection
- **Checksum validation**: Detects external file modifications
- **User notification**: Alerts users to concurrent changes
- **Reload requirement**: Forces reload before allowing edits

## 📝 Logging

Application logs are stored in:
- **File**: `logs/vudatasim-webui.log`
- **Binary logs**: `logs/ui-<timestamp>.log`
- **Rotation**: Automatic log rotation (10MB max, 5 backups)

## 🚨 Troubleshooting

### Common Issues

1. **"Binary not found"**
   - Ensure binaries are in `../bin/` directory
   - Check file permissions (should be executable)

2. **"Configuration file not found"**
   - Verify `../conf.d/` directory exists
   - Check that module directories contain `conf.yml` files

3. **"Port already in use"**
   - Change port in `src/core/config.py`
   - Or kill existing process using the port

4. **"Permission denied"**
   - Ensure write permissions for `logs/` and `backups/` directories
   - Check binary execution permissions

### Debug Mode

Enable debug logging by modifying `src/ui/app.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Development

### Project Structure
```
src/
├── core/           # Core business logic
│   ├── config.py      # Configuration management
│   ├── binary_manager.py  # Process management
│   ├── yaml_editor.py     # Safe YAML editing
│   └── eps_calculator.py  # EPS calculations
└── ui/            # User interface
    └── app.py         # Streamlit application
```

### Adding New Features

1. **Core Logic**: Add to appropriate module in `src/core/`
2. **UI Components**: Extend `src/ui/app.py`
3. **Configuration**: Update `src/core/config.py`
4. **Testing**: Add tests to `tests/` directory

### Code Style

- Use type hints for all function parameters and return values
- Follow PEP 8 style guidelines
- Add docstrings for all public functions
- Handle exceptions gracefully with appropriate logging

## 📄 License

This project is part of the vuDataSim ecosystem. See your organization's licensing terms for usage restrictions.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs in `logs/`
3. Check binary logs for runtime issues
4. Verify configuration file syntax

---

**Happy Data Simulating! 🚀**