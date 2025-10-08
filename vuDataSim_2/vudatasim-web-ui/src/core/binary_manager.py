"""
Binary process management for vuDataSim
"""
import os
import time
import signal
import logging
import subprocess
import paramiko
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .config import (
    BIN_DIR, PRIMARY_BINARY, LOGS_DIR, DEFAULT_TIMEOUT,
    REMOTE_HOST, REMOTE_USER, REMOTE_SSH_KEY_PATH, REMOTE_BINARY_DIR, REMOTE_TIMEOUT
)

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
                    preexec_fn=os.setsid,  # Create new process group
                    cwd=BIN_DIR.parent  # Run from the workspace directory
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
                elapsed_seconds = elapsed.total_seconds()

                # Check for timeout
                timeout = process_info.get("timeout", 0)
                if timeout > 0 and elapsed_seconds >= timeout:
                    logger.info(f"Timeout reached for {binary_name} (PID {process.pid}), stopping...")
                    # Stop the process due to timeout
                    stop_result = self.stop_binary(binary_name)
                    if stop_result.get("success"):
                        return {
                            "status": "timeout",
                            "pid": process.pid,
                            "run_id": process_info["run_id"],
                            "start_time": process_info["start_time"].isoformat(),
                            "elapsed_seconds": elapsed_seconds,
                            "timeout": timeout,
                            "log_file": str(process_info["log_file"]),
                            "message": f"Process stopped due to timeout ({timeout}s)"
                        }
                    else:
                        logger.error(f"Failed to stop timed out process {binary_name}: {stop_result.get('error')}")

                return {
                    "status": "running",
                    "pid": process.pid,
                    "run_id": process_info["run_id"],
                    "start_time": process_info["start_time"].isoformat(),
                    "elapsed_seconds": elapsed_seconds,
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
        if not BIN_DIR.exists():
            logger.info(f"Local bin directory does not exist: {BIN_DIR}")
            return binaries
        
        try:
            for binary_name in os.listdir(BIN_DIR):
                binary_path = BIN_DIR / binary_name
                if binary_path.is_file() and os.access(binary_path, os.X_OK):
                    binaries.append(binary_name)
        except Exception as e:
            logger.error(f"Error listing local binaries: {e}")
        
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

    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client for remote connections"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Expand the tilde in the SSH key path
            expanded_key_path = os.path.expanduser(REMOTE_SSH_KEY_PATH)
            
            ssh.connect(
                REMOTE_HOST,
                username=REMOTE_USER,
                key_filename=expanded_key_path,
                timeout=10
            )
            return ssh
        except Exception as e:
            logger.error(f"Failed to connect to remote host {REMOTE_HOST}: {e}")
            raise

    def list_remote_binaries(self) -> list:
        """List available binaries on remote host"""
        try:
            ssh = self._get_ssh_client()
            # Use ls -l to get detailed file info and filter only executable files
            _, stdout, _ = ssh.exec_command(f"find {REMOTE_BINARY_DIR} -maxdepth 1 -type f -executable -printf '%f\\n'")

            binaries = []
            for line in stdout:
                binary_name = line.strip()
                # Filter out empty lines, hidden files, and invalid characters
                if (binary_name and 
                    not binary_name.startswith('.') and 
                    binary_name.replace('_', '').replace('-', '').isalnum()):
                    binaries.append(binary_name)

            ssh.close()
            return sorted(binaries)  # Return sorted list for consistent ordering

        except Exception as e:
            logger.error(f"Error listing remote binaries: {e}")
            return []

    def start_remote_binary(self, binary_name: str, timeout: int = REMOTE_TIMEOUT) -> Dict[str, Any]:
        """
        Start a binary on remote host via SSH

        Args:
            binary_name: Name of binary to start
            timeout: Timeout in seconds

        Returns:
            Dict with process info
        """
        try:
            ssh = self._get_ssh_client()

            # Create remote log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            remote_log_file = f"/tmp/vudatasim_{binary_name}_{timestamp}.log"

            # Build command to run binary in background with proper execution
            binary_path = f"{REMOTE_BINARY_DIR}/{binary_name}"
            
            # Check if binary exists and make it executable
            check_binary_cmd = f"test -f {binary_path} && echo 'exists' || echo 'not_found'"
            _, stdout_check, _ = ssh.exec_command(check_binary_cmd)
            binary_exists = stdout_check.read().decode().strip()
            
            if binary_exists != 'exists':
                raise FileNotFoundError(f"Binary {binary_name} not found at {binary_path}")
            
            # Make sure binary is executable
            make_executable_cmd = f"chmod +x {binary_path}"
            ssh.exec_command(make_executable_cmd)
            
            # Build the complete command with proper background execution
            # Change to binary directory and run with ./ prefix (as user typically does)
            # Also add some debug info to the log file
            if timeout > 0:
                # Use timeout with nohup for proper background execution
                command = f'cd {REMOTE_BINARY_DIR} && echo "Starting {binary_name} with timeout {timeout}s at $(date)" > {remote_log_file} && nohup timeout {timeout}s ./{binary_name} >> {remote_log_file} 2>&1 & echo $!'
            else:
                # Use nohup for proper background execution without timeout
                command = f'cd {REMOTE_BINARY_DIR} && echo "Starting {binary_name} at $(date)" > {remote_log_file} && nohup ./{binary_name} >> {remote_log_file} 2>&1 & echo $!'

            # Execute the command and get the PID immediately
            _, stdout, stderr = ssh.exec_command(command)
            
            # Read the PID from stdout (echo $! output)
            pid_output = stdout.read().decode().strip()
            stderr_output = stderr.read().decode().strip()
            
            if stderr_output:
                logger.warning(f"Remote command stderr: {stderr_output}")
            
            if not pid_output or not pid_output.isdigit():
                raise RuntimeError(f"Failed to get valid PID. Output: '{pid_output}', Stderr: '{stderr_output}'")
            
            pid = pid_output

            run_id = f"remote_{binary_name}_{int(time.time())}"

            # Store process info immediately
            self.processes[f"remote_{binary_name}"] = {
                "ssh": ssh,
                "run_id": run_id,
                "start_time": datetime.now(),
                "timeout": timeout,
                "status": "running",
                "remote_log_file": remote_log_file,
                "pid": pid,
                "is_remote": True
            }

            # Wait a moment to ensure process has started, then verify
            time.sleep(1.0)
            
            # Verify the process is actually running
            check_cmd = f"kill -0 {pid} 2>/dev/null && echo 'running' || echo 'not_running'"
            _, stdout_check, _ = ssh.exec_command(check_cmd)
            process_status = stdout_check.read().decode().strip()
            
            if process_status != "running":
                # Process failed to start, clean up
                if f"remote_{binary_name}" in self.processes:
                    del self.processes[f"remote_{binary_name}"]
                raise RuntimeError(f"Process with PID {pid} is not running after start. Check binary path and permissions.")

            logger.info(f"Started remote {binary_name} with PID {pid}, run_id: {run_id}")
            return {
                "success": True,
                "run_id": run_id,
                "pid": pid,
                "remote_log_file": remote_log_file,
                "message": f"Started remote {binary_name} successfully"
            }

        except Exception as e:
            logger.error(f"Failed to start remote {binary_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to start remote {binary_name}: {str(e)}"
            }

    def stop_remote_binary(self, binary_name: str) -> Dict[str, Any]:
        """
        Stop a running remote binary

        Args:
            binary_name: Name of binary to stop

        Returns:
            Dict with stop results
        """
        remote_key = f"remote_{binary_name}"

        if remote_key not in self.processes:
            return {
                "success": False,
                "error": "Remote binary not found in managed processes",
                "message": f"Remote {binary_name} is not being managed"
            }

        process_info = self.processes[remote_key]

        if process_info["status"] != "running":
            return {
                "success": False,
                "error": f"Remote binary {binary_name} is not running",
                "message": f"Remote {binary_name} is not currently running"
            }

        try:
            ssh = process_info["ssh"]

            # Kill the remote process
            pid = process_info.get("pid")
            if pid:
                ssh.exec_command(f"kill {pid}")

            # Close SSH connection
            ssh.close()

            # Update process info
            process_info.update({
                "status": "stopped",
                "end_time": datetime.now()
            })

            return {
                "success": True,
                "message": f"Stopped remote {binary_name} successfully"
            }

        except Exception as e:
            logger.error(f"Failed to stop remote {binary_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to stop remote {binary_name}"
            }

    def get_remote_status(self, binary_name: str) -> Dict[str, Any]:
        """Get status of a remote binary"""
        remote_key = f"remote_{binary_name}"

        if remote_key not in self.processes:
            return {
                "status": "not_managed",
                "message": f"Remote {binary_name} is not being managed"
            }

        process_info = self.processes[remote_key]

        try:
            # Check if process is still running on remote host
            # Reuse existing SSH connection if available, otherwise create new one
            ssh = process_info.get("ssh")
            if not ssh or not ssh.get_transport() or not ssh.get_transport().is_active():
                ssh = self._get_ssh_client()
                process_info["ssh"] = ssh
            
            pid = process_info.get("pid")

            if pid:
                # Check if PID exists
                _, stdout, _ = ssh.exec_command(f"kill -0 {pid} 2>/dev/null && echo 'running' || echo 'stopped'")
                status = stdout.read().decode().strip()

                if status == "running":
                    elapsed = datetime.now() - process_info["start_time"]
                    elapsed_seconds = elapsed.total_seconds()

                    # Check for timeout
                    timeout = process_info.get("timeout", 0)
                    if timeout > 0 and elapsed_seconds >= timeout:
                        logger.info(f"Timeout reached for remote {binary_name} (PID {pid}), stopping...")
                        stop_result = self.stop_remote_binary(binary_name)
                        if stop_result.get("success"):
                            return {
                                "status": "timeout",
                                "pid": pid,
                                "run_id": process_info["run_id"],
                                "start_time": process_info["start_time"].isoformat(),
                                "elapsed_seconds": elapsed_seconds,
                                "timeout": timeout,
                                "remote_log_file": process_info.get("remote_log_file"),
                                "message": f"Remote process stopped due to timeout ({timeout}s)"
                            }

                    return {
                        "status": "running",
                        "pid": pid,
                        "run_id": process_info["run_id"],
                        "start_time": process_info["start_time"].isoformat(),
                        "elapsed_seconds": elapsed_seconds,
                        "remote_log_file": process_info.get("remote_log_file"),
                        "is_remote": True
                    }
                else:
                    # Process has exited
                    process_info.update({
                        "status": "exited",
                        "end_time": datetime.now()
                    })

                    elapsed = process_info.get("end_time") - process_info["start_time"]
                    return {
                        "status": "exited",
                        "run_id": process_info["run_id"],
                        "start_time": process_info["start_time"].isoformat(),
                        "elapsed_seconds": elapsed.total_seconds(),
                        "remote_log_file": process_info.get("remote_log_file"),
                        "is_remote": True
                    }
            else:
                return {
                    "status": "unknown",
                    "message": "No PID available for remote process"
                }

        except Exception as e:
            logger.error(f"Error getting remote status for {binary_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Error checking status of remote {binary_name}"
            }
        finally:
            try:
                ssh.close()
            except Exception:
                pass

    def get_remote_logs(self, binary_name: str) -> str:
        """Retrieve logs from remote binary"""
        remote_key = f"remote_{binary_name}"

        if remote_key not in self.processes:
            return f"No logs available for remote {binary_name}"

        process_info = self.processes[remote_key]
        remote_log_file = process_info.get("remote_log_file")

        if not remote_log_file:
            return f"No log file available for remote {binary_name}"

        try:
            ssh = self._get_ssh_client()
            sftp = ssh.open_sftp()
            with sftp.file(remote_log_file, 'r') as f:
                logs = f.read().decode('utf-8', errors='ignore')
            sftp.close()
            ssh.close()
            return logs

        except Exception as e:
            logger.error(f"Error retrieving remote logs for {binary_name}: {e}")
            return f"Error retrieving logs: {e}"


# Global process manager instance
process_manager = ProcessManager()