"""
Audit logging system for vuDataSim Web UI
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .config import LOGS_DIR

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging for all operations"""

    def __init__(self):
        self.audit_file = LOGS_DIR / "audit.jsonl"
        LOGS_DIR.mkdir(exist_ok=True)

    def log_action(self, action: str, details: Dict[str, Any], user: str = "system"):
        """Log an action to the audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "details": details
        }

        try:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')

            logger.info(f"Audit: {action} by {user}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def log_binary_operation(self, operation: str, binary_name: str, details: Dict[str, Any]):
        """Log binary operations"""
        self.log_action(
            f"binary_{operation}",
            {
                "binary_name": binary_name,
                "operation": operation,
                **details
            }
        )

    def log_config_change(self, file_path: str, operation: str, details: Dict[str, Any]):
        """Log configuration changes"""
        self.log_action(
            f"config_{operation}",
            {
                "file_path": file_path,
                "operation": operation,
                **details
            }
        )

    def get_audit_history(self, limit: int = 100) -> list:
        """Get recent audit history"""
        if not self.audit_file.exists():
            return []

        entries = []
        try:
            with open(self.audit_file, 'r') as f:
                for line in f.readlines()[-limit:]:
                    entries.append(json.loads(line.strip()))
        except Exception as e:
            logger.error(f"Error reading audit history: {e}")

        return entries


# Global audit logger instance
audit_logger = AuditLogger()