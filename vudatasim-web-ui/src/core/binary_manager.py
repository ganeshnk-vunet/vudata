"""
Binary process management for vuDataSim
"""
import os
import time
import signal
import psutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .config import BIN_DIR, PRIMARY_BINARY, LOGS_DIR, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages vuDataSim binary processes"""

    def __init__(self):
        self.processes: Dict[str, Dict[str, Any]] = {}
        self.log_counter = 0

    def _get_binary_path(self, binary_name: str) -> Path:
        """Get full path to binary"""
        return BIN_DIR / binary_name

    def _get_log_filename(self) -> str:
        """Generate unique log filename"""
        self.log_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ui-{timestamp}-{self.log_counter}.log"

    def start_binary(self, binary_name: str = PRIMARY_BINARY, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """
        Start a binary with optional timeout

        Args:
            binary_name: Name of binary to start
            timeout: Timeout in seconds (0 = no timeout)

        Returns:
            Dict with process info and run_id
        """
        binary_path = self._get_binary_path(binary_name)

        if not binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")

        if binary_name in self.processes:
            if self.processes[binary_name]["status"] == "running":
                raise ValueError(f"Binary {binary_name} is already running")

        # Create log file
        log_file = LOGS_DIR / self._get_log_filename()

        try:
            # Start the process
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    [str(binary_path)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid  # Create new process group
                )

            run_id = f"{binary_name}_{int(time.time())}"

            self.processes[binary_name] = {
                "process": process,
                "run_id": run_id,
                "start_time": datetime.now(),
                "timeout": timeout,
                "status": "running",
                "log_file": log_file
            }

            logger.info(f"Started {binary_name} with PID {process.pid}, run_id: {run_id}")
            return {
                "success": True,
                "run_id": run_id,
                "pid": process.pid,
                "log_file": str(log_file),
                "message": f"Started {binary_name} successfully"
            }

        except Exception as e:
            logger.error(f"Failed to start {binary_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to start {binary_name}"
            }

    def stop_binary(self, binary_name: str = PRIMARY_BINARY, graceful_timeout: int = 10) -> Dict[str, Any]:
        """
        Stop a running binary

        Args:
            binary_name: Name of binary to stop
            graceful_timeout: Seconds to wait for graceful shutdown

        Returns:
            Dict with stop results
        """
        if binary_name not in self.processes:
            return {
                "success": False,
                "error": "Binary not found in managed processes",
                "message": f"{binary_name} is not being managed"
            }

        process_info = self.processes[binary_name]
        process = process_info["process"]

        if process_info["status"] != "running":
            return {
                "success": False,
                "error": f"Binary {binary_name} is not running",
                "message": f"{binary_name} is not currently running"
            }

        try:
            # Try graceful termination first
            process.terminate()
            logger.info(f"Sent SIGTERM to {binary_name} (PID {process.pid})")

            # Wait for graceful shutdown
            try:
                process.wait(timeout=graceful_timeout)
                exit_code = process.returncode
                logger.info(f"{binary_name} terminated gracefully with exit code {exit_code}")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                logger.warning(f"{binary_name} didn't terminate gracefully, sending SIGKILL")
                process.kill()
                process.wait(timeout=5)
                exit_code = -1
                logger.info(f"{binary_name} killed with SIGKILL")

            # Update process info
            process_info.update({
                "status": "stopped",
                "exit_code": exit_code,
                "end_time": datetime.now()
            })

            return {
                "success": True,
                "exit_code": exit_code,
                "message": f"Stopped {binary_name} successfully"
            }

        except Exception as e:
            logger.error(f"Failed to stop {binary_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to stop {binary_name}"
            }

    def get_status(self, binary_name: str = PRIMARY_BINARY) -> Dict[str, Any]:
        """Get status of a binary"""
        if binary_name not in self.processes:
            return {
                "status": "not_managed",
                "message": f"{binary_name} is not being managed"
            }

        process_info = self.processes[binary_name]
        process = process_info["process"]

        try:
            # Check if process is still running
            if process.poll() is None:
                # Process is still running
                elapsed = datetime.now() - process_info["start_time"]
                return {
                    "status": "running",
                    "pid": process.pid,
                    "run_id": process_info["run_id"],
                    "start_time": process_info["start_time"].isoformat(),
                    "elapsed_seconds": elapsed.total_seconds(),
                    "log_file": str(process_info["log_file"])
                }
            else:
                # Process has exited
                process_info.update({
                    "status": "exited",
                    "exit_code": process.returncode,
                    "end_time": datetime.now()
                })

                elapsed = process_info.get("end_time") - process_info["start_time"]
                return {
                    "status": "exited",
                    "exit_code": process.returncode,
                    "run_id": process_info["run_id"],
                    "start_time": process_info["start_time"].isoformat(),
                    "elapsed_seconds": elapsed.total_seconds(),
                    "log_file": str(process_info["log_file"])
                }

        except Exception as e:
            logger.error(f"Error getting status for {binary_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Error checking status of {binary_name}"
            }

    def list_binaries(self) -> list:
        """List available binaries"""
        binaries = []
        for binary_name in os.listdir(BIN_DIR):
            binary_path = BIN_DIR / binary_name
            if binary_path.is_file() and os.access(binary_path, os.X_OK):
                binaries.append(binary_name)
        return binaries

    def cleanup_finished_processes(self):
        """Clean up finished processes from memory"""
        to_remove = []
        for binary_name, process_info in self.processes.items():
            if process_info["status"] in ["stopped", "exited"]:
                to_remove.append(binary_name)

        for binary_name in to_remove:
            del self.processes[binary_name]
            logger.info(f"Cleaned up finished process: {binary_name}")


# Global process manager instance
process_manager = ProcessManager()