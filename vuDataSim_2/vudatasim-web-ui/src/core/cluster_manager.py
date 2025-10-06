"""
Cluster Configuration Manager for vuDataSim Multi-Node Setup
Handles remote node configuration synchronization and management
"""
import os
import yaml
import logging
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import paramiko
from paramiko import SSHClient, SFTPClient
import tempfile
import time

logger = logging.getLogger(__name__)

class NodeConnectionError(Exception):
    """Exception raised when node connection fails"""
    pass

class ConfigSyncError(Exception):
    """Exception raised when configuration sync fails"""
    pass

class ClusterManager:
    """Manages configuration synchronization across multiple vuDataSim nodes"""
    
    def __init__(self, nodes_file: str = "nodes.yaml", base_dir: Optional[Path] = None):
        """
        Initialize cluster manager
        
        Args:
            nodes_file: Path to nodes configuration file
            base_dir: Base directory for the application (defaults to parent of this file)
        """
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self.nodes_file = self.base_dir / nodes_file
        self.conf_snapshots_dir = self.base_dir / "conf_snapshots"
        self.backups_dir = self.base_dir / "backups"
        self.cluster_log_file = self.base_dir / "logs" / "cluster_sync.log"
        
        # Ensure required directories exist
        self.conf_snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.cluster_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup cluster-specific logging
        self._setup_cluster_logging()
        
        # Load node configurations
        self.nodes_config = self._load_nodes_config()
        self.cluster_settings = self.nodes_config.get('cluster_settings', {})
        
    def _setup_cluster_logging(self):
        """Setup logging for cluster operations"""
        cluster_logger = logging.getLogger('cluster_sync')
        cluster_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in cluster_logger.handlers[:]:
            cluster_logger.removeHandler(handler)
            
        # File handler for cluster sync logs
        file_handler = logging.FileHandler(self.cluster_log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        cluster_logger.addHandler(file_handler)
        
        self.cluster_logger = cluster_logger
    
    def _load_nodes_config(self) -> Dict[str, Any]:
        """Load nodes configuration from YAML file"""
        try:
            if not self.nodes_file.exists():
                logger.warning(f"Nodes config file {self.nodes_file} not found")
                return {'nodes': {}, 'cluster_settings': {}}
                
            with open(self.nodes_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                
            # Validate configuration structure
            if 'nodes' not in config:
                config['nodes'] = {}
            if 'cluster_settings' not in config:
                config['cluster_settings'] = self._get_default_cluster_settings()
                
            return config
            
        except Exception as e:
            logger.error(f"Error loading nodes config: {e}")
            return {'nodes': {}, 'cluster_settings': self._get_default_cluster_settings()}
    
    def _get_default_cluster_settings(self) -> Dict[str, Any]:
        """Get default cluster settings"""
        return {
            'backup_retention_days': 30,
            'sync_timeout': 60,
            'connection_timeout': 10,
            'max_retries': 3,
            'conflict_resolution': 'manual'
        }
    
    def get_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured nodes"""
        return self.nodes_config.get('nodes', {})
    
    def get_enabled_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Get only enabled nodes"""
        nodes = self.get_nodes()
        return {name: config for name, config in nodes.items() 
                if config.get('enabled', True)}
    
    def add_node(self, name: str, host: str, user: str, key_path: str, 
                 conf_dir: str, binary_dir: str, description: str = "", 
                 enabled: bool = True) -> bool:
        """
        Add a new node to the configuration
        
        Args:
            name: Node name/identifier
            host: SSH host/IP address
            user: SSH username
            key_path: Path to SSH private key
            conf_dir: Remote path to conf.d directory
            binary_dir: Remote path to binary directory
            description: Optional description
            enabled: Whether node is enabled
            
        Returns:
            bool: Success status
        """
        try:
            if 'nodes' not in self.nodes_config:
                self.nodes_config['nodes'] = {}
                
            self.nodes_config['nodes'][name] = {
                'host': host,
                'user': user,
                'key_path': key_path,
                'conf_dir': conf_dir,
                'binary_dir': binary_dir,
                'description': description,
                'enabled': enabled
            }
            
            # Save updated configuration
            with open(self.nodes_file, 'w') as f:
                yaml.dump(self.nodes_config, f, default_flow_style=False)
                
            logger.info(f"Added node {name} to configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error adding node {name}: {e}")
            return False
    
    def remove_node(self, name: str) -> bool:
        """Remove a node from the configuration"""
        try:
            if name in self.nodes_config.get('nodes', {}):
                del self.nodes_config['nodes'][name]
                
                # Save updated configuration
                with open(self.nodes_file, 'w') as f:
                    yaml.dump(self.nodes_config, f, default_flow_style=False)
                    
                # Clean up snapshots and backups
                node_snapshot_dir = self.conf_snapshots_dir / name
                node_backup_dir = self.backups_dir / name
                
                if node_snapshot_dir.exists():
                    shutil.rmtree(node_snapshot_dir)
                if node_backup_dir.exists():
                    shutil.rmtree(node_backup_dir)
                    
                logger.info(f"Removed node {name} from configuration")
                return True
            else:
                logger.warning(f"Node {name} not found in configuration")
                return False
                
        except Exception as e:
            logger.error(f"Error removing node {name}: {e}")
            return False
    
    def _create_ssh_connection(self, node_config: Dict[str, Any]) -> Tuple[SSHClient, SFTPClient]:
        """
        Create SSH and SFTP connections to a node
        
        Args:
            node_config: Node configuration dictionary
            
        Returns:
            Tuple of (SSHClient, SFTPClient)
            
        Raises:
            NodeConnectionError: If connection fails
        """
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Expand user path for key file
            key_path = os.path.expanduser(node_config['key_path'])
            
            # Connect with timeout
            timeout = self.cluster_settings.get('connection_timeout', 10)
            ssh.connect(
                hostname=node_config['host'],
                username=node_config['user'],
                key_filename=key_path,
                timeout=timeout
            )
            
            # Create SFTP client
            sftp = ssh.open_sftp()
            
            self.cluster_logger.info(f"Connected to node {node_config['host']}")
            return ssh, sftp
            
        except Exception as e:
            error_msg = f"Failed to connect to {node_config['host']}: {e}"
            self.cluster_logger.error(error_msg)
            raise NodeConnectionError(error_msg)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate checksum for {file_path}: {e}")
            return ""
    
    def _sync_directory_from_remote(self, sftp: SFTPClient, remote_dir: str, 
                                   local_dir: Path, node_name: str) -> Dict[str, str]:
        """
        Recursively sync a directory from remote to local
        
        Args:
            sftp: SFTP client
            remote_dir: Remote directory path
            local_dir: Local directory path
            node_name: Node name for logging
            
        Returns:
            Dict mapping local file paths to their checksums
        """
        checksums = {}
        
        def _sync_recursive(remote_path: str, local_path: Path):
            try:
                # List remote directory contents
                items = sftp.listdir_attr(remote_path)
                
                for item in items:
                    remote_item_path = f"{remote_path}/{item.filename}"
                    local_item_path = local_path / item.filename
                    
                    if item.st_mode and (item.st_mode & 0o170000) == 0o040000:  # Directory
                        # Create local directory if it doesn't exist
                        local_item_path.mkdir(parents=True, exist_ok=True)
                        # Recursively sync subdirectory
                        _sync_recursive(remote_item_path, local_item_path)
                    else:  # File
                        # Download file
                        sftp.get(remote_item_path, str(local_item_path))
                        # Calculate checksum
                        checksum = self._calculate_checksum(local_item_path)
                        checksums[str(local_item_path.relative_to(local_dir))] = checksum
                        
                        self.cluster_logger.debug(f"Downloaded {remote_item_path} to {local_item_path}")
                        
            except Exception as e:
                self.cluster_logger.error(f"Error syncing {remote_path}: {e}")
                
        # Ensure local directory exists
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Start recursive sync
        _sync_recursive(remote_dir.rstrip('/'), local_dir)
        
        return checksums
    
    def fetch_node_config(self, node_name: str) -> bool:
        """
        Fetch configuration from a single node
        
        Args:
            node_name: Name of the node to fetch from
            
        Returns:
            bool: Success status
        """
        nodes = self.get_nodes()
        if node_name not in nodes:
            logger.error(f"Node {node_name} not found in configuration")
            return False
            
        node_config = nodes[node_name]
        if not node_config.get('enabled', True):
            logger.warning(f"Node {node_name} is disabled")
            return False
            
        ssh = None
        sftp = None
        
        try:
            # Create connection
            ssh, sftp = self._create_ssh_connection(node_config)
            
            # Create local snapshot directory for this node
            node_snapshot_dir = self.conf_snapshots_dir / node_name
            conf_snapshot_dir = node_snapshot_dir / "conf.d"
            
            # Remove existing snapshot
            if node_snapshot_dir.exists():
                shutil.rmtree(node_snapshot_dir)
                
            # Sync remote conf.d directory
            remote_conf_dir = node_config['conf_dir']
            self.cluster_logger.info(f"Fetching configuration from {node_name} ({remote_conf_dir})")
            
            checksums = self._sync_directory_from_remote(
                sftp, remote_conf_dir, conf_snapshot_dir, node_name
            )
            
            # Save checksums for conflict detection
            checksum_file = node_snapshot_dir / "checksums.yaml"
            with open(checksum_file, 'w') as f:
                yaml.dump({
                    'timestamp': datetime.now().isoformat(),
                    'node': node_name,
                    'remote_path': remote_conf_dir,
                    'checksums': checksums
                }, f)
                
            self.cluster_logger.info(f"Successfully fetched {len(checksums)} files from {node_name}")
            return True
            
        except Exception as e:
            self.cluster_logger.error(f"Error fetching config from {node_name}: {e}")
            return False
            
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()
    
    def fetch_all_configs(self) -> Dict[str, bool]:
        """
        Fetch configurations from all enabled nodes
        
        Returns:
            Dict mapping node names to success status
        """
        results = {}
        enabled_nodes = self.get_enabled_nodes()
        
        self.cluster_logger.info(f"Fetching configurations from {len(enabled_nodes)} nodes")
        
        for node_name in enabled_nodes:
            results[node_name] = self.fetch_node_config(node_name)
            
        success_count = sum(1 for success in results.values() if success)
        self.cluster_logger.info(f"Successfully fetched from {success_count}/{len(enabled_nodes)} nodes")
        
        return results
    
    def get_node_snapshot_files(self, node_name: str) -> List[Path]:
        """
        Get list of configuration files in a node's snapshot
        
        Args:
            node_name: Name of the node
            
        Returns:
            List of Path objects for configuration files
        """
        node_snapshot_dir = self.conf_snapshots_dir / node_name / "conf.d"
        if not node_snapshot_dir.exists():
            return []
            
        files = []
        for file_path in node_snapshot_dir.rglob("*.yaml"):
            files.append(file_path)
        for file_path in node_snapshot_dir.rglob("*.yml"):
            files.append(file_path)
            
        return sorted(files)
    
    def get_all_snapshot_files(self) -> Dict[str, List[Path]]:
        """Get all snapshot files organized by node"""
        result = {}
        for node_name in self.get_nodes():
            result[node_name] = self.get_node_snapshot_files(node_name)
        return result
    
    def create_backup(self, node_name: str, file_path: Path) -> bool:
        """
        Create a timestamped backup of a configuration file
        
        Args:
            node_name: Name of the node
            file_path: Path to the file to backup
            
        Returns:
            bool: Success status
        """
        try:
            # Create backup directory structure
            backup_dir = self.backups_dir / node_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            relative_path = file_path.relative_to(self.conf_snapshots_dir / node_name)
            backup_file = backup_dir / f"{relative_path.stem}_{timestamp}{relative_path.suffix}"
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_file)
            
            logger.info(f"Created backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return False
    
    def push_file_to_node(self, node_name: str, local_file: Path, 
                          remote_file: str, create_backup: bool = True) -> bool:
        """
        Push a single file to a remote node
        
        Args:
            node_name: Name of the target node
            local_file: Local file path
            remote_file: Remote file path
            create_backup: Whether to create a backup before pushing
            
        Returns:
            bool: Success status
        """
        nodes = self.get_nodes()
        if node_name not in nodes:
            logger.error(f"Node {node_name} not found")
            return False
            
        node_config = nodes[node_name]
        if not node_config.get('enabled', True):
            logger.warning(f"Node {node_name} is disabled")
            return False
            
        ssh = None
        sftp = None
        
        try:
            # Create connection
            ssh, sftp = self._create_ssh_connection(node_config)
            
            # Create backup if requested
            if create_backup:
                self.create_backup(node_name, local_file)
            
            # Push file to remote
            sftp.put(str(local_file), remote_file)
            
            self.cluster_logger.info(f"Pushed {local_file} to {node_name}:{remote_file}")
            return True
            
        except Exception as e:
            self.cluster_logger.error(f"Error pushing {local_file} to {node_name}: {e}")
            return False
            
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()
    
    def push_config_to_node(self, node_name: str, local_config_file: Path) -> bool:
        """
        Push a configuration file to its corresponding location on a node
        
        Args:
            node_name: Name of the target node
            local_config_file: Local configuration file path
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate relative path within conf.d
            node_snapshot_dir = self.conf_snapshots_dir / node_name / "conf.d"
            relative_path = local_config_file.relative_to(node_snapshot_dir)
            
            # Get remote conf.d path for this node
            nodes = self.get_nodes()
            remote_conf_dir = nodes[node_name]['conf_dir']
            remote_file_path = f"{remote_conf_dir.rstrip('/')}/{relative_path}"
            
            return self.push_file_to_node(node_name, local_config_file, remote_file_path)
            
        except Exception as e:
            logger.error(f"Error determining remote path for {local_config_file}: {e}")
            return False
    
    def restart_vudatasim(self, node_name: str) -> bool:
        """
        Restart vuDataSim binary on a remote node
        
        Args:
            node_name: Name of the target node
            
        Returns:
            bool: Success status
        """
        nodes = self.get_nodes()
        if node_name not in nodes:
            logger.error(f"Node {node_name} not found")
            return False
            
        node_config = nodes[node_name]
        if not node_config.get('enabled', True):
            logger.warning(f"Node {node_name} is disabled")
            return False
            
        ssh = None
        
        try:
            # Create SSH connection
            ssh, _ = self._create_ssh_connection(node_config)
            
            # Commands to stop and start vuDataSim
            binary_dir = node_config['binary_dir']
            stop_cmd = f"pkill -f vuDataSim || true"
            start_cmd = f"cd {binary_dir} && nohup ./vuDataSim > /dev/null 2>&1 &"
            
            # Stop existing process
            stdin, stdout, stderr = ssh.exec_command(stop_cmd)
            stdout.channel.recv_exit_status()  # Wait for command to complete
            
            # Wait a moment for processes to terminate
            time.sleep(2)
            
            # Start new process
            stdin, stdout, stderr = ssh.exec_command(start_cmd)
            stdout.channel.recv_exit_status()  # Wait for command to complete
            
            self.cluster_logger.info(f"Restarted vuDataSim on {node_name}")
            return True
            
        except Exception as e:
            self.cluster_logger.error(f"Error restarting vuDataSim on {node_name}: {e}")
            return False
            
        finally:
            if ssh:
                ssh.close()
    
    def check_conflicts(self, node_name: str) -> Dict[str, Any]:
        """
        Check for conflicts between local and remote configurations
        
        Args:
            node_name: Name of the node to check
            
        Returns:
            Dict with conflict information
        """
        # This would require fetching current remote checksums and comparing
        # with stored checksums - implementation depends on specific requirements
        # For now, return a placeholder
        return {
            'has_conflicts': False,
            'conflicted_files': [],
            'last_sync': None
        }
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster status"""
        nodes = self.get_nodes()
        enabled_nodes = self.get_enabled_nodes()
        
        status = {
            'total_nodes': len(nodes),
            'enabled_nodes': len(enabled_nodes),
            'disabled_nodes': len(nodes) - len(enabled_nodes),
            'nodes': {}
        }
        
        for node_name, node_config in nodes.items():
            snapshot_dir = self.conf_snapshots_dir / node_name
            has_snapshot = snapshot_dir.exists()
            
            # Get last sync time from checksums file if available
            last_sync = None
            checksum_file = snapshot_dir / "checksums.yaml"
            if checksum_file.exists():
                try:
                    with open(checksum_file, 'r') as f:
                        checksum_data = yaml.safe_load(f)
                        last_sync = checksum_data.get('timestamp')
                except Exception:
                    pass
            
            status['nodes'][node_name] = {
                'enabled': node_config.get('enabled', True),
                'host': node_config.get('host'),
                'has_snapshot': has_snapshot,
                'last_sync': last_sync,
                'config_files': len(self.get_node_snapshot_files(node_name))
            }
            
        return status


# Global cluster manager instance
cluster_manager = None

def get_cluster_manager() -> ClusterManager:
    """Get or create global cluster manager instance"""
    global cluster_manager
    if cluster_manager is None:
        cluster_manager = ClusterManager()
    return cluster_manager
