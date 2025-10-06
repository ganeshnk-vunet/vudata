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
    
    # Sync status
    if 'sync_status' in st.session_state:
        render_sync_status()

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
                    new_period = st.number_input(
                        "Period (seconds)", 
                        value=float(period) if period else 1.0,
                        min_value=0.1
                    )
                
                # Calculate EPS
                if new_period > 0:
                    eps = new_num_uniq_key / new_period
                    st.metric("Estimated EPS", f"{eps:.2f}")
                    
                    # Show impact of changes
                    if num_uniq_key and period:
                        old_eps = num_uniq_key / period
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "⚙️ Node Management", 
        "🔄 Config Sync", 
        "📁 Config Browser"
    ])
    
    with tab1:
        render_cluster_overview()
    
    with tab2:
        render_node_management()
    
    with tab3:
        render_config_sync()
    
    with tab4:
        render_config_browser()

if __name__ == "__main__":
    render_cluster_sync_page()
