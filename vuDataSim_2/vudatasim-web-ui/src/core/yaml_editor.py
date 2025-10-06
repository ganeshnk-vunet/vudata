"""
Safe YAML editor that preserves formatting and comments
"""
import os
import re
import yaml
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from .config import CONF_D_DIR, BACKUPS_DIR, MAX_UNIQUE_KEY

logger = logging.getLogger(__name__)


class SafeYAMLEditor:
    """Safe YAML editor that preserves formatting and comments"""

    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _create_backup(self, file_path: Path) -> Path:
        """Create timestamped backup of file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f"{file_path.name}.bak.{timestamp}"

        # Ensure backups directory exists
        BACKUPS_DIR.mkdir(exist_ok=True)

        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path

    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to seconds"""
        if not duration_str:
            return 1.0

        # Handle common duration formats
        duration_str = duration_str.strip()

        # Match patterns like "1s", "250ms", "1m", "2h"
        match = re.match(r'^(\d+)(ms|s|m|h)$', duration_str)
        if not match:
            raise ValueError(f"Invalid duration format: {duration_str}")

        value, unit = match.groups()
        value = int(value)

        multipliers = {
            'ms': 0.001,
            's': 1.0,
            'm': 60.0,
            'h': 3600.0
        }

        return value * multipliers[unit]

    def _format_duration(self, seconds: float) -> str:
        """Format seconds back to duration string"""
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        else:
            return f"{int(seconds // 3600)}h"

    def read_main_config(self) -> Tuple[Dict[str, Any], str]:
        """
        Read main configuration file with checksum

        Returns:
            Tuple of (config_data, checksum)
        """
        main_config_path = CONF_D_DIR / "conf.yml"

        if not main_config_path.exists():
            raise FileNotFoundError(f"Main config file not found: {main_config_path}")

        try:
            with open(main_config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse YAML while preserving structure
            data = self.yaml.load(content)

            # Calculate checksum
            checksum = self._calculate_checksum(main_config_path)

            return data, checksum

        except Exception as e:
            logger.error(f"Error reading main config: {e}")
            raise

    def write_main_config(self, data: Dict[str, Any], original_checksum: str) -> Dict[str, Any]:
        """
        Write main configuration file with conflict detection

        Args:
            data: Configuration data to write
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        main_config_path = CONF_D_DIR / "conf.yml"

        # Check for concurrent modifications
        current_checksum = self._calculate_checksum(main_config_path)
        if current_checksum != original_checksum:
            raise ValueError(
                "File has been modified since it was read. "
                "Please reload and try again."
            )

        # Create backup
        backup_path = self._create_backup(main_config_path)

        # Write to temporary file first
        temp_path = main_config_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)

            # Atomic move
            temp_path.replace(main_config_path)

            new_checksum = self._calculate_checksum(main_config_path)

            logger.info(f"Successfully updated main config: {main_config_path}")

            return {
                "success": True,
                "backup_path": str(backup_path),
                "new_checksum": new_checksum,
                "message": "Main configuration updated successfully"
            }

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()

            logger.error(f"Error writing main config: {e}")
            raise

    def read_module_config(self, module_name: str) -> Tuple[Dict[str, Any], str]:
        """
        Read module configuration file

        Args:
            module_name: Name of the module

        Returns:
            Tuple of (config_data, checksum)
        """
        module_dir = CONF_D_DIR / module_name
        config_path = module_dir / "conf.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Module config not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            data = self.yaml.load(content)
            checksum = self._calculate_checksum(config_path)

            return data, checksum

        except Exception as e:
            logger.error(f"Error reading module config {module_name}: {e}")
            raise

    def write_module_config(self, module_name: str, data: Dict[str, Any],
                          original_checksum: str) -> Dict[str, Any]:
        """
        Write module configuration file

        Args:
            module_name: Name of the module
            data: Configuration data to write
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        module_dir = CONF_D_DIR / module_name
        config_path = module_dir / "conf.yml"

        # Check for concurrent modifications
        current_checksum = self._calculate_checksum(config_path)
        if current_checksum != original_checksum:
            raise ValueError(
                f"Module {module_name} config has been modified since it was read. "
                "Please reload and try again."
            )

        # Create backup
        backup_path = self._create_backup(config_path)

        # Write to temporary file first
        temp_path = config_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)

            # Atomic move
            temp_path.replace(config_path)

            new_checksum = self._calculate_checksum(config_path)

            logger.info(f"Successfully updated module config: {module_name}")

            return {
                "success": True,
                "backup_path": str(backup_path),
                "new_checksum": new_checksum,
                "message": f"Module {module_name} configuration updated successfully"
            }

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()

            logger.error(f"Error writing module config {module_name}: {e}")
            raise

    def read_submodule_config(self, module_name: str, submodule_name: str) -> Tuple[Dict[str, Any], str]:
        """
        Read submodule configuration file

        Args:
            module_name: Name of the parent module
            submodule_name: Name of the submodule file (without .yml extension)

        Returns:
            Tuple of (config_data, checksum)
        """
        module_dir = CONF_D_DIR / module_name
        config_path = module_dir / f"{submodule_name}.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Submodule config not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            data = self.yaml.load(content)
            checksum = self._calculate_checksum(config_path)

            return data, checksum

        except Exception as e:
            logger.error(f"Error reading submodule config {module_name}/{submodule_name}: {e}")
            raise

    def write_submodule_config(self, module_name: str, submodule_name: str,
                             data: Dict[str, Any], original_checksum: str) -> Dict[str, Any]:
        """
        Write submodule configuration file

        Args:
            module_name: Name of the parent module
            submodule_name: Name of the submodule file (without .yml extension)
            data: Configuration data to write
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        module_dir = CONF_D_DIR / module_name
        config_path = module_dir / f"{submodule_name}.yml"

        # Check for concurrent modifications
        current_checksum = self._calculate_checksum(config_path)
        if current_checksum != original_checksum:
            raise ValueError(
                f"Submodule {module_name}/{submodule_name} config has been modified since it was read. "
                "Please reload and try again."
            )

        # Create backup
        backup_path = self._create_backup(config_path)

        # Write to temporary file first
        temp_path = config_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)

            # Atomic move
            temp_path.replace(config_path)

            new_checksum = self._calculate_checksum(config_path)

            logger.info(f"Successfully updated submodule config: {module_name}/{submodule_name}")

            return {
                "success": True,
                "backup_path": str(backup_path),
                "new_checksum": new_checksum,
                "message": f"Submodule {module_name}/{submodule_name} configuration updated successfully"
            }

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()

            logger.error(f"Error writing submodule config {module_name}/{submodule_name}: {e}")
            raise

    def toggle_module_enabled(self, module_name: str, enabled: bool, original_checksum: str) -> Dict[str, Any]:
        """
        Toggle module enabled status in main config

        Args:
            module_name: Name of module to toggle
            enabled: New enabled state
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        # Read current config
        data, current_checksum = self.read_main_config()

        if current_checksum != original_checksum:
            raise ValueError("Main config has been modified since it was read")

        # Update the specific module
        if "include_module_dirs" not in data:
            raise ValueError("include_module_dirs section not found in main config")

        if module_name not in data["include_module_dirs"]:
            raise ValueError(f"Module {module_name} not found in include_module_dirs")

        # Update only the enabled field
        data["include_module_dirs"][module_name]["enabled"] = enabled

        # Write back
        return self.write_main_config(data, original_checksum)

    def update_module_uniquekey(self, module_name: str, num_uniquekey: int,
                              original_checksum: str) -> Dict[str, Any]:
        """
        Update module uniquekey.NumUniqKey value

        Args:
            module_name: Name of module
            num_uniquekey: New NumUniqKey value
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        if not isinstance(num_uniquekey, int) or num_uniquekey < 1 or num_uniquekey > MAX_UNIQUE_KEY:
            raise ValueError(f"NumUniqKey must be between 1 and {MAX_UNIQUE_KEY}")

        # Read current config
        data, current_checksum = self.read_module_config(module_name)

        if current_checksum != original_checksum:
            raise ValueError(f"Module {module_name} config has been modified since it was read")

        # Update/create uniquekey section
        if "uniquekey" not in data:
            data["uniquekey"] = {}

        data["uniquekey"]["NumUniqKey"] = num_uniquekey

        # Write back
        return self.write_module_config(module_name, data, original_checksum)

    def update_module_period(self, module_name: str, period: str,
                           original_checksum: str) -> Dict[str, Any]:
        """
        Update module period value

        Args:
            module_name: Name of module
            period: New period value (e.g., "1s", "250ms")
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        # Validate period format
        try:
            self._parse_duration(period)
        except ValueError as e:
            raise ValueError(f"Invalid period format: {e}")

        # Read current config
        data, current_checksum = self.read_module_config(module_name)

        if current_checksum != original_checksum:
            raise ValueError(f"Module {module_name} config has been modified since it was read")

        # Update period
        data["period"] = period

        # Write back
        return self.write_module_config(module_name, data, original_checksum)

    def update_submodule_uniquekey(self, module_name: str, submodule_name: str,
                                 num_uniquekey: int, original_checksum: str) -> Dict[str, Any]:
        """
        Update submodule uniquekey.NumUniqKey value

        Args:
            module_name: Name of parent module
            submodule_name: Name of submodule file (without .yml)
            num_uniquekey: New NumUniqKey value
            original_checksum: Checksum from when file was read

        Returns:
            Dict with operation results
        """
        if not isinstance(num_uniquekey, int) or num_uniquekey < 1 or num_uniquekey > MAX_UNIQUE_KEY:
            raise ValueError(f"NumUniqKey must be between 1 and {MAX_UNIQUE_KEY}")

        # Read current config
        data, current_checksum = self.read_submodule_config(module_name, submodule_name)

        if current_checksum != original_checksum:
            raise ValueError(f"Submodule {module_name}/{submodule_name} config has been modified since it was read")

        # Update/create uniquekey section
        if "uniquekey" not in data:
            data["uniquekey"] = {}

        data["uniquekey"]["NumUniqKey"] = num_uniquekey

        # Write back
        return self.write_submodule_config(module_name, submodule_name, data, original_checksum)


# Global YAML editor instance
yaml_editor = SafeYAMLEditor()