"""
Streamlit UI components for cluster management
"""
import streamlit as st
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import time
from datetime import datetime

from core.cluster_manager import get_cluster_manager, NodeConnectionError, ConfigSyncError
from core.yaml_editor import yaml_editor

logger = logging.getLogger(__name__)

def render_cluster_overview():
    """Render the cluster overview section"""
    st.header("🌐 Cluster Overview")
    
    cluster_mgr = get_cluster_manager()
    status = cluster_mgr.get_cluster_status()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Nodes", status['total_nodes'])
    with col2:
        st.metric("Enabled Nodes", status['enabled_nodes'])
    with col3:
        st.metric("Disabled Nodes", status['disabled_nodes'])
    with col4:
        synced_nodes = sum(1 for node_status in status['nodes'].values() 
                          if node_status['has_snapshot'])
        st.metric("Synced Nodes", synced_nodes)
    
    # Nodes table
    if status['nodes']:
        st.subheader("Node Status")
        
        nodes_data = []
        for node_name, node_status in status['nodes'].items():
            nodes_data.append({
                'Node': node_name,
                'Host': node_status['host'] or 'N/A',
                'Status': '🟢 Enabled' if node_status['enabled'] else '🔴 Disabled',
                'Synced': '✅ Yes' if node_status['has_snapshot'] else '❌ No',
                'Config Files': node_status['config_files'],
                'Last Sync': node_status['last_sync'] or 'Never'
            })
        
        st.dataframe(nodes_data, use_container_width=True)
    else:
        st.info("No nodes configured. Add nodes using the Node Management section.")

def render_node_management():
    """Render the node management section"""
    st.header("⚙️ Node Management")
    
    cluster_mgr = get_cluster_manager()
    
    # Add new node
    with st.expander("➕ Add New Node", expanded=False):
        with st.form("add_node_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                node_name = st.text_input("Node Name*", help="Unique identifier for the node")
                host = st.text_input("Host/IP Address*", help="SSH host or IP address")
                user = st.text_input("SSH Username*", value="vunet")
            
            with col2:
                key_path = st.text_input("SSH Key Path*", value="~/.ssh/id_rsa")
                conf_dir = st.text_input("Conf.d Directory*", 
                                       value="/home/vunet/vuDataSim/vuDataSim/conf.d")
                binary_dir = st.text_input("Binary Directory*", 
                                         value="/home/vunet/vuDataSim/vuDataSim/bin")
            
            description = st.text_area("Description (Optional)")
            enabled = st.checkbox("Enabled", value=True)
            
            if st.form_submit_button("Add Node", type="primary"):
                if node_name and host and user and key_path and conf_dir and binary_dir:
                    success = cluster_mgr.add_node(
                        name=node_name,
                        host=host,
                        user=user,
                        key_path=key_path,
                        conf_dir=conf_dir,
                        binary_dir=binary_dir,
                        description=description,
                        enabled=enabled
                    )
                    
                    if success:
                        st.success(f"Node '{node_name}' added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to add node '{node_name}'")
                else:
                    st.error("Please fill in all required fields (marked with *)")
    
    # Manage existing nodes
    nodes = cluster_mgr.get_nodes()
    if nodes:
        st.subheader("Existing Nodes")
        
        for node_name, node_config in nodes.items():
            with st.expander(f"📋 {node_name} ({node_config['host']})", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Host:** {node_config['host']}")
                    st.write(f"**User:** {node_config['user']}")
                    st.write(f"**Conf Directory:** {node_config['conf_dir']}")
                    st.write(f"**Binary Directory:** {node_config['binary_dir']}")
                    st.write(f"**Status:** {'🟢 Enabled' if node_config.get('enabled', True) else '🔴 Disabled'}")
                    if node_config.get('description'):
                        st.write(f"**Description:** {node_config['description']}")
                
                with col2:
                    if st.button(f"🗑️ Remove", key=f"remove_{node_name}"):
                        if cluster_mgr.remove_node(node_name):
                            st.success(f"Node '{node_name}' removed successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to remove node '{node_name}'")

def render_config_sync():
    """Render the configuration synchronization section"""
    st.header("🔄 Configuration Sync")
    
    cluster_mgr = get_cluster_manager()
    enabled_nodes = cluster_mgr.get_enabled_nodes()
    
    if not enabled_nodes:
        st.warning("No enabled nodes found. Please add and enable nodes first.")
        return
    
    # Sync controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        selected_nodes = st.multiselect(
            "Select Nodes to Sync",
            options=list(enabled_nodes.keys()),
            default=list(enabled_nodes.keys()),
            help="Choose which nodes to fetch configurations from"
        )
    
    with col2:
        sync_option = st.selectbox(
            "Sync Option",
            ["Fetch Only", "Fetch & Backup", "Full Sync"],
            help="Choose sync behavior"
        )
    
    with col3:
        st.write("")  # Spacer
        if st.button("🔄 Start Sync", type="primary"):
            if selected_nodes:
                sync_configurations(selected_nodes, sync_option)
            else:
                st.error("Please select at least one node to sync")
    
    # Add separator
    st.markdown("---")
    
    # Push local configurations section
    render_local_push_section(enabled_nodes)
    
    # Sync status
    if 'sync_status' in st.session_state:
        render_sync_status()
    
    # Push status 
    if 'push_status' in st.session_state:
        render_push_status()

def sync_configurations(node_names: List[str], sync_option: str):
    """Execute configuration sync for selected nodes"""
    cluster_mgr = get_cluster_manager()
    
    # Initialize sync status
    st.session_state.sync_status = {
        'in_progress': True,
        'results': {},
        'start_time': datetime.now(),
        'total_nodes': len(node_names)
    }
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    try:
        for i, node_name in enumerate(node_names):
            status_container.info(f"Syncing node {i+1}/{len(node_names)}: {node_name}")
            
            # Fetch configuration
            success = cluster_mgr.fetch_node_config(node_name)
            
            st.session_state.sync_status['results'][node_name] = {
                'success': success,
                'files_synced': len(cluster_mgr.get_node_snapshot_files(node_name)) if success else 0,
                'error': None if success else "Connection or sync failed"
            }
            
            # Update progress
            progress_bar.progress((i + 1) / len(node_names))
            
            # Brief pause to show progress
            time.sleep(0.5)
        
        # Complete sync
        st.session_state.sync_status['in_progress'] = False
        st.session_state.sync_status['end_time'] = datetime.now()
        
        # Show completion message
        success_count = sum(1 for result in st.session_state.sync_status['results'].values() 
                          if result['success'])
        
        if success_count == len(node_names):
            st.success(f"✅ Successfully synced all {len(node_names)} nodes!")
        elif success_count > 0:
            st.warning(f"⚠️ Synced {success_count}/{len(node_names)} nodes. Check details below.")
        else:
            st.error("❌ Failed to sync any nodes. Check node configurations and connectivity.")
    
    except Exception as e:
        st.session_state.sync_status['in_progress'] = False
        st.session_state.sync_status['error'] = str(e)
        st.error(f"Sync failed with error: {e}")
    
    finally:
        progress_bar.empty()
        status_container.empty()

def render_sync_status():
    """Render sync status and results"""
    status = st.session_state.sync_status
    
    if status['in_progress']:
        st.info("🔄 Sync in progress...")
        return
    
    # Sync summary
    st.subheader("Sync Results")
    
    success_count = sum(1 for result in status['results'].values() if result['success'])
    total_files = sum(result['files_synced'] for result in status['results'].values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Successful Nodes", f"{success_count}/{status['total_nodes']}")
    with col2:
        st.metric("Total Files Synced", total_files)
    with col3:
        duration = (status.get('end_time', status['start_time']) - status['start_time']).total_seconds()
        st.metric("Duration", f"{duration:.1f}s")
    
    # Detailed results
    if status['results']:
        results_data = []
        for node_name, result in status['results'].items():
            results_data.append({
                'Node': node_name,
                'Status': '✅ Success' if result['success'] else '❌ Failed',
                'Files Synced': result['files_synced'],
                'Error': result.get('error', '') or 'None'
            })
        
        st.dataframe(results_data, use_container_width=True)
    
    # Clear results button
    if st.button("Clear Results"):
        del st.session_state.sync_status
        st.rerun()

def render_local_push_section(enabled_nodes: Dict[str, Any]):
    """Render the section for pushing local configurations to VMs"""
    st.subheader("🚀 Push Local Changes to VMs")
    st.markdown("Push your local configuration changes to replace the configurations on remote VMs")
    
    cluster_mgr = get_cluster_manager()
    
    # Display local config info
    # The conf.d directory is in the project root, not in the web UI directory
    local_config_dir = Path(__file__).parent.parent.parent.parent / "conf.d"
    
    if not local_config_dir.exists():
        st.error(f"❌ Local configuration directory not found: {local_config_dir}")
        return
    
    # Count local config files
    local_files = list(local_config_dir.rglob("*.yml"))
    
    st.info(f"📁 Found {len(local_files)} configuration files in local conf.d directory")
    
    # Show some example files
    if local_files:
        with st.expander("📋 Local Configuration Files Preview", expanded=False):
            example_files = local_files[:10]  # Show first 10 files
            for file_path in example_files:
                relative_path = file_path.relative_to(local_config_dir)
                st.text(f"📄 {relative_path}")
            if len(local_files) > 10:
                st.text(f"... and {len(local_files) - 10} more files")
    
    # Push controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        target_nodes = st.multiselect(
            "Select Target Nodes",
            options=list(enabled_nodes.keys()),
            default=list(enabled_nodes.keys()),
            help="Choose which nodes to push configurations to"
        )
    
    with col2:
        create_backup = st.checkbox(
            "Create Backup",
            value=True,
            help="Create backups before replacing configurations"
        )
    
    with col3:
        st.write("")  # Spacer
        push_button = st.button(
            "🚀 Push All Configs",
            type="primary",
            help="Replace VM configurations with local configurations"
        )
    
    # Warning about the operation
    if target_nodes:
        st.warning(
            f"⚠️ **Warning**: This will replace ALL configuration files on "
            f"{len(target_nodes)} node(s) with your local versions. "
            f"{'Backups will be created.' if create_backup else 'No backups will be created.'}"
        )
    
    # Execute push operation
    if push_button:
        if not target_nodes:
            st.error("Please select at least one target node")
        elif not local_files:
            st.error("No local configuration files found to push")
        else:
            push_all_configurations(target_nodes, create_backup)

def push_all_configurations(target_nodes: List[str], create_backup: bool):
    """Execute bulk push operation to all selected nodes"""
    cluster_mgr = get_cluster_manager()
    
    # Initialize push status
    st.session_state.push_status = {
        'in_progress': True,
        'results': {},
        'start_time': datetime.now(),
        'total_nodes': len(target_nodes),
        'create_backup': create_backup
    }
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    try:
        st.info("🚀 Starting bulk push operation...")
        
        for i, node_name in enumerate(target_nodes):
            status_container.info(f"Pushing to node {i+1}/{len(target_nodes)}: {node_name}")
            
            # Push all configurations to this node
            result = cluster_mgr.push_all_local_configs_to_node(node_name, create_backup)
            
            st.session_state.push_status['results'][node_name] = result
            
            # Update progress
            progress_bar.progress((i + 1) / len(target_nodes))
            
            # Brief pause to show progress
            time.sleep(0.5)
        
        # Complete push operation
        st.session_state.push_status['in_progress'] = False
        st.session_state.push_status['end_time'] = datetime.now()
        
        # Show completion message
        successful_nodes = sum(1 for result in st.session_state.push_status['results'].values() 
                             if result['success'])
        total_files_pushed = sum(result['files_pushed'] for result in st.session_state.push_status['results'].values())
        
        if successful_nodes == len(target_nodes):
            st.success(f"✅ Successfully pushed configurations to all {len(target_nodes)} nodes! "
                      f"Total files pushed: {total_files_pushed}")
        elif successful_nodes > 0:
            st.warning(f"⚠️ Pushed to {successful_nodes}/{len(target_nodes)} nodes. "
                      f"Total files pushed: {total_files_pushed}. Check details below.")
        else:
            st.error("❌ Failed to push to any nodes. Check node configurations and connectivity.")
    
    except Exception as e:
        st.session_state.push_status['in_progress'] = False
        st.session_state.push_status['error'] = str(e)
        st.error(f"Push operation failed with error: {e}")
    
    finally:
        progress_bar.empty()
        status_container.empty()

def render_push_status():
    """Render push operation status and results"""
    status = st.session_state.push_status
    
    if status['in_progress']:
        st.info("🚀 Push operation in progress...")
        return
    
    # Push summary
    st.subheader("📊 Push Results")
    
    successful_nodes = sum(1 for result in status['results'].values() if result['success'])
    total_files_pushed = sum(result['files_pushed'] for result in status['results'].values())
    total_files_attempted = sum(result['total_files'] for result in status['results'].values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Successful Nodes", f"{successful_nodes}/{status['total_nodes']}")
    with col2:
        st.metric("Files Pushed", f"{total_files_pushed}/{total_files_attempted}")
    with col3:
        duration = (status.get('end_time', status['start_time']) - status['start_time']).total_seconds()
        st.metric("Duration", f"{duration:.1f}s")
    
    # Detailed results
    if status['results']:
        st.subheader("📋 Detailed Results")
        
        for node_name, result in status['results'].items():
            with st.expander(f"{'✅' if result['success'] else '❌'} {node_name}", 
                           expanded=not result['success']):
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Files Pushed", f"{result['files_pushed']}/{result['total_files']}")
                with col2:
                    success_rate = (result['files_pushed'] / result['total_files'] * 100) if result['total_files'] > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                with col3:
                    st.metric("Failed Files", len(result.get('failed_files', [])))
                
                # Show errors if any
                if result.get('errors'):
                    st.error("**Errors:**")
                    for error in result['errors']:
                        st.text(f"• {error}")
                
                # Show failed files if any
                if result.get('failed_files'):
                    st.warning("**Failed Files:**")
                    for failed_file in result['failed_files']:
                        st.text(f"• {failed_file['file']}: {failed_file['error']}")
                
                if result['success'] and result['files_pushed'] > 0:
                    st.success(f"✅ Successfully pushed {result['files_pushed']} configuration files to {node_name}")
    
    # Clear results button
    if st.button("Clear Push Results"):
        del st.session_state.push_status
        st.rerun()

def render_config_browser():
    """Render the configuration browser and editor"""
    st.header("📁 Configuration Browser")
    
    cluster_mgr = get_cluster_manager()
    snapshot_files = cluster_mgr.get_all_snapshot_files()
    
    if not any(files for files in snapshot_files.values()):
        st.info("No configuration snapshots available. Please sync nodes first.")
        return
    
    # Node selection
    available_nodes = [node for node, files in snapshot_files.items() if files]
    selected_node = st.selectbox("Select Node", available_nodes)
    
    if not selected_node:
        return
    
    files = snapshot_files[selected_node]
    
    # File browser
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Configuration Files")
        
        # Group files by directory
        file_groups = {}
        for file_path in files:
            # Get relative path from conf.d
            try:
                conf_dir = cluster_mgr.conf_snapshots_dir / selected_node / "conf.d"
                rel_path = file_path.relative_to(conf_dir)
                dir_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'Root'
                
                if dir_name not in file_groups:
                    file_groups[dir_name] = []
                file_groups[dir_name].append((file_path, rel_path.name))
            except ValueError:
                continue
        
        selected_file = None
        for dir_name, file_list in sorted(file_groups.items()):
            with st.expander(f"📂 {dir_name}", expanded=(dir_name == 'Root')):
                for file_path, file_name in file_list:
                    if st.button(f"📄 {file_name}", key=str(file_path)):
                        st.session_state.selected_file = file_path
    
    with col2:
        if 'selected_file' in st.session_state and st.session_state.selected_file:
            render_config_editor(selected_node, st.session_state.selected_file)

def render_config_editor(node_name: str, file_path: Path):
    """Render the configuration file editor"""
    st.subheader(f"Editing: {file_path.name}")
    
    cluster_mgr = get_cluster_manager()
    
    try:
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Display file info
        st.caption(f"Node: {node_name} | Path: {file_path}")
        
        # Edit content
        edited_content = st.text_area(
            "File Content",
            value=content,
            height=400,
            help="Edit the YAML configuration. Comments and formatting will be preserved."
        )
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Locally", type="primary"):
                try:
                    with open(file_path, 'w') as f:
                        f.write(edited_content)
                    st.success("File saved locally!")
                except Exception as e:
                    st.error(f"Error saving file: {e}")
        
        with col2:
            if st.button("🚀 Push to Node"):
                success = cluster_mgr.push_config_to_node(node_name, file_path)
                if success:
                    st.success(f"File pushed to {node_name}!")
                else:
                    st.error(f"Failed to push file to {node_name}")
        
        with col3:
            if st.button("🔧 Validate YAML"):
                try:
                    yaml.safe_load(edited_content)
                    st.success("✅ YAML is valid!")
                except yaml.YAMLError as e:
                    st.error(f"❌ YAML validation failed: {e}")
        
        with col4:
            if st.button("🔄 Restart vuDataSim"):
                success = cluster_mgr.restart_vudatasim(node_name)
                if success:
                    st.success(f"vuDataSim restarted on {node_name}!")
                else:
                    st.error(f"Failed to restart vuDataSim on {node_name}")
        
        # EPS Calculator integration
        if st.checkbox("Show EPS Calculator"):
            render_eps_calculator_for_config(edited_content)
            
    except Exception as e:
        st.error(f"Error loading file: {e}")

def render_eps_calculator_for_config(yaml_content: str):
    """Render EPS calculator for the current configuration"""
    try:
        config_data = yaml.safe_load(yaml_content)
        
        # Look for EPS-relevant parameters
        if isinstance(config_data, dict):
            # Try to find NumUniqKey and period parameters
            num_uniq_key = None
            period = None
            
            # Search through nested structure
            def find_params(data, path=""):
                nonlocal num_uniq_key, period
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key.lower() in ['numuniqkey', 'num_uniq_key']:
                            num_uniq_key = value
                        elif key.lower() in ['period', 'time_period']:
                            period = value
                        elif isinstance(value, (dict, list)):
                            find_params(value, f"{path}.{key}" if path else key)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        find_params(item, f"{path}[{i}]" if path else f"[{i}]")
            
            find_params(config_data)
            
            if num_uniq_key is not None or period is not None:
                st.subheader("📊 EPS Calculator")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_num_uniq_key = st.number_input(
                        "NumUniqKey", 
                        value=int(num_uniq_key) if num_uniq_key else 1,
                        min_value=1
                    )
                with col2:
                    # Parse period from duration string (e.g., "1s", "250ms") to seconds
                    try:
                        period_seconds = yaml_editor._parse_duration(str(period)) if period else 1.0
                    except (ValueError, TypeError):
                        # Fallback: try to parse as float directly
                        try:
                            period_seconds = float(period) if period else 1.0
                        except (ValueError, TypeError):
                            period_seconds = 1.0
                    
                    new_period = st.number_input(
                        "Period (seconds)", 
                        value=period_seconds,
                        min_value=0.1
                    )
                
                # Calculate EPS
                if new_period > 0:
                    eps = new_num_uniq_key / new_period
                    st.metric("Estimated EPS", f"{eps:.2f}")
                    
                    # Show impact of changes
                    if num_uniq_key and period:
                        old_eps = num_uniq_key / period_seconds
                        change = ((eps - old_eps) / old_eps) * 100 if old_eps > 0 else 0
                        st.metric("EPS Change", f"{change:+.1f}%")
            else:
                st.info("No EPS-relevant parameters found in this configuration.")
                
    except Exception as e:
        st.warning(f"Could not parse configuration for EPS calculation: {e}")

def render_cluster_sync_page():
    """Main function to render the cluster sync page"""
    st.set_page_config(
        page_title="Cluster Configuration Manager",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("🌐 Cluster Configuration Manager")
    st.markdown("Centralized management for vuDataSim configurations across multiple nodes")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "⚙️ Node Management", 
        "🔄 Config Sync", 
        "📁 Config Browser",
        "🔧 Bulk Editor"
    ])
    
    with tab1:
        render_cluster_overview()
    
    with tab2:
        render_node_management()
    
    with tab3:
        render_config_sync()
    
    with tab4:
        render_config_browser()
    
    with tab5:
        render_bulk_submodule_editor()

def render_bulk_submodule_editor():
    """Render the bulk submodule editor section"""
    st.header("🔧 Bulk Submodule Editor")
    st.markdown("Edit unique key values across all submodules in one place")
    
    cluster_mgr = get_cluster_manager()
    status = cluster_mgr.get_cluster_status()
    
    if not status['nodes']:
        st.info("No nodes configured. Add nodes first to enable bulk editing.")
        return
    
    enabled_nodes = [name for name, node_status in status['nodes'].items() 
                    if node_status['enabled']]
    
    if not enabled_nodes:
        st.warning("No enabled nodes found. Enable at least one node to perform bulk editing.")
        return
    
    # Node selection for preview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        preview_node = st.selectbox(
            "Select node to preview current configuration:",
            ["Local Configuration"] + enabled_nodes,
            help="Choose which node's configuration to display for editing"
        )
    
    with col2:
        if st.button("🔄 Refresh Configuration", key="refresh_config"):
            if preview_node != "Local Configuration":
                with st.spinner(f"Fetching configuration from {preview_node}..."):
                    cluster_mgr.fetch_node_config(preview_node)
            st.success("Configuration refreshed!")
            time.sleep(1)
            st.rerun()
    
    # Get submodule summary
    node_name = None if preview_node == "Local Configuration" else preview_node
    
    with st.spinner("Loading submodule configurations..."):
        try:
            summary = cluster_mgr.get_submodule_unique_key_summary(node_name)
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
            return
    
    if summary['total_submodules'] == 0:
        st.warning("No submodules found in the configuration.")
        return
    
    # Display summary statistics
    st.subheader("📊 Configuration Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Submodules", summary['total_submodules'])
    with col2:
        st.metric("With Unique Keys", summary['submodules_with_unique_keys'])
    with col3:
        st.metric("Total Modules", len(summary['modules']))
    with col4:
        total_unique_keys = sum(
            detail['current_num_uniq_key'] or 0 
            for detail in summary['submodule_details']
            if detail['current_num_uniq_key'] is not None
        )
        st.metric("Total Unique Keys", f"{total_unique_keys:,}")
    
    # Bulk editing interface
    st.subheader("✏️ Bulk Edit Unique Keys")
    
    # Create tabs for different editing modes
    tab1, tab2, tab3 = st.tabs(["📝 Individual Edit", "🎯 Pattern Edit", "📋 Bulk Operations"])
    
    with tab1:
        render_individual_submodule_editor(summary, enabled_nodes, cluster_mgr)
    
    with tab2:
        render_pattern_submodule_editor(summary, enabled_nodes, cluster_mgr)
    
    with tab3:
        render_bulk_operations_editor(summary, enabled_nodes, cluster_mgr)

def render_individual_submodule_editor(summary, enabled_nodes, cluster_mgr):
    """Render individual submodule editor"""
    st.markdown("Edit unique key values for individual submodules:")
    
    # Group by module for better organization
    for module_name, module_info in summary['modules'].items():
        with st.expander(f"📁 {module_name} ({module_info['submodules_with_unique_keys']} submodules with unique keys)"):
            
            updates_for_module = {}
            
            for submodule in module_info['submodules']:
                if not submodule['has_unique_key_config']:
                    st.info(f"⚠️ {submodule['submodule_name']}: No unique key configuration")
                    continue
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.text(f"📄 {submodule['submodule_name']}")
                
                with col2:
                    current_value = submodule['current_num_uniq_key'] or 0
                    st.text(f"Current: {current_value:,}")
                
                with col3:
                    new_value = st.number_input(
                        "New value:",
                        min_value=0,
                        value=current_value,
                        key=f"individual_{submodule['path']}",
                        label_visibility="collapsed"
                    )
                    
                    if new_value != current_value:
                        updates_for_module[submodule['path']] = new_value
            
            # Apply changes for this module
            if updates_for_module:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    target_nodes = st.multiselect(
                        f"Target nodes for {module_name}:",
                        enabled_nodes,
                        default=enabled_nodes,
                        key=f"nodes_{module_name}"
                    )
                
                with col2:
                    create_backup = st.checkbox(
                        "Create backup",
                        value=True,
                        key=f"backup_{module_name}"
                    )
                
                if st.button(f"Apply Changes to {module_name}", 
                           key=f"apply_{module_name}",
                           type="primary"):
                    apply_submodule_changes(
                        cluster_mgr, updates_for_module, target_nodes, create_backup
                    )

def render_pattern_submodule_editor(summary, enabled_nodes, cluster_mgr):
    """Render pattern-based submodule editor"""
    st.markdown("Apply the same value to multiple submodules based on patterns:")
    
    # Pattern selection
    col1, col2 = st.columns(2)
    
    with col1:
        pattern_type = st.selectbox(
            "Select pattern type:",
            ["By Module", "By Submodule Name", "All Submodules"]
        )
    
    with col2:
        new_value = st.number_input(
            "New NumUniqKey value:",
            min_value=0,
            value=1000,
            step=100
        )
    
    # Show matching submodules
    matching_submodules = []
    
    if pattern_type == "By Module":
        selected_modules = st.multiselect(
            "Select modules:",
            list(summary['modules'].keys()),
            help="All submodules in selected modules will be updated"
        )
        
        for detail in summary['submodule_details']:
            if (detail['has_unique_key_config'] and 
                detail['module_name'] in selected_modules):
                matching_submodules.append(detail)
                
    elif pattern_type == "By Submodule Name":
        available_names = set(detail['submodule_name'] 
                            for detail in summary['submodule_details']
                            if detail['has_unique_key_config'])
        
        selected_names = st.multiselect(
            "Select submodule names:",
            sorted(available_names),
            help="All submodules with these names will be updated"
        )
        
        for detail in summary['submodule_details']:
            if (detail['has_unique_key_config'] and 
                detail['submodule_name'] in selected_names):
                matching_submodules.append(detail)
                
    else:  # All Submodules
        matching_submodules = [
            detail for detail in summary['submodule_details']
            if detail['has_unique_key_config']
        ]
    
    # Show preview
    if matching_submodules:
        st.subheader("📋 Preview Changes")
        st.write(f"**{len(matching_submodules)} submodules** will be updated:")
        
        preview_data = []
        for detail in matching_submodules:
            preview_data.append({
                'Module': detail['module_name'],
                'Submodule': detail['submodule_name'],
                'Current Value': f"{detail['current_num_uniq_key'] or 0:,}",
                'New Value': f"{new_value:,}",
                'Change': f"{new_value - (detail['current_num_uniq_key'] or 0):+,}"
            })
        
        st.dataframe(preview_data, use_container_width=True)
        
        # Target nodes and options
        col1, col2 = st.columns(2)
        
        with col1:
            target_nodes = st.multiselect(
                "Target nodes:",
                enabled_nodes,
                default=enabled_nodes,
                key="pattern_target_nodes"
            )
        
        with col2:
            create_backup = st.checkbox(
                "Create backup before changes",
                value=True,
                key="pattern_backup"
            )
        
        # Apply changes
        if st.button("Apply Pattern Changes", type="primary", key="apply_pattern"):
            updates = {detail['path']: new_value for detail in matching_submodules}
            apply_submodule_changes(cluster_mgr, updates, target_nodes, create_backup)

def render_bulk_operations_editor(summary, enabled_nodes, cluster_mgr):
    """Render bulk operations editor"""
    st.markdown("Perform bulk operations on unique key values:")
    
    # Operation type
    operation = st.selectbox(
        "Select operation:",
        ["Multiply by factor", "Add/Subtract value", "Set minimum value", "Set maximum value"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if operation == "Multiply by factor":
            factor = st.number_input("Multiplication factor:", min_value=0.1, value=1.0, step=0.1)
        elif operation == "Add/Subtract value":
            adjustment = st.number_input("Value to add (negative to subtract):", value=0, step=100)
        elif operation == "Set minimum value":
            min_value = st.number_input("Minimum value:", min_value=0, value=1000, step=100)
        else:  # Set maximum value
            max_value = st.number_input("Maximum value:", min_value=1, value=10000, step=100)
    
    with col2:
        # Filter options
        filter_modules = st.multiselect(
            "Filter by modules (optional):",
            list(summary['modules'].keys()),
            help="Leave empty to apply to all modules"
        )
    
    # Calculate and preview changes
    if st.button("Preview Changes", key="bulk_preview"):
        updates = {}
        preview_data = []
        
        for detail in summary['submodule_details']:
            if not detail['has_unique_key_config']:
                continue
                
            if filter_modules and detail['module_name'] not in filter_modules:
                continue
                
            current_value = detail['current_num_uniq_key'] or 0
            
            if operation == "Multiply by factor":
                new_value = max(1, int(current_value * factor))
            elif operation == "Add/Subtract value":
                new_value = max(0, current_value + adjustment)
            elif operation == "Set minimum value":
                new_value = max(current_value, min_value)
            else:  # Set maximum value
                new_value = min(current_value, max_value)
            
            if new_value != current_value:
                updates[detail['path']] = new_value
                preview_data.append({
                    'Module': detail['module_name'],
                    'Submodule': detail['submodule_name'],
                    'Current Value': f"{current_value:,}",
                    'New Value': f"{new_value:,}",
                    'Change': f"{new_value - current_value:+,}"
                })
        
        if preview_data:
            st.subheader("📋 Bulk Operation Preview")
            st.write(f"**{len(preview_data)} submodules** will be updated:")
            st.dataframe(preview_data, use_container_width=True)
            
            # Store updates in session state for applying
            st.session_state.bulk_updates = updates
            
            # Target nodes and options
            col1, col2 = st.columns(2)
            
            with col1:
                target_nodes = st.multiselect(
                    "Target nodes:",
                    enabled_nodes,
                    default=enabled_nodes,
                    key="bulk_target_nodes"
                )
            
            with col2:
                create_backup = st.checkbox(
                    "Create backup before changes",
                    value=True,
                    key="bulk_backup"
                )
            
            # Apply changes
            if st.button("Apply Bulk Changes", type="primary", key="apply_bulk"):
                apply_submodule_changes(
                    cluster_mgr, st.session_state.bulk_updates, target_nodes, create_backup
                )
        else:
            st.info("No changes would be made with the current operation and filters.")

def apply_submodule_changes(cluster_mgr, updates, target_nodes, create_backup):
    """Apply submodule changes to target nodes"""
    if not updates or not target_nodes:
        st.warning("No updates to apply or no target nodes selected.")
        return
    
    st.subheader("🚀 Applying Changes")
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Apply changes to all target nodes
        all_results = cluster_mgr.bulk_edit_all_nodes_unique_keys(
            updates, target_nodes, create_backup
        )
        
        # Show results
        status_text.empty()
        progress_bar.empty()
        
        st.subheader("📊 Results Summary")
        
        for node_name, node_results in all_results.items():
            success_count = sum(1 for success in node_results.values() if success)
            total_count = len(node_results)
            
            if success_count == total_count:
                st.success(f"✅ {node_name}: All {total_count} updates successful")
            elif success_count > 0:
                st.warning(f"⚠️ {node_name}: {success_count}/{total_count} updates successful")
            else:
                st.error(f"❌ {node_name}: All updates failed")
            
            # Show detailed results in expandable section
            with st.expander(f"Details for {node_name}"):
                for submodule_path, success in node_results.items():
                    status_icon = "✅" if success else "❌"
                    new_value = updates[submodule_path]
                    st.write(f"{status_icon} {submodule_path}: NumUniqKey = {new_value:,}")
        
        # Show overall success rate
        total_operations = sum(len(results) for results in all_results.values())
        successful_operations = sum(
            sum(1 for success in results.values() if success)
            for results in all_results.values()
        )
        
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        
        if success_rate == 100:
            st.balloons()
            st.success(f"🎉 All operations completed successfully! ({successful_operations}/{total_operations})")
        elif success_rate > 0:
            st.info(f"📈 Partial success: {successful_operations}/{total_operations} operations completed ({success_rate:.1f}%)")
        else:
            st.error(f"💥 All operations failed: {successful_operations}/{total_operations}")
    
    except Exception as e:
        st.error(f"Error applying changes: {e}")
        logger.error(f"Error in apply_submodule_changes: {e}")

def render_eps_calculator():
    """Render the EPS Calculator & Viewer section"""
    st.header("📊 EPS Calculator & Viewer")
    st.markdown("Calculate Events Per Second (EPS) for selected modules based on configuration fetched from remote nodes")
    
    cluster_mgr = get_cluster_manager()
    status = cluster_mgr.get_cluster_status()
    
    if not status['nodes']:
        st.info("No nodes configured. Add nodes first to calculate EPS.")
        return
    
    enabled_nodes = [name for name, node_status in status['nodes'].items() 
                    if node_status['enabled']]
    
    if not enabled_nodes:
        st.warning("No enabled nodes found. Enable at least one node to calculate EPS.")
        return
    
    # Node and period selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_node = st.selectbox(
            "Select node to fetch configuration from:",
            enabled_nodes,
            help="Choose which node's configuration to use for EPS calculation"
        )
    
    with col2:
        time_period = st.selectbox(
            "Time period:",
            [1, 5, 10, 30, 60],
            format_func=lambda x: f"{x} second{'s' if x > 1 else ''}",
            help="Time period for EPS calculation"
        )
    
    with col3:
        if st.button("🔄 Refresh Config", key="refresh_eps_config"):
            with st.spinner(f"Fetching configuration from {selected_node}..."):
                success = cluster_mgr.fetch_node_config(selected_node)
                if success:
                    st.success("Configuration refreshed!")
                else:
                    st.error("Failed to refresh configuration")
            time.sleep(1)
            st.rerun()
    
    # Formula display
    st.info("**Formula:** EPS = (Module Level unique keys × Sum of Submodule unique keys) ÷ period")
    
    # Get available modules
    with st.spinner("Loading module configurations..."):
        try:
            summary = cluster_mgr.get_submodule_unique_key_summary(selected_node)
            available_modules = list(summary['modules'].keys())
            
            if not available_modules:
                st.warning("No modules with unique key configurations found.")
                return
                
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
            return
    
    # Module selection
    st.subheader("Select Modules to Analyze")
    
    # Quick selection buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 Select All", key="select_all_modules"):
            st.session_state.selected_modules = available_modules
    with col2:
        if st.button("🗑️ Clear All", key="clear_all_modules"):
            st.session_state.selected_modules = []
    with col3:
        if st.button("🔥 Top 5 by EPS", key="select_top_5"):
            # Get quick calculation to find top modules
            all_eps = cluster_mgr.get_all_modules_eps_summary(selected_node, 1)
            top_modules = sorted(
                all_eps['modules'].items(),
                key=lambda x: x[1]['calculated_eps'],
                reverse=True
            )[:5]
            st.session_state.selected_modules = [name for name, _ in top_modules]
    with col4:
        if st.button("⚡ High Performance", key="select_high_perf"):
            # Select modules with EPS > 10000
            all_eps = cluster_mgr.get_all_modules_eps_summary(selected_node, 1)
            high_perf = [name for name, data in all_eps['modules'].items() 
                        if data['calculated_eps'] > 10000]
            st.session_state.selected_modules = high_perf
    
    # Initialize session state for selected modules
    if 'selected_modules' not in st.session_state:
        st.session_state.selected_modules = []
    
    # Module checkboxes in columns
    modules_per_row = 4
    module_rows = [available_modules[i:i + modules_per_row] 
                   for i in range(0, len(available_modules), modules_per_row)]
    
    for row in module_rows:
        cols = st.columns(modules_per_row)
        for i, module in enumerate(row):
            with cols[i]:
                is_selected = module in st.session_state.selected_modules
                if st.checkbox(module, value=is_selected, key=f"module_{module}"):
                    if module not in st.session_state.selected_modules:
                        st.session_state.selected_modules.append(module)
                else:
                    if module in st.session_state.selected_modules:
                        st.session_state.selected_modules.remove(module)
    
    # Calculate EPS button
    if st.session_state.selected_modules:
        st.subheader(f"Selected Modules ({len(st.session_state.selected_modules)})")
        st.write(", ".join(st.session_state.selected_modules))
        
        if st.button("🧮 Calculate EPS", type="primary", key="calculate_eps"):
            with st.spinner("Calculating EPS..."):
                try:
                    eps_data = cluster_mgr.get_quick_eps_summary(
                        module_names=st.session_state.selected_modules,
                        node_name=selected_node,
                        period=time_period
                    )
                    
                    # Store results in session state
                    st.session_state.eps_results = eps_data
                    
                except Exception as e:
                    st.error(f"Error calculating EPS: {e}")
                    return
    
    # Display results if available
    if hasattr(st.session_state, 'eps_results') and st.session_state.eps_results:
        eps_data = st.session_state.eps_results
        
        st.subheader("📈 EPS Results")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total EPS", f"{eps_data['total_eps']:,.0f}")
        with col2:
            st.metric("Modules Analyzed", eps_data['module_count'])
        with col3:
            st.metric("Time Period", f"{eps_data['period_seconds']}s")
        with col4:
            avg_eps = eps_data['total_eps'] / eps_data['module_count'] if eps_data['module_count'] > 0 else 0
            st.metric("Avg EPS/Module", f"{avg_eps:,.0f}")
        
        # Module details table
        st.subheader("Module Breakdown")
        
        table_data = []
        for module in eps_data['modules']:
            if 'error' not in module:
                table_data.append({
                    'Module': module['name'],
                    'EPS': f"{module['eps']:,.0f}",
                    'Module Key': module['module_unique_key'],
                    'Submodules': module['submodule_count'],
                    'Sub Keys Sum': module['submodule_keys_sum'],
                    'Calculation': f"({module['module_unique_key']} × {module['submodule_keys_sum']}) ÷ {eps_data['period_seconds']}"
                })
            else:
                table_data.append({
                    'Module': module['name'],
                    'EPS': 'ERROR',
                    'Module Key': 'N/A',
                    'Submodules': 'N/A',
                    'Sub Keys Sum': 'N/A',
                    'Calculation': module['error']
                })
        
        st.dataframe(table_data, use_container_width=True)
        
        # Time period comparison
        if eps_data['total_eps'] > 0:
            st.subheader("📊 EPS at Different Time Intervals")
            
            comparison_data = []
            for period in [1, 5, 10, 30, 60]:
                eps_per_period = eps_data['total_eps'] * eps_data['period_seconds'] / period
                if period == 1:
                    unit = "second"
                elif period == 60:
                    unit = "minute"
                else:
                    unit = f"{period} seconds"
                
                comparison_data.append({
                    'Time Period': unit,
                    'EPS': f"{eps_per_period:,.1f}",
                    'Events per Period': f"{eps_per_period * period:,.0f}"
                })
            
            st.dataframe(comparison_data, use_container_width=True)
        
        # Export functionality
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View All Modules EPS", key="view_all_eps"):
                with st.spinner("Calculating EPS for all modules..."):
                    all_eps = cluster_mgr.get_all_modules_eps_summary(selected_node, time_period)
                    
                    st.subheader("🔥 All Modules EPS Ranking")
                    
                    # Sort by EPS
                    all_modules_sorted = sorted(
                        all_eps['modules'].items(),
                        key=lambda x: x[1]['calculated_eps'],
                        reverse=True
                    )
                    
                    ranking_data = []
                    for i, (module_name, module_data) in enumerate(all_modules_sorted):
                        ranking_data.append({
                            'Rank': i + 1,
                            'Module': module_name,
                            'EPS': f"{module_data['calculated_eps']:,.0f}",
                            'Module Key': module_data['module_level_unique_key'],
                            'Submodules': module_data['submodule_count'],
                            'Sub Keys Sum': module_data['submodule_unique_keys_sum']
                        })
                    
                    st.dataframe(ranking_data, use_container_width=True)
                    
                    st.metric("🔥 Total EPS (All Modules)", f"{all_eps['summary']['total_eps_all_modules']:,.0f}")
        
        with col2:
            if st.button("📄 Export Results", key="export_eps"):
                # Create export data
                export_data = {
                    'timestamp': datetime.now().isoformat(),
                    'node': selected_node,
                    'time_period': time_period,
                    'results': eps_data
                }
                
                st.download_button(
                    label="💾 Download EPS Report (JSON)",
                    data=yaml.dump(export_data, default_flow_style=False),
                    file_name=f"eps_report_{selected_node}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
                    mime="application/x-yaml"
                )
    
    else:
        st.info("👆 Select modules and click 'Calculate EPS' to see results")

if __name__ == "__main__":
    render_cluster_sync_page()
