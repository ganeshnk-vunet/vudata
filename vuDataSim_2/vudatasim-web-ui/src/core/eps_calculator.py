"""
EPS (Events Per Second) calculation engine
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from .config import CONF_D_DIR, DEFAULT_UNIQUE_KEY
from .yaml_editor import yaml_editor

logger = logging.getLogger(__name__)


class EPSCalculator:
    """Calculates EPS for modules and submodules"""

    def _parse_duration_to_seconds(self, duration_str: str) -> float:
        """Parse duration string to seconds"""
        return yaml_editor._parse_duration(duration_str)

    def get_module_list(self) -> List[str]:
        """Get list of available modules (subdirectories in conf.d/)"""
        modules = []
        try:
            for item in CONF_D_DIR.iterdir():
                if item.is_dir() and (item / "conf.yml").exists():
                    modules.append(item.name)
        except Exception as e:
            logger.error(f"Error listing modules: {e}")
        return sorted(modules)

    def get_submodules(self, module_name: str) -> List[str]:
        """Get list of submodules for a module"""
        submodules = []
        module_dir = CONF_D_DIR / module_name

        if not module_dir.exists():
            return submodules

        try:
            # Look for .yml files in the module directory
            for yml_file in module_dir.glob("*.yml"):
                if yml_file.name != "conf.yml":
                    # Remove .yml extension
                    submodules.append(yml_file.stem)
        except Exception as e:
            logger.error(f"Error listing submodules for {module_name}: {e}")

        return sorted(submodules)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get module configuration with defaults"""
        try:
            data, _ = yaml_editor.read_module_config(module_name)

            # Extract uniquekey and period with defaults
            uniquekey = DEFAULT_UNIQUE_KEY
            period = "1s"

            if "uniquekey" in data and "NumUniqKey" in data["uniquekey"]:
                uniquekey = data["uniquekey"]["NumUniqKey"]

            if "period" in data:
                period = data["period"]

            return {
                "uniquekey": uniquekey,
                "period": period,
                "period_seconds": self._parse_duration_to_seconds(period),
                "full_config": data
            }

        except Exception as e:
            logger.error(f"Error reading module config for {module_name}: {e}")
            return {
                "uniquekey": DEFAULT_UNIQUE_KEY,
                "period": "1s",
                "period_seconds": 1.0,
                "full_config": {},
                "error": str(e)
            }

    def get_submodule_config(self, module_name: str, submodule_name: str) -> Dict[str, Any]:
        """Get submodule configuration with defaults"""
        try:
            data, _ = yaml_editor.read_submodule_config(module_name, submodule_name)

            # Extract uniquekey with default
            uniquekey = DEFAULT_UNIQUE_KEY

            if "uniquekey" in data and "NumUniqKey" in data["uniquekey"]:
                uniquekey = data["uniquekey"]["NumUniqKey"]

            return {
                "uniquekey": uniquekey,
                "full_config": data
            }

        except Exception as e:
            logger.error(f"Error reading submodule config for {module_name}/{submodule_name}: {e}")
            return {
                "uniquekey": DEFAULT_UNIQUE_KEY,
                "full_config": {},
                "error": str(e)
            }

    def calculate_eps(self, module_name: str, module_uniquekey: int = None,
                     module_period: str = None, submodule_overrides: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Calculate EPS for a module

        Args:
            module_name: Name of the module
            module_uniquekey: Override module uniquekey (optional)
            module_period: Override module period (optional)
            submodule_overrides: Dict of submodule_name -> uniquekey overrides

        Returns:
            Dict with EPS calculation details
        """
        # Get module configuration
        module_config = self.get_module_config(module_name)

        # Apply overrides
        if module_uniquekey is not None:
            module_config["uniquekey"] = module_uniquekey

        if module_period is not None:
            module_config["period"] = module_period
            module_config["period_seconds"] = self._parse_duration_to_seconds(module_period)

        # Get submodules
        submodules = self.get_submodules(module_name)

        # Calculate submodule contributions
        submodule_details = []
        total_submodule_contribution = 0

        for submodule_name in submodules:
            # Get submodule config
            submodule_config = self.get_submodule_config(module_name, submodule_name)

            # Apply override if provided
            if submodule_overrides and submodule_name in submodule_overrides:
                submodule_config["uniquekey"] = submodule_overrides[submodule_name]

            # Use default if uniquekey is missing or 0
            uniquekey = submodule_config["uniquekey"]
            if uniquekey < 1:
                uniquekey = DEFAULT_UNIQUE_KEY

            # For submodules, we use multiplier = 1 (as mentioned in requirements)
            multiplier = 1
            contribution = multiplier * uniquekey

            submodule_details.append({
                "name": submodule_name,
                "uniquekey": uniquekey,
                "multiplier": multiplier,
                "contribution": contribution
            })

            total_submodule_contribution += contribution

        # Calculate final EPS using the formula:
        # EPS = (ModuleLevelUniqueKeys * Sum(submodule contributions)) / periodSeconds
        module_level_keys = module_config["uniquekey"]
        period_seconds = module_config["period_seconds"]

        if period_seconds <= 0:
            period_seconds = 1.0  # Avoid division by zero

        eps = (module_level_keys * total_submodule_contribution) / period_seconds

        return {
            "module_name": module_name,
            "module_uniquekey": module_level_keys,
            "module_period": module_config["period"],
            "module_period_seconds": period_seconds,
            "submodules": submodule_details,
            "total_submodule_contribution": total_submodule_contribution,
            "eps": eps,
            "calculation": {
                "formula": "EPS = (ModuleLevelUniqueKeys * Sum(submodule contributions)) / periodSeconds",
                "module_level_keys": module_level_keys,
                "total_submodule_contribution": total_submodule_contribution,
                "period_seconds": period_seconds
            }
        }

    def calculate_eps_for_all_modules(self) -> Dict[str, Dict[str, Any]]:
        """Calculate EPS for all available modules"""
        modules = self.get_module_list()
        results = {}

        for module_name in modules:
            try:
                eps_data = self.calculate_eps(module_name)
                results[module_name] = eps_data
            except Exception as e:
                logger.error(f"Error calculating EPS for {module_name}: {e}")
                results[module_name] = {
                    "error": str(e),
                    "eps": 0
                }

        return results

    def suggest_uniquekey_for_target_eps(self, module_name: str, target_eps: float,
                                       period: str = None, tolerance: float = 0.05) -> Dict[str, Any]:
        """
        Suggest uniquekey values to achieve target EPS

        Args:
            module_name: Name of the module
            target_eps: Target EPS to achieve
            period: Fixed period (optional, will use current if not provided)
            tolerance: Acceptable tolerance (default 5%)

        Returns:
            Dict with suggested values and expected EPS
        """
        # Get current configuration
        module_config = self.get_module_config(module_name)
        submodules = self.get_submodules(module_name)

        # Get current period if not specified
        if period is None:
            period = module_config["period"]

        period_seconds = self._parse_duration_to_seconds(period)

        # Calculate current total submodule contribution
        total_submodule_contribution = 0
        submodule_configs = {}

        for submodule_name in submodules:
            submodule_config = self.get_submodule_config(module_name, submodule_name)
            uniquekey = submodule_config["uniquekey"]
            if uniquekey < 1:
                uniquekey = DEFAULT_UNIQUE_KEY

            multiplier = 1  # As per requirements
            contribution = multiplier * uniquekey
            total_submodule_contribution += contribution

            submodule_configs[submodule_name] = {
                "current_uniquekey": uniquekey,
                "multiplier": multiplier,
                "contribution": contribution
            }

        if total_submodule_contribution <= 0:
            return {
                "error": "No valid submodules found for EPS calculation",
                "suggestion": None
            }

        # Calculate required module uniquekey for target EPS
        # EPS = (ModuleLevelUniqueKeys * total_submodule_contribution) / period_seconds
        # So: ModuleLevelUniqueKeys = (target_eps * period_seconds) / total_submodule_contribution

        required_module_uniquekey = (target_eps * period_seconds) / total_submodule_contribution

        # Round to nearest integer
        suggested_module_uniquekey = max(1, round(required_module_uniquekey))

        # Calculate expected EPS with suggested value
        expected_eps = (suggested_module_uniquekey * total_submodule_contribution) / period_seconds

        # Check if we're within tolerance
        actual_tolerance = abs(expected_eps - target_eps) / target_eps if target_eps > 0 else 0

        return {
            "target_eps": target_eps,
            "suggested_module_uniquekey": suggested_module_uniquekey,
            "current_module_uniquekey": module_config["uniquekey"],
            "module_period": period,
            "period_seconds": period_seconds,
            "submodule_configs": submodule_configs,
            "total_submodule_contribution": total_submodule_contribution,
            "expected_eps": expected_eps,
            "tolerance_used": actual_tolerance,
            "within_tolerance": actual_tolerance <= tolerance,
            "calculation_details": {
                "required_module_uniquekey": required_module_uniquekey,
                "rounded_suggestion": suggested_module_uniquekey,
                "tolerance_threshold": tolerance
            }
        }

    def get_module_summary(self, module_name: str) -> Dict[str, Any]:
        """Get comprehensive summary for a module"""
        try:
            eps_data = self.calculate_eps(module_name)
            module_config = self.get_module_config(module_name)

            return {
                "name": module_name,
                "enabled": module_config["full_config"].get("enabled", False),
                "current_eps": eps_data["eps"],
                "module_uniquekey": eps_data["module_uniquekey"],
                "module_period": eps_data["module_period"],
                "submodule_count": len(eps_data["submodules"]),
                "submodules": eps_data["submodules"],
                "config": module_config
            }

        except Exception as e:
            logger.error(f"Error getting module summary for {module_name}: {e}")
            return {
                "name": module_name,
                "error": str(e),
                "current_eps": 0
            }


# Global EPS calculator instance
eps_calculator = EPSCalculator()