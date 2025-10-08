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
    
    def get_all_submodule_configs(self, node_name: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all submodule configuration files with their unique key settings
        
        Args:
            node_name: Optional node name to use snapshot from, 
                      if None uses first available node snapshot
                      
        Returns:
            Dict mapping submodule paths to their config data
        """
        submodule_configs = {}
        
        try:
            if node_name:
                # Use specific node's snapshot
                snapshot_dir = self.conf_snapshots_dir / node_name / "conf.d"
            else:
                # If no node specified, try to use the first available node snapshot
                available_nodes = [d.name for d in self.conf_snapshots_dir.iterdir() 
                                 if d.is_dir() and (d / "conf.d").exists()]
                if not available_nodes:
                    logger.warning("No node snapshots available")
                    return {}
                
                # Use the first available node snapshot
                node_name = available_nodes[0]
                snapshot_dir = self.conf_snapshots_dir / node_name / "conf.d"
                logger.info(f"Using snapshot from node {node_name} (first available)")
                
            if not snapshot_dir.exists():
                logger.warning(f"Configuration directory {snapshot_dir} not found")
                return {}
                
            # Walk through all module directories
            for module_dir in snapshot_dir.iterdir():
                if not module_dir.is_dir() or module_dir.name.startswith('.'):
                    continue
                    
                # Skip the main conf.yml
                if module_dir.name == 'conf.yml':
                    continue
                    
                module_conf_path = module_dir / "conf.yml"
                if not module_conf_path.exists():
                    continue
                    
                # Load module config to get submodules list
                try:
                    with open(module_conf_path, 'r') as f:
                        module_config = yaml.safe_load(f) or {}
                        
                    # Get included submodules
                    included_submodules = module_config.get('Include_sub_modules', [])
                    if isinstance(included_submodules, str):
                        included_submodules = [included_submodules]
                        
                    # Process each submodule
                    for submodule_name in included_submodules:
                        if submodule_name == '*':
                            # Handle wildcard - include all .yml files
                            for yml_file in module_dir.glob("*.yml"):
                                if yml_file.name != "conf.yml":
                                    self._process_submodule_file(
                                        yml_file, module_dir.name, 
                                        yml_file.stem, submodule_configs
                                    )
                        else:
                            # Handle specific submodule
                            submodule_path = module_dir / f"{submodule_name}.yml"
                            if submodule_path.exists():
                                self._process_submodule_file(
                                    submodule_path, module_dir.name, 
                                    submodule_name, submodule_configs
                                )
                                
                except Exception as e:
                    logger.error(f"Error processing module {module_dir.name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting submodule configs: {e}")
            
        return submodule_configs
    
    def _process_submodule_file(self, file_path: Path, module_name: str, 
                               submodule_name: str, configs_dict: Dict):
        """Process a single submodule file and extract config info"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                config_data = yaml.safe_load(content) or {}
                
            # Create unique key for this submodule
            submodule_key = f"{module_name}/{submodule_name}"
            
            configs_dict[submodule_key] = {
                'file_path': str(file_path),
                'module_name': module_name,
                'submodule_name': submodule_name,
                'config_data': config_data,
                'raw_content': content,
                'has_unique_key_config': self._has_unique_key_config(config_data)
            }
            
        except Exception as e:
            logger.error(f"Error processing submodule file {file_path}: {e}")
    
    def _has_unique_key_config(self, config_data: Dict) -> bool:
        """Check if config data has unique key configuration"""
        return (isinstance(config_data, dict) and 
                'uniquekey' in config_data and 
                isinstance(config_data['uniquekey'], dict) and
                'NumUniqKey' in config_data['uniquekey'])
    
    def bulk_edit_submodule_unique_keys(self, node_name: str, 
                                       unique_key_updates: Dict[str, int],
                                       create_backup: bool = True) -> Dict[str, bool]:
        """
        Bulk edit unique key values across multiple submodules on a node
        
        Args:
            node_name: Target node name
            unique_key_updates: Dict mapping submodule paths to new NumUniqKey values
                              Format: {"Apache/status": 5000, "AWS_ALB/cloudwatch": 3000}
            create_backup: Whether to create backup before making changes
            
        Returns:
            Dict mapping submodule paths to success status
        """
        results = {}
        
        if node_name not in self.nodes_config.get('nodes', {}):
            logger.error(f"Node {node_name} not found in configuration")
            return {path: False for path in unique_key_updates.keys()}
            
        node_config = self.nodes_config['nodes'][node_name]
        
        if not node_config.get('enabled', True):
            logger.error(f"Node {node_name} is disabled")
            return {path: False for path in unique_key_updates.keys()}
            
        try:
            # Create backup if requested
            if create_backup:
                backup_success = self.create_node_backup(node_name)
                if not backup_success:
                    logger.warning(f"Failed to create backup for node {node_name}")
                    
            # Establish connection
            ssh, sftp = self._create_ssh_connection(node_config)
            
            try:
                # Process each submodule update
                for submodule_path, new_value in unique_key_updates.items():
                    try:
                        module_name, submodule_name = submodule_path.split('/', 1)
                        remote_file_path = f"{node_config['conf_dir']}/{module_name}/{submodule_name}.yml"
                        
                        # Download current file
                        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yml', delete=False) as temp_file:
                            temp_path = temp_file.name
                            
                        try:
                            sftp.get(remote_file_path, temp_path)
                            
                            # Load and modify the YAML
                            with open(temp_path, 'r') as f:
                                content = f.read()
                                config_data = yaml.safe_load(content) or {}
                                
                            # Update the NumUniqKey value
                            if 'uniquekey' not in config_data:
                                config_data['uniquekey'] = {}
                            if not isinstance(config_data['uniquekey'], dict):
                                config_data['uniquekey'] = {}
                                
                            config_data['uniquekey']['NumUniqKey'] = new_value
                            
                            # Write back to temp file with preserved formatting
                            with open(temp_path, 'w') as f:
                                yaml.dump(config_data, f, default_flow_style=False, 
                                        allow_unicode=True, sort_keys=False)
                                
                            # Upload modified file back
                            sftp.put(temp_path, remote_file_path)
                            
                            results[submodule_path] = True
                            self.cluster_logger.info(
                                f"Updated {submodule_path} on {node_name}: NumUniqKey = {new_value}"
                            )
                            
                        except Exception as e:
                            error_msg = f"Error updating {submodule_path} on {node_name}: {e}"
                            logger.error(error_msg)
                            self.cluster_logger.error(error_msg)
                            results[submodule_path] = False
                            
                        finally:
                            # Clean up temp file
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                                
                    except ValueError:
                        logger.error(f"Invalid submodule path format: {submodule_path}")
                        results[submodule_path] = False
                        
            finally:
                sftp.close()
                ssh.close()
                
        except NodeConnectionError as e:
            error_msg = f"Connection error for node {node_name}: {e}"
            logger.error(error_msg)
            self.cluster_logger.error(error_msg)
            return {path: False for path in unique_key_updates.keys()}
        except Exception as e:
            error_msg = f"Error during bulk edit on node {node_name}: {e}"
            logger.error(error_msg)
            self.cluster_logger.error(error_msg)
            return {path: False for path in unique_key_updates.keys()}
            
        return results
    
    def bulk_edit_all_nodes_unique_keys(self, unique_key_updates: Dict[str, int],
                                       target_nodes: List[str] = None,
                                       create_backup: bool = True) -> Dict[str, Dict[str, bool]]:
        """
        Bulk edit unique key values across multiple submodules on all or selected nodes
        
        Args:
            unique_key_updates: Dict mapping submodule paths to new NumUniqKey values
            target_nodes: Optional list of node names to target, if None targets all enabled nodes
            create_backup: Whether to create backup before making changes
            
        Returns:
            Dict mapping node names to their individual results
        """
        all_results = {}
        
        # Determine target nodes
        if target_nodes is None:
            target_nodes = [
                name for name, config in self.nodes_config.get('nodes', {}).items()
                if config.get('enabled', True)
            ]
        
        # Process each node
        for node_name in target_nodes:
            if node_name not in self.nodes_config.get('nodes', {}):
                logger.warning(f"Node {node_name} not found in configuration")
                all_results[node_name] = {path: False for path in unique_key_updates.keys()}
                continue
                
            self.cluster_logger.info(f"Starting bulk edit on node {node_name}")
            node_results = self.bulk_edit_submodule_unique_keys(
                node_name, unique_key_updates, create_backup
            )
            all_results[node_name] = node_results
            
            # Log summary for this node
            success_count = sum(1 for success in node_results.values() if success)
            total_count = len(node_results)
            self.cluster_logger.info(
                f"Node {node_name}: {success_count}/{total_count} submodules updated successfully"
            )
            
        return all_results
    
    def bulk_edit_module_unique_keys(self, node_name: str, module_name: str, 
                                    new_unique_key_value: int,
                                    create_backup: bool = True) -> Dict[str, bool]:
        """
        Bulk edit unique key values for ALL submodules within a specific module
        
        Args:
            node_name: Target node name
            module_name: Name of the module (e.g., "Apache", "AWS_ALB")
            new_unique_key_value: New NumUniqKey value to set for all submodules
            create_backup: Whether to create backup before making changes
            
        Returns:
            Dict mapping submodule paths to success status
        """
        # Get all submodule configs to find submodules for this module
        submodule_configs = self.get_all_submodule_configs(node_name)
        
        # Filter to only submodules in the specified module
        module_submodules = {}
        for submodule_path, config_info in submodule_configs.items():
            if config_info['module_name'] == module_name and config_info['has_unique_key_config']:
                module_submodules[submodule_path] = new_unique_key_value
        
        if not module_submodules:
            logger.warning(f"No submodules with unique key config found in module {module_name} on node {node_name}")
            return {}
        
        self.cluster_logger.info(
            f"Bulk editing {len(module_submodules)} submodules in module {module_name} "
            f"on node {node_name} to NumUniqKey = {new_unique_key_value}"
        )
        
        # Use existing bulk edit method
        return self.bulk_edit_submodule_unique_keys(node_name, module_submodules, create_backup)
    
    def bulk_edit_module_unique_keys_all_nodes(self, module_name: str, 
                                             new_unique_key_value: int,
                                             target_nodes: List[str] = None,
                                             create_backup: bool = True) -> Dict[str, Dict[str, bool]]:
        """
        Bulk edit unique key values for ALL submodules within a specific module across all nodes
        
        Args:
            module_name: Name of the module (e.g., "Apache", "AWS_ALB")
            new_unique_key_value: New NumUniqKey value to set for all submodules
            target_nodes: Optional list of node names to target, if None targets all enabled nodes
            create_backup: Whether to create backup before making changes
            
        Returns:
            Dict mapping node names to their individual results
        """
        all_results = {}
        
        # Determine target nodes
        if target_nodes is None:
            target_nodes = [
                name for name, config in self.nodes_config.get('nodes', {}).items()
                if config.get('enabled', True)
            ]
        
        self.cluster_logger.info(
            f"Starting bulk edit of module {module_name} across {len(target_nodes)} nodes "
            f"with NumUniqKey = {new_unique_key_value}"
        )
        
        # Process each node
        for node_name in target_nodes:
            if node_name not in self.nodes_config.get('nodes', {}):
                logger.warning(f"Node {node_name} not found in configuration")
                all_results[node_name] = {}
                continue
                
            self.cluster_logger.info(f"Processing module {module_name} on node {node_name}")
            node_results = self.bulk_edit_module_unique_keys(
                node_name, module_name, new_unique_key_value, create_backup
            )
            all_results[node_name] = node_results
            
            # Log summary for this node
            success_count = sum(1 for success in node_results.values() if success)
            total_count = len(node_results)
            self.cluster_logger.info(
                f"Node {node_name}, Module {module_name}: {success_count}/{total_count} "
                f"submodules updated successfully"
            )
            
        return all_results
    
    def get_module_submodules_summary(self, module_name: str, node_name: str = None) -> Dict[str, Any]:
        """
        Get summary of all submodules within a specific module and their current NumUniqKey values
        
        Args:
            module_name: Name of the module to analyze
            node_name: Optional node name to fetch from, if None uses local snapshot
            
        Returns:
            Dict with module-specific summary information
        """
        submodule_configs = self.get_all_submodule_configs(node_name)
        
        module_summary = {
            'module_name': module_name,
            'total_submodules': 0,
            'submodules_with_unique_keys': 0,
            'submodule_details': []
        }
        
        for submodule_path, config_info in submodule_configs.items():
            if config_info['module_name'] != module_name:
                continue
                
            module_summary['total_submodules'] += 1
            
            # Extract current NumUniqKey value
            current_value = None
            has_unique_key = config_info['has_unique_key_config']
            
            if has_unique_key:
                current_value = config_info['config_data']['uniquekey'].get('NumUniqKey')
                module_summary['submodules_with_unique_keys'] += 1
            
            submodule_detail = {
                'path': submodule_path,
                'submodule_name': config_info['submodule_name'],
                'has_unique_key_config': has_unique_key,
                'current_num_uniq_key': current_value,
                'file_path': config_info['file_path']
            }
            
            module_summary['submodule_details'].append(submodule_detail)
            
        return module_summary
    
    def get_module_eps_calculation(self, module_names: List[str], node_name: str = None, 
                                  period: int = 1) -> Dict[str, Any]:
        """
        Calculate EPS (Events Per Second) for selected modules
        EPS = (Module Level unique keys * Sum(Submodule level unique keys)) / period
        
        Args:
            module_names: List of module names to calculate EPS for
            node_name: Node name to fetch from (if None, uses local snapshot)
            period: Time period in seconds (default: 1 second)
            
        Returns:
            Dict with EPS calculations and details
        """
        if node_name:
            # Fetch fresh config from remote node
            fetch_success = self.fetch_node_config(node_name)
            if not fetch_success:
                logger.warning(f"Failed to fetch config from node {node_name}, using cached data")
        
        submodule_configs = self.get_all_submodule_configs(node_name)
        
        eps_results = {
            'node_name': node_name or 'Local Configuration',
            'period_seconds': period,
            'total_eps': 0,
            'modules': {},
            'calculation_details': {
                'formula': 'EPS = (Module Level unique keys * Sum(Submodule level unique keys)) / period',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        for module_name in module_names:
            # Get module-level unique key from module conf.yml
            module_level_unique_key = self._get_module_level_unique_key(module_name, node_name)
            
            # Get all submodules for this module
            module_submodules = {
                path: config for path, config in submodule_configs.items()
                if config['module_name'] == module_name and config['has_unique_key_config']
            }
            
            # Calculate sum of submodule unique keys
            submodule_sum = 0
            submodule_details = []
            
            for submodule_path, config_info in module_submodules.items():
                submodule_unique_key = config_info['config_data']['uniquekey'].get('NumUniqKey', 0)
                submodule_sum += submodule_unique_key
                
                submodule_details.append({
                    'name': config_info['submodule_name'],
                    'path': submodule_path,
                    'unique_key_value': submodule_unique_key
                })
            
            # Calculate EPS for this module
            module_eps = (module_level_unique_key * submodule_sum) / period if period > 0 else 0
            
            eps_results['modules'][module_name] = {
                'module_level_unique_key': module_level_unique_key,
                'submodule_count': len(module_submodules),
                'submodule_unique_keys_sum': submodule_sum,
                'calculated_eps': module_eps,
                'submodule_details': submodule_details,
                'calculation': f"({module_level_unique_key} * {submodule_sum}) / {period} = {module_eps}"
            }
            
            eps_results['total_eps'] += module_eps
            
            self.cluster_logger.info(
                f"Module {module_name} EPS: {module_eps} "
                f"(Module key: {module_level_unique_key}, Submodule sum: {submodule_sum})"
            )
        
        eps_results['summary'] = {
            'total_modules_analyzed': len(module_names),
            'total_eps_all_modules': eps_results['total_eps'],
            'average_eps_per_module': eps_results['total_eps'] / len(module_names) if module_names else 0
        }
        
        return eps_results
    
    def _get_module_level_unique_key(self, module_name: str, node_name: str = None) -> int:
        """
        Get the module-level unique key value from module's conf.yml
        
        Args:
            module_name: Name of the module
            node_name: Node name to get config from
            
        Returns:
            Module level unique key value (defaults to 1 if not found)
        """
        try:
            if node_name:
                snapshot_dir = self.conf_snapshots_dir / node_name / "conf.d" / module_name
            else:
                # Use first available node snapshot
                available_nodes = [d.name for d in self.conf_snapshots_dir.iterdir() 
                                 if d.is_dir() and (d / "conf.d").exists()]
                if not available_nodes:
                    logger.warning("No node snapshots available for module level unique key lookup")
                    return 1
                
                snapshot_dir = self.conf_snapshots_dir / available_nodes[0] / "conf.d" / module_name
            
            module_conf_path = snapshot_dir / "conf.yml"
            
            if not module_conf_path.exists():
                logger.warning(f"Module config file not found: {module_conf_path}")
                return 1
            
            with open(module_conf_path, 'r') as f:
                module_config = yaml.safe_load(f) or {}
            
            # Look for unique key configuration in module conf.yml
            if isinstance(module_config, dict) and 'uniquekey' in module_config:
                if isinstance(module_config['uniquekey'], dict):
                    module_unique_key = module_config['uniquekey'].get('NumUniqKey', 1)
                    return module_unique_key
            
            # If no unique key found, default to 1
            logger.info(f"No module-level unique key found for {module_name}, using default value 1")
            return 1
            
        except Exception as e:
            logger.warning(f"Error getting module level unique key for {module_name}: {e}")
            return 1
    
    def get_all_modules_eps_summary(self, node_name: str = None, period: int = 1) -> Dict[str, Any]:
        """
        Get EPS summary for all modules with unique key configurations
        
        Args:
            node_name: Node name to fetch from (if None, uses local snapshot)
            period: Time period in seconds (default: 1 second)
            
        Returns:
            Dict with EPS summary for all modules
        """
        if node_name:
            # Fetch fresh config from remote node
            fetch_success = self.fetch_node_config(node_name)
            if not fetch_success:
                logger.warning(f"Failed to fetch config from node {node_name}, using cached data")
        
        submodule_configs = self.get_all_submodule_configs(node_name)
        
        # Get all unique module names that have submodules with unique keys
        module_names = list(set(
            config['module_name'] for config in submodule_configs.values()
            if config['has_unique_key_config']
        ))
        
        return self.get_module_eps_calculation(module_names, node_name, period)
    
    def get_quick_eps_summary(self, module_names: List[str], node_name: str, period: int = 1) -> Dict[str, Any]:
        """
        Get a quick EPS summary for selected modules - simplified output for web interface
        
        Args:
            module_names: List of module names to calculate EPS for
            node_name: Node name to fetch configuration from (required)
            period: Time period in seconds (default: 1 second)
            
        Returns:
            Simplified dict with EPS information for web interface
        """
        full_eps_data = self.get_module_eps_calculation(module_names, node_name, period)
        
        # Create simplified summary for web interface
        quick_summary = {
            'node_name': node_name,
            'period_seconds': period,
            'total_eps': full_eps_data['total_eps'],
            'module_count': len(module_names),
            'modules': []
        }
        
        for module_name in module_names:
            if module_name in full_eps_data['modules']:
                module_data = full_eps_data['modules'][module_name]
                quick_summary['modules'].append({
                    'name': module_name,
                    'eps': module_data['calculated_eps'],
                    'module_unique_key': module_data['module_level_unique_key'],
                    'submodule_count': module_data['submodule_count'],
                    'submodule_keys_sum': module_data['submodule_unique_keys_sum']
                })
            else:
                # Module not found or has no unique key configs
                quick_summary['modules'].append({
                    'name': module_name,
                    'eps': 0,
                    'module_unique_key': 0,
                    'submodule_count': 0,
                    'submodule_keys_sum': 0,
                    'error': 'Module not found or has no unique key configurations'
                })
        
        # Sort modules by EPS (highest first)
        quick_summary['modules'].sort(key=lambda x: x['eps'], reverse=True)
        
        return quick_summary
    
    def get_submodule_unique_key_summary(self, node_name: str = None) -> Dict[str, Any]:
        """
        Get a summary of all submodules and their current NumUniqKey values
        
        Args:
            node_name: Optional node name to fetch from, if None uses local snapshot
            
        Returns:
            Dict with summary information
        """
        submodule_configs = self.get_all_submodule_configs(node_name)
        
        summary = {
            'total_submodules': 0,
            'submodules_with_unique_keys': 0,
            'modules': {},
            'submodule_details': []
        }
        
        for submodule_path, config_info in submodule_configs.items():
            summary['total_submodules'] += 1
            
            module_name = config_info['module_name']
            if module_name not in summary['modules']:
                summary['modules'][module_name] = {
                    'total_submodules': 0,
                    'submodules_with_unique_keys': 0,
                    'submodules': []
                }
                
            summary['modules'][module_name]['total_submodules'] += 1
            
            # Extract current NumUniqKey value
            current_value = None
            has_unique_key = config_info['has_unique_key_config']
            
            if has_unique_key:
                current_value = config_info['config_data']['uniquekey'].get('NumUniqKey')
                summary['submodules_with_unique_keys'] += 1
                summary['modules'][module_name]['submodules_with_unique_keys'] += 1
            
            submodule_detail = {
                'path': submodule_path,
                'module_name': module_name,
                'submodule_name': config_info['submodule_name'],
                'has_unique_key_config': has_unique_key,
                'current_num_uniq_key': current_value,
                'file_path': config_info['file_path']
            }
            
            summary['submodule_details'].append(submodule_detail)
            summary['modules'][module_name]['submodules'].append(submodule_detail)
            
        return summary

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

    def push_all_local_configs_to_node(self, node_name: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Push all configuration files from the node's snapshot directory to replace the ones on a VM
        
        Args:
            node_name: Name of the target node
            create_backup: Whether to create backups before pushing
            
        Returns:
            dict: Results with success status, files pushed, and any errors
        """
        result = {
            'success': False,
            'files_pushed': 0,
            'total_files': 0,
            'failed_files': [],
            'errors': []
        }
        
        nodes = self.get_nodes()
        if node_name not in nodes:
            result['errors'].append(f"Node {node_name} not found")
            return result
            
        node_config = nodes[node_name]
        if not node_config.get('enabled', True):
            result['errors'].append(f"Node {node_name} is disabled")
            return result
        
        try:
            # Get all configuration files from the node's snapshot directory
            local_config_dir = self.conf_snapshots_dir / node_name / "conf.d"
            if not local_config_dir.exists():
                result['errors'].append(f"Node snapshot directory not found: {local_config_dir}")
                return result
            
            # Find all YAML files in the node's snapshot conf.d directory
            config_files = []
            for file_path in local_config_dir.rglob("*.yml"):
                if file_path.is_file():
                    config_files.append(file_path)
            
            result['total_files'] = len(config_files)
            
            if not config_files:
                result['errors'].append(f"No configuration files found in node snapshot directory: {local_config_dir}")
                return result
            
            self.cluster_logger.info(f"Starting bulk push of {len(config_files)} files to {node_name}")
            
            # Create overall backup if requested
            if create_backup:
                backup_name = f"bulk_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.cluster_logger.info(f"Creating backup: {backup_name}")
            
            # Push each file
            ssh = None
            sftp = None
            
            try:
                # Create single connection for all transfers
                ssh, sftp = self._create_ssh_connection(node_config)
                remote_conf_dir = node_config['conf_dir'].rstrip('/')
                
                for local_file in config_files:
                    try:
                        # Calculate relative path
                        relative_path = local_file.relative_to(local_config_dir)
                        remote_file_path = f"{remote_conf_dir}/{relative_path}"
                        
                        # Ensure remote directory exists
                        remote_dir = os.path.dirname(remote_file_path)
                        try:
                            ssh.exec_command(f"mkdir -p '{remote_dir}'")
                            time.sleep(0.1)  # Brief pause for directory creation
                        except Exception:
                            pass  # Directory might already exist
                        
                        # Push the file
                        sftp.put(str(local_file), remote_file_path)
                        result['files_pushed'] += 1
                        
                        self.cluster_logger.info(f"Pushed {relative_path} to {node_name}")
                        
                    except Exception as e:
                        error_msg = f"Failed to push {local_file.name}: {str(e)}"
                        result['failed_files'].append({
                            'file': str(local_file),
                            'error': error_msg
                        })
                        self.cluster_logger.error(f"Error pushing {local_file} to {node_name}: {e}")
                
            finally:
                if sftp:
                    sftp.close()
                if ssh:
                    ssh.close()
            
            # Determine overall success
            result['success'] = result['files_pushed'] > 0
            
            if result['success']:
                success_rate = (result['files_pushed'] / result['total_files']) * 100
                self.cluster_logger.info(
                    f"Bulk push to {node_name} completed: {result['files_pushed']}/{result['total_files']} "
                    f"files ({success_rate:.1f}% success rate)"
                )
            else:
                self.cluster_logger.error(f"Bulk push to {node_name} failed: no files were pushed")
            
        except Exception as e:
            error_msg = f"Bulk push operation failed: {str(e)}"
            result['errors'].append(error_msg)
            self.cluster_logger.error(f"Error in bulk push to {node_name}: {e}")
        
        return result

    def push_all_local_configs_to_all_nodes(self, target_nodes: Optional[List[str]] = None, 
                                          create_backup: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Push configuration files from each node's snapshot directory to multiple nodes
        
        Args:
            target_nodes: List of node names to push to (if None, pushes to all enabled nodes)
            create_backup: Whether to create backups before pushing
            
        Returns:
            dict: Results for each node
        """
        if target_nodes is None:
            target_nodes = list(self.get_enabled_nodes().keys())
        
        results = {}
        
        self.cluster_logger.info(f"Starting bulk push to {len(target_nodes)} nodes: {target_nodes}")
        
        for node_name in target_nodes:
            self.cluster_logger.info(f"Processing node: {node_name}")
            results[node_name] = self.push_all_local_configs_to_node(node_name, create_backup)
        
        # Log summary
        successful_nodes = sum(1 for result in results.values() if result['success'])
        total_files_pushed = sum(result['files_pushed'] for result in results.values())
        
        self.cluster_logger.info(
            f"Bulk push completed: {successful_nodes}/{len(target_nodes)} nodes successful, "
            f"{total_files_pushed} total files pushed"
        )
        
        return results


# Global cluster manager instance
cluster_manager = None

def get_cluster_manager() -> ClusterManager:
    """Get or create global cluster manager instance"""
    global cluster_manager
    if cluster_manager is None:
        cluster_manager = ClusterManager()
    return cluster_manager
