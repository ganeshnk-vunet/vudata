"""
Main Streamlit UI for vuDataSim Web Interface
"""
import streamlit as st
import logging
import sys
import os
from pathlib import Path
import pandas as pd
import time

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import (
    PRIMARY_BINARY, SUPPORTED_BINARIES, DEFAULT_TIMEOUT,
    STREAMLIT_PORT, STREAMLIT_ADDRESS, LOG_FILE, LOGS_DIR,
    REMOTE_HOST, REMOTE_USER, REMOTE_TIMEOUT
)
from core.binary_manager import process_manager
from core.yaml_editor import yaml_editor
from core.eps_calculator import eps_calculator
from core.diff_viewer import diff_viewer
from core.clickhouse_monitor import ClickHouseMonitor
clickhouse_monitor = ClickHouseMonitor(
    host="10.32.3.50",
    port=9000,
    database="monitoring",
    user="vuDataSim_tool",
    password="StrongPassword123"
)


# Configure logging
logger = logging.getLogger(__name__)

# Ensure required directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Update LOG_FILE path now that directory exists
import core.config as config
config.LOG_FILE = LOGS_DIR / "vudatasim-webui.log"

# Add file handler for logging if LOG_FILE is available
if config.LOG_FILE and not any(isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers):
    try:
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")

# Page configuration
st.set_page_config(
    page_title="vuDataSim Web UI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for new grouped design
st.markdown("""
<style>
    /* Main header with gradient */
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #4F46E5;
        text-align: center;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #4F46E5, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sidebar header styling */
    .sidebar-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #4F46E5;
        margin-bottom: 1rem;
        text-align: center;
        padding: 0.5rem;
        background: linear-gradient(135deg, #F3F4F6, #E5E7EB);
        border-radius: 0.5rem;
        border-left: 4px solid #4F46E5;
    }
    
    /* Enhanced metric cards */
    .metric-card {
        background: linear-gradient(135deg, #F8FAFC, #F1F5F9);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #4F46E5;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(79, 70, 229, 0.15);
        border-left-color: #10B981;
    }
    
    /* Status indicators with new color scheme */
    .status-running {
        color: #10B981;
        font-weight: bold;
        font-size: 1.1em;
    }
    .status-stopped {
        color: #EF4444;
        font-weight: bold;
        font-size: 1.1em;
    }
    .status-error {
        color: #FACC15;
        font-weight: bold;
        font-size: 1.1em;
    }
    .diff-added { color: #28a745; font-weight: bold; }
    .diff-removed { color: #dc3545; font-weight: bold; }
    .diff-context { color: #6c757d; }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 0.5rem;
    }
    .module-card {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
    }
    .module-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 0.5rem 1rem rgba(31, 119, 180, 0.15);
        transform: translateY(-1px);
    }
    .submodule-item {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .tuning-controls {
        background: linear-gradient(135deg, #e8f4f8, #f0f8ff);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .auto-tuner-result {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeaa7;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .diff-viewer {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        max-height: 400px;
        overflow-y: auto;
    }
    .success-message {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 1px solid #c3e6cb;
        color: #155724;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-message {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeaa7;
        color: #856404;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-message {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border: 1px solid #f5c6cb;
        color: #721c24;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application"""

    # Enhanced Grouped Navigation
    st.sidebar.markdown('<p class="sidebar-header">⚡ vuDataSim Web Interface</p>', unsafe_allow_html=True)
    
    # Main navigation sections
    section = st.sidebar.selectbox(
        "🧭 Main Sections",
        ["🏠 Overview", "🧩 Configuration", "🖥️ Cluster Operations", "🧩 System", "🔮 Future"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # Sub-navigation based on selected section
    if section == "🏠 Overview":
        page = st.sidebar.selectbox(
            "Overview Pages",
            ["Dashboard", "Live Metrics", "Audit & Logs"],
            index=0
        )
    elif section == "🧩 Configuration":
        page = st.sidebar.selectbox(
            "Configuration Pages", 
            ["Module Browser", "Submodule Editor", "EPS Tools", "Diff & Versioning"],
            index=0
        )
    elif section == "🖥️ Cluster Operations":
        page = st.sidebar.selectbox(
            "Cluster Operations",
            ["Cluster Manager", "Binary Control"],
            index=0
        )  
    elif section == "🧩 System":
        page = st.sidebar.selectbox(
            "System Pages",
            ["System Status", "Settings", "Audit Trail"],
            index=0
        )
    elif section == "🔮 Future":
        page = st.sidebar.selectbox(
            "Future Features",
            ["Real-time Analytics", "Alerts & Thresholds", "Template Library", "Config Testing", "Dark Mode"],
            index=0
        )
    
    # Add breadcrumb navigation
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Path:** {section} → {page}")
    
    # Quick actions sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Quick Actions")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄", help="Refresh Data"):
            st.rerun()
    with col2:
        if st.button("⚙️", help="Global Settings"):
            st.session_state.show_global_settings = True

    st.sidebar.markdown("---")

    # Header
    st.markdown('<h1 class="main-header">⚡ vuDataSim Web Interface</h1>', unsafe_allow_html=True)

    # Route to appropriate page based on new structure
    if page == "Dashboard":
        show_dashboard()
    elif page == "Live Metrics":
        show_live_metrics()  # Enhanced Live EPS Monitor
    elif page == "Audit & Logs":
        show_audit_and_logs()  # Combined Logs & Audit
    elif page == "Module Browser":
        show_module_browser()
    elif page == "Submodule Editor":
        show_submodule_editor()
    elif page == "EPS Tools":
        show_eps_tools()  # Unified EPS workspace
    elif page == "Diff & Versioning":
        show_diff_and_versioning()  # Combined Diff & Backup
    elif page == "Cluster Manager":
        show_cluster_manager()
    elif page == "Binary Control":
        show_binary_control_hub()  # Combined local/remote
    elif page == "System Status":
        show_system_status()
    elif page == "Settings":
        show_global_settings()
    elif page == "Audit Trail":
        show_audit_trail()
    elif page == "Real-time Analytics":
        show_realtime_analytics()
    elif page == "Alerts & Thresholds":
        show_alerts_thresholds()
    elif page == "Template Library":
        show_template_library()
    elif page == "Config Testing":
        show_config_testing()
    elif page == "Dark Mode":
        show_dark_mode_settings()
    else:
        st.info(f"Select a page from the sidebar. Current: {page}")


def show_dashboard():
    """Main dashboard showing overview"""
    st.header("📊 Dashboard")

    # Binary status section
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Binary Status")
        try:
            status = process_manager.get_status(PRIMARY_BINARY)
        except Exception as e:
            st.error(f"Error fetching binary status: {e}")
            status = {"status": "unknown"}

        if status.get("status") == "running":
            st.markdown(f'<p class="status-running">● Running (PID: {status.get("pid", "N/A")})</p>',
                       unsafe_allow_html=True)
            st.write(f"**Start Time:** {status.get('start_time', 'N/A')}")
            st.write(f"**Elapsed:** {status.get('elapsed_seconds', 0):.1f} seconds")
        elif status.get("status") == "exited":
            st.markdown(f'<p class="status-stopped">● Exited (Code: {status.get("exit_code", "N/A")})</p>',
                       unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-stopped">● Not Running</p>', unsafe_allow_html=True)

        if status.get("log_file"):
            st.write(f"**Log File:** `{status['log_file']}`")

    with col2:
        st.subheader("📈 EPS Overview")
        try:
            all_eps = eps_calculator.calculate_eps_for_all_modules()
            total_eps = sum(module.get("eps", 0) for module in all_eps.values())

            st.metric("Total EPS", f"{total_eps:.1f}")

            # Show top modules by EPS
            module_eps = [(name, data.get("eps", 0)) for name, data in all_eps.items()]
            module_eps.sort(key=lambda x: x[1], reverse=True)

            for module_name, eps in module_eps[:5]:  # Top 5
                st.write(f"**{module_name}:** {eps:.1f} EPS")

        except Exception as e:
            st.error(f"Error calculating EPS: {e}")

    # Recent activity section
    st.subheader("📋 Recent Activity")
    try:
        # Show recent log entries
        if LOG_FILE and Path(LOG_FILE).exists():
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:]  # Last 10 lines

            for line in reversed(recent_lines):
                st.text(line.strip())
        else:
            st.info("No activity logs available yet.")
    except Exception as e:
        st.error(f"Error reading logs: {e}")


def show_binary_control():
    """Binary control interface"""
    st.header("🎮 Binary Control")

    # Binary selection
    try:
        available_binaries = process_manager.list_binaries()
    except Exception as e:
        st.error(f"Error listing binaries: {e}")
        return

    if not available_binaries:
        st.warning("No local binaries found in bin/ directory")
        st.info(f"💡 **Tip**: Use the **Remote Binary Control** page from the sidebar to control binaries on the remote VM ({REMOTE_HOST})")
        return

    default_index = 0
    if PRIMARY_BINARY in available_binaries:
        default_index = available_binaries.index(PRIMARY_BINARY)

    binary_name = st.selectbox(
        "Select Binary",
        available_binaries,
        index=default_index
    )

    # Current status
    status = process_manager.get_status(binary_name)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh Status"):
            st.rerun()

    with col2:
        if status.get("status") == "running":
            if st.button("⏹️ Stop"):
                with st.spinner("Stopping binary..."):
                    result = process_manager.stop_binary(binary_name)
                    if result.get("success"):
                        st.success(result.get("message", "Stopped"))
                        st.rerun()
                    else:
                        st.error(result.get("message", "Failed to stop"))
        else:
            st.button("⏹️ Stop", disabled=True)

    with col3:
        if status.get("status") != "running":
            timeout = st.number_input("Timeout (seconds)", min_value=0, value=int(DEFAULT_TIMEOUT), step=10)
            if st.button("▶️ Start"):
                with st.spinner("Starting binary..."):
                    result = process_manager.start_binary(binary_name, timeout)
                    if result.get("success"):
                        st.success(result.get("message", "Started"))
                        st.rerun()
                    else:
                        st.error(result.get("message", "Failed to start"))
        else:
            st.button("▶️ Start", disabled=True)

    with col4:
        if status.get("status") == "running":
            if st.button("🔄 Restart"):
                with st.spinner("Restarting binary..."):
                    stop_result = process_manager.stop_binary(binary_name)
                    if stop_result.get("success"):
                        start_result = process_manager.start_binary(binary_name, int(DEFAULT_TIMEOUT))
                        if start_result.get("success"):
                            st.success("Binary restarted successfully")
                            st.rerun()
                        else:
                            st.error(f"Failed to restart: {start_result.get('message')}")
                    else:
                        st.error(f"Failed to stop for restart: {stop_result.get('message')}")
        else:
            st.button("🔄 Restart", disabled=True)

    # Status details
    st.subheader("📊 Current Status")
    if status.get("status") == "running":
        st.markdown(f'<p class="status-running">● Running</p>', unsafe_allow_html=True)
        st.json({
            "PID": status.get("pid"),
            "Run ID": status.get("run_id"),
            "Start Time": status.get("start_time"),
            "Elapsed": f"{status.get('elapsed_seconds', 0):.1f}s",
            "Log File": status.get("log_file")
        })
    elif status.get("status") == "exited":
        st.markdown(f'<p class="status-stopped">● Exited</p>', unsafe_allow_html=True)
        st.json({
            "Exit Code": status.get("exit_code"),
            "Run ID": status.get("run_id"),
            "Elapsed": f"{status.get('elapsed_seconds', 0):.1f}s",
            "Log File": status.get("log_file")
        })
    else:
        st.info("Binary is not currently running")


def show_remote_binary_control():
    """Remote binary control interface"""
    st.header("🌐 Remote Binary Control")

    st.info(f"📡 Connected to remote host: {REMOTE_HOST}")

    # Remote binary selection
    try:
        available_remote_binaries = process_manager.list_remote_binaries()
    except Exception as e:
        st.error(f"Error connecting to remote host: {e}")
        st.error("Please check SSH configuration and network connectivity")
        return

    if not available_remote_binaries:
        st.error("No binaries found in remote bin/ directory")
        return

    # Add remote prefix to distinguish from local binaries
    remote_options = [f"🔗 {binary}" for binary in available_remote_binaries]

    binary_name = st.selectbox(
        "Select Remote Binary",
        remote_options
    )

    # Remove the emoji prefix for actual binary name
    actual_binary_name = binary_name.replace("🔗 ", "")

    # Current status with error handling
    try:
        status = process_manager.get_remote_status(actual_binary_name)
    except Exception as e:
        st.error(f"Error getting remote status: {e}")
        status = {"status": "error", "message": str(e)}

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False, help="Automatically refresh status every 3 seconds")
        if st.button("🔄 Refresh Status") or auto_refresh:
            if auto_refresh:
                time.sleep(3)
            st.rerun()

    with col2:
        if status.get("status") == "running":
            if st.button("⏹️ Stop"):
                with st.spinner("Stopping remote binary..."):
                    result = process_manager.stop_remote_binary(actual_binary_name)
                    if result.get("success"):
                        st.success(result.get("message", "Stopped"))
                        st.rerun()
                    else:
                        st.error(result.get("message", "Failed to stop"))
        else:
            st.button("⏹️ Stop", disabled=True)

    with col3:
        if status.get("status") != "running":
            timeout = st.number_input("Timeout (seconds)", min_value=0, value=int(REMOTE_TIMEOUT), step=10)
            if st.button("▶️ Start"):
                with st.spinner("Starting remote binary..."):
                    result = process_manager.start_remote_binary(actual_binary_name, timeout)
                    if result.get("success"):
                        st.success(f"✅ {result.get('message', 'Started')} (PID: {result.get('pid', 'unknown')})")
                        # Give the UI a moment to process the success message
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('message', 'Failed to start')}")
                        if result.get("error"):
                            st.error(f"Details: {result.get('error')}")
        else:
            st.button("▶️ Start", disabled=True)

    with col4:
        if status.get("status") == "running":
            if st.button("📋 View Logs"):
                st.session_state.show_remote_logs = True
                st.rerun()
        else:
            st.button("📋 View Logs", disabled=True)

    # Status details
    st.subheader("📊 Current Status")
    if status.get("status") == "running":
        st.markdown(f'<p class="status-running">● Running (Remote)</p>', unsafe_allow_html=True)
        st.json({
            "PID": status.get("pid"),
            "Run ID": status.get("run_id"),
            "Start Time": status.get("start_time"),
            "Elapsed": f"{status.get('elapsed_seconds', 0):.1f}s",
            "Remote Log File": status.get("remote_log_file"),
            "Host": REMOTE_HOST
        })
    elif status.get("status") == "exited":
        st.markdown(f'<p class="status-stopped">● Exited (Remote)</p>', unsafe_allow_html=True)
        st.json({
            "Run ID": status.get("run_id"),
            "Start Time": status.get("start_time"),
            "Elapsed": f"{status.get('elapsed_seconds', 0):.1f}s",
            "Remote Log File": status.get("remote_log_file"),
            "Host": REMOTE_HOST
        })
    elif status.get("status") == "timeout":
        st.markdown(f'<p class="status-error">● Timeout (Remote)</p>', unsafe_allow_html=True)
        st.json({
            "PID": status.get("pid"),
            "Run ID": status.get("run_id"),
            "Start Time": status.get("start_time"),
            "Elapsed": f"{status.get('elapsed_seconds', 0):.1f}s",
            "Timeout": f"{status.get('timeout', 0)}s",
            "Host": REMOTE_HOST
        })
    else:
        st.info("Remote binary is not currently running")

    # Show remote logs if requested
    if st.session_state.get("show_remote_logs", False):
        st.subheader("📜 Remote Binary Logs")
        try:
            logs = process_manager.get_remote_logs(actual_binary_name)
            if logs:
                st.code(logs, language="log")
            else:
                st.info("No logs available")
        except Exception as e:
            st.error(f"Error retrieving logs: {e}")

        if st.button("🔙 Back to Control"):
            st.session_state.show_remote_logs = False
            st.rerun()


def show_cluster_manager():
    """Show the cluster management interface"""
    from ui.cluster_ui import (
        render_cluster_overview,
        render_node_management, 
        render_config_sync,
        render_config_browser,
        render_bulk_submodule_editor,
        render_eps_calculator
    )
    
    st.header("🌐 Cluster Configuration Manager")
    st.markdown("Centralized management for vuDataSim configurations across multiple nodes")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "⚙️ Node Management", 
        "🔄 Config Sync", 
        "📁 Config Browser",
        "🔧 Bulk Editor",
        "📈 EPS Calculator"
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
    
    with tab6:
        render_eps_calculator()


def show_module_browser():
    """Module browser interface"""
    st.header("📁 Module Browser")

    try:
        # Read main config to get module status
        main_config, checksum = yaml_editor.read_main_config()

        if "include_module_dirs" not in main_config:
            st.error("No include_module_dirs section found in main config")
            return

        modules = main_config["include_module_dirs"]

        # Filter options
        col1, col2 = st.columns([2, 1])

        with col2:
            show_only_enabled = st.checkbox("Show only enabled modules", value=False)

        # Display modules
        st.subheader("📋 Available Modules")

        for module_name, module_config in modules.items():
            is_enabled = module_config.get("enabled", False)

            if show_only_enabled and not is_enabled:
                continue

            with st.expander(f"{'✅' if is_enabled else '❌'} {module_name} ({'Enabled' if is_enabled else 'Disabled'})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Status:** {'Enabled' if is_enabled else 'Disabled'}")

                    # Quick toggle
                    new_status = st.checkbox(
                        "Enable/Disable",
                        value=is_enabled,
                        key=f"toggle_{module_name}"
                    )

                    if new_status != is_enabled:
                        if st.button("💾 Save Toggle", key=f"save_toggle_{module_name}"):
                            try:
                                result = yaml_editor.toggle_module_enabled(module_name, new_status, checksum)
                                if result.get("success"):
                                    st.success(f"Module {module_name} {'enabled' if new_status else 'disabled'}")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to toggle module: {result.get('error')}")
                            except Exception as e:
                                st.error(f"Error toggling module: {e}")

                with col2:
                    # Show EPS info if available
                    try:
                        eps_data = eps_calculator.calculate_eps(module_name)
                        st.metric("Current EPS", f"{eps_data.get('eps', 0):.1f}")
                    except Exception as e:
                        st.write(f"EPS: Error calculating ({e})")

    except Exception as e:
        st.error(f"Error reading module configuration: {e}")


def show_eps_tuner():
    """EPS tuning interface"""
    st.header("🎯 EPS Tuner")

    # Module selection
    modules = eps_calculator.get_module_list()
    if not modules:
        st.error("No modules found")
        return

    selected_module = st.selectbox("Select Module", modules)

    if selected_module:
        # Get current configuration
        eps_data = eps_calculator.calculate_eps(selected_module)
        module_config = eps_calculator.get_module_config(selected_module)

        # Current EPS display
        st.subheader(f"📊 Current Configuration - {selected_module}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Current EPS", f"{eps_data.get('eps', 0):.1f}")

        with col2:
            st.metric("Module Unique Keys", eps_data.get('module_uniquekey', 0))

        with col3:
            st.metric("Period", eps_data.get('module_period', 'N/A'))

        # Manual tuning section
        st.subheader("🔧 Manual Tuning")

        with st.form("manual_tuning"):
            col1, col2 = st.columns(2)

            with col1:
                new_uniquekey = st.number_input(
                    "Module Unique Keys",
                    min_value=1,
                    max_value=1000000000,
                    value=int(eps_data.get('module_uniquekey', 1)),
                    step=100
                )

            with col2:
                new_period = st.text_input(
                    "Period",
                    value=str(eps_data.get('module_period', '1s')),
                    help="Format: 1s, 250ms, 1m, 2h"
                )

            if st.form_submit_button("🔄 Calculate EPS"):
                try:
                    # Calculate new EPS
                    new_eps_data = eps_calculator.calculate_eps(
                        selected_module,
                        module_uniquekey=new_uniquekey,
                        module_period=new_period
                    )

                    st.success(f"New EPS: {new_eps_data.get('eps', 0):.1f}")

                    # Show detailed calculation
                    with st.expander("📋 Calculation Details"):
                        st.json(new_eps_data.get('calculation', {}))

                except Exception as e:
                    st.error(f"Error calculating EPS: {e}")

        # Auto-tuner section
        st.subheader("🎯 Auto-Tuner")

        target_eps = st.number_input(
            "Target EPS",
            min_value=0.0,
            value=float(eps_data.get('eps', 0.0)),
            step=100.0
        )

        if st.button("🔮 Suggest Configuration"):
            try:
                suggestion = eps_calculator.suggest_uniquekey_for_target_eps(
                    selected_module,
                    target_eps
                )

                if suggestion.get("error"):
                    st.error(suggestion["error"])
                else:
                    st.success(f"Suggested Module Unique Keys: {suggestion.get('suggested_module_uniquekey'):,}")
                    st.info(f"Expected EPS: {suggestion.get('expected_eps', 0):.1f}")

                    with st.expander("📊 Detailed Suggestion"):
                        st.json(suggestion)

            except Exception as e:
                st.error(f"Error generating suggestion: {e}")


def show_config_editor():
    """Enhanced configuration editor interface"""
    st.header("⚙️ Configuration Editor")

    # Module selection for editing
    modules = eps_calculator.get_module_list()

    if not modules:
        st.info("No modules found for editing")
        return

    selected_module = st.selectbox("Select Module to Edit", modules, key="config_editor_module")

    if selected_module:
        try:
            # Get current config
            config, checksum = yaml_editor.read_module_config(selected_module)

            st.subheader(f"📝 Edit Configuration - {selected_module}")

            # Show current uniquekey and period
            current_uniquekey = config.get("uniquekey", {}).get("NumUniqKey", 1)
            current_period = config.get("period", "1s")

            # Live preview of changes
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### Current Configuration")
                st.json({
                    "NumUniqKey": current_uniquekey,
                    "Period": current_period
                })

            with col2:
                # Calculate current EPS
                current_eps = eps_calculator.calculate_eps(selected_module).get("eps", 0.0)
                st.metric("Current EPS", f"{current_eps:.1f}")

            st.markdown("---")
            st.markdown("#### Make Changes")

            # Input controls with live preview
            new_uniquekey = st.number_input(
                "NumUniqKey",
                min_value=1,
                max_value=1000000000,
                value=int(current_uniquekey),
                step=100,
                help="Number of unique keys to generate"
            )

            new_period = st.text_input(
                "Period",
                value=current_period,
                help="Format: 1s, 250ms, 1m, 2h"
            )

            # Live preview
            if new_uniquekey != current_uniquekey or new_period != current_period:
                try:
                    preview_eps = eps_calculator.calculate_eps(
                        selected_module,
                        module_uniquekey=new_uniquekey,
                        module_period=new_period
                    )
                    st.success(f"Preview EPS: {preview_eps.get('eps', 0):.1f}")

                    # Show diff preview
                    if st.checkbox("Show YAML Changes Preview"):
                        diff_result = diff_viewer.preview_module_changes(
                            selected_module, new_uniquekey, new_period
                        )

                        if diff_result.get("diffs") and "error" not in diff_result["diffs"]:
                            st.markdown("##### YAML Changes Preview")
                            st.code(diff_result["diffs"].get("clean_diff", ""), language="diff")
                        else:
                            st.warning("Could not generate diff preview")

                except Exception as e:
                    st.warning(f"Could not calculate preview: {e}")

            # Save changes
            if st.button("💾 Save Changes", type="primary"):
                try:
                    changes_made = False

                    # Update uniquekey if changed
                    if new_uniquekey != current_uniquekey:
                        result = yaml_editor.update_module_uniquekey(
                            selected_module, new_uniquekey, checksum
                        )
                        if result.get("success"):
                            st.success("✅ NumUniqKey updated successfully")
                            checksum = result.get("new_checksum", checksum)
                            changes_made = True
                        else:
                            st.error(f"❌ Failed to update NumUniqKey: {result.get('error')}")

                    # Update period if changed
                    if new_period != current_period:
                        result = yaml_editor.update_module_period(
                            selected_module, new_period, checksum
                        )
                        if result.get("success"):
                            st.success("✅ Period updated successfully")
                            changes_made = True
                        else:
                            st.error(f"❌ Failed to update period: {result.get('error')}")

                    if changes_made:
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error saving configuration: {e}")

        except Exception as e:
            st.error(f"❌ Error reading module configuration: {e}")


def show_submodule_editor():
    """Submodule editor interface"""
    st.header("🔧 Submodule Editor")

    # Module selection
    modules = eps_calculator.get_module_list()
    if not modules:
        st.info("No modules found")
        return

    selected_module = st.selectbox("Select Module", modules, key="submodule_module")

    if selected_module:
        # Get submodules
        submodules = eps_calculator.get_submodules(selected_module)

        if not submodules:
            st.info(f"No submodules found for module: {selected_module}")
            return

        st.subheader(f"📋 Submodules - {selected_module}")

        # Display submodules with editing capabilities
        for submodule_name in submodules:
            with st.expander(f"🔧 {submodule_name}"):
                try:
                    # Get current config
                    config, checksum = yaml_editor.read_submodule_config(selected_module, submodule_name)
                    current_uniquekey = config.get("uniquekey", {}).get("NumUniqKey", 1)

                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.write(f"**Current NumUniqKey:** {current_uniquekey:,}")

                    with col2:
                        new_uniquekey = st.number_input(
                            "New Value",
                            min_value=1,
                            max_value=1000000000,
                            value=int(current_uniquekey),
                            key=f"submodule_{selected_module}_{submodule_name}"
                        )

                    with col3:
                        if st.button("💾 Save", key=f"save_submodule_{selected_module}_{submodule_name}"):
                            if new_uniquekey != current_uniquekey:
                                try:
                                    result = yaml_editor.update_submodule_uniquekey(
                                        selected_module, submodule_name, new_uniquekey, checksum
                                    )
                                    if result.get("success"):
                                        st.success(f"✅ {submodule_name} updated successfully")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to update {submodule_name}")
                                except Exception as e:
                                    st.error(f"❌ Error updating {submodule_name}: {e}")
                            else:
                                st.info("No changes to save")

                except Exception as e:
                    st.error(f"❌ Error reading {submodule_name}: {e}")


def show_auto_tuner():
    """Auto-tuner interface"""
    st.header("🎯 Auto-Tuner")

    # Module selection
    modules = eps_calculator.get_module_list()
    if not modules:
        st.info("No modules found")
        return

    selected_module = st.selectbox("Select Module for Auto-Tuning", modules, key="auto_tuner_module")

    if selected_module:
        st.subheader(f"🎯 Auto-Tune - {selected_module}")

        # Get current configuration
        current_eps_data = eps_calculator.calculate_eps(selected_module)
        current_eps = current_eps_data.get("eps", 0.0)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Current Configuration")
            st.info(f"Current EPS: {current_eps:.1f}")

            st.markdown("**Module Settings:**")
            st.write(f"• Unique Keys: {current_eps_data.get('module_uniquekey', 0):,}")
            st.write(f"• Period: {current_eps_data.get('module_period', 'N/A')}")

        with col2:
            st.markdown("#### Target Configuration")
            target_eps = st.number_input(
                "Target EPS",
                min_value=0.0,
                value=float(current_eps),
                step=100.0,
                help="Desired Events Per Second"
            )

            tolerance = st.slider(
                "Tolerance (%)",
                min_value=1,
                max_value=20,
                value=5,
                help="Acceptable percentage deviation from target"
            ) / 100.0

        if st.button("🔮 Generate Suggestion"):
            try:
                with st.spinner("Calculating optimal configuration..."):
                    suggestion = eps_calculator.suggest_uniquekey_for_target_eps(
                        selected_module, target_eps, tolerance=tolerance
                    )

                if suggestion.get("error"):
                    st.error(f"❌ {suggestion['error']}")
                else:
                    st.markdown("#### 🎉 Auto-Tune Results")

                    achievement_pct = (abs(suggestion.get('expected_eps', 0.0) - target_eps) / target_eps * 100) if target_eps else 0.0
                    achievement_text = 'within' if suggestion.get('within_tolerance') else 'outside'

                    st.markdown(f"""
                    <div class="auto-tuner-result">
                    <h4>✅ Optimal Configuration Found!</h4>
                    <p><strong>Suggested Module Unique Keys:</strong> {suggestion.get('suggested_module_uniquekey'):,}</p>
                    <p><strong>Expected EPS:</strong> {suggestion.get('expected_eps', 0):.1f}</p>
                    <p><strong>Achievement:</strong> {achievement_pct:.2f}% {achievement_text} tolerance</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Detailed breakdown
                    with st.expander("📊 Detailed Calculation"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Current vs Suggested:**")
                            current_keys = suggestion.get('current_module_uniquekey', 0)
                            suggested_keys = suggestion.get('suggested_module_uniquekey', 0)
                            st.write(f"Current: {current_keys:,}")
                            st.write(f"Suggested: {suggested_keys:,}")
                            st.write(f"Change: {suggested_keys - current_keys:,}")

                        with col2:
                            st.write("**EPS Comparison:**")
                            st.write(f"Current: {eps_calculator.calculate_eps(selected_module).get('eps', 0):.1f}")
                            st.write(f"Target: {target_eps:.1f}")
                            st.write(f"Expected: {suggestion.get('expected_eps', 0):.1f}")

                        st.write("**Submodule Contributions:**")
                        for submodule_name, config in suggestion.get('submodule_configs', {}).items():
                            st.write(f"• {submodule_name}: {config.get('current_uniquekey', 0)} keys")

                    # Apply suggestion
                    if st.button("✅ Apply Suggestion"):
                        try:
                            _, checksum = yaml_editor.read_module_config(selected_module)

                            result = yaml_editor.update_module_uniquekey(
                                selected_module,
                                suggestion.get('suggested_module_uniquekey'),
                                checksum
                            )

                            if result.get("success"):
                                st.success("🎉 Configuration updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to apply changes: {result.get('error')}")

                        except Exception as e:
                            st.error(f"❌ Error applying configuration: {e}")

            except Exception as e:
                st.error(f"❌ Error generating auto-tune suggestion: {e}")


def show_diff_preview():
    """Diff preview interface"""
    st.header("🔍 Diff Preview")

    # Module selection
    modules = eps_calculator.get_module_list()
    if not modules:
        st.info("No modules found")
        return

    selected_module = st.selectbox("Select Module", modules, key="diff_module")

    if selected_module:
        st.subheader(f"🔍 Preview Changes - {selected_module}")

        # Get current config
        try:
            config, checksum = yaml_editor.read_module_config(selected_module)
            current_uniquekey = config.get("uniquekey", {}).get("NumUniqKey", 1)
            current_period = config.get("period", "1s")

            st.markdown("#### Current Configuration")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**NumUniqKey:** {current_uniquekey:,}")
            with col2:
                st.write(f"**Period:** {current_period}")

            st.markdown("---")
            st.markdown("#### Proposed Changes")

            # Input new values
            col1, col2 = st.columns(2)

            with col1:
                new_uniquekey = st.number_input(
                    "New NumUniqKey",
                    min_value=1,
                    max_value=1000000000,
                    value=int(current_uniquekey),
                    step=100,
                    key="diff_uniquekey"
                )

            with col2:
                new_period = st.text_input(
                    "New Period",
                    value=current_period,
                    key="diff_period"
                )

            if new_uniquekey != current_uniquekey or new_period != current_period:
                # Generate diff preview
                diff_result = diff_viewer.preview_module_changes(
                    selected_module, new_uniquekey, new_period
                )

                if diff_result.get("diffs") and "error" not in diff_result["diffs"]:
                    st.markdown("##### 📋 YAML Changes Preview")

                    # Show clean diff
                    st.markdown("**Changes Summary:**")
                    st.info(diff_result["diffs"].get("summary", "No summary available"))

                    st.markdown("**Detailed Diff:**")
                    st.code(diff_result["diffs"].get("clean_diff", ""), language="diff")

                    # Apply changes option
                    if st.button("💾 Apply These Changes"):
                        try:
                            # Apply uniquekey change if modified
                            if new_uniquekey != current_uniquekey:
                                result = yaml_editor.update_module_uniquekey(
                                    selected_module, new_uniquekey, checksum
                                )
                                if result.get("success"):
                                    st.success("✅ NumUniqKey updated")
                                    checksum = result.get("new_checksum", checksum)
                                else:
                                    st.error(f"❌ Failed to update NumUniqKey: {result.get('error')}")

                            # Apply period change if modified
                            if new_period != current_period:
                                result = yaml_editor.update_module_period(
                                    selected_module, new_period, checksum
                                )
                                if result.get("success"):
                                    st.success("✅ Period updated")
                                else:
                                    st.error(f"❌ Failed to update period: {result.get('error')}")

                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error applying changes: {e}")
                else:
                    st.warning("Could not generate diff preview")
            else:
                st.info("Make changes above to see diff preview")

        except Exception as e:
            st.error(f"❌ Error reading module configuration: {e}")


def show_logs_and_audit():
    """Logs and audit trail interface"""
    st.header("📜 Logs & Audit Trail")

    # Log file selection
    log_tabs = st.tabs(["Application Logs", "Binary Logs", "Audit Trail"])

    with log_tabs[0]:
        st.subheader("📋 Application Logs")
        try:
            if LOG_FILE and Path(LOG_FILE).exists():
                with open(LOG_FILE, 'r') as f:
                    logs = f.readlines()

                if logs:
                    # Filter controls
                    log_levels = st.multiselect(
                        "Filter by Level",
                        ["INFO", "WARNING", "ERROR", "DEBUG"],
                        default=["INFO", "WARNING", "ERROR"]
                    )

                    # Display recent logs
                    filtered_logs = []
                    for log in reversed(logs[-100:]):  # Last 100 lines
                        if any(level in log for level in log_levels):
                            filtered_logs.append(log.strip())

                    if filtered_logs:
                        st.code('\n'.join(filtered_logs), language="log")
                    else:
                        st.info("No logs match the selected filters")
                else:
                    st.info("No application logs available")
            else:
                st.info("Log file not found")
        except Exception as e:
            st.error(f"Error reading logs: {e}")

    with log_tabs[1]:
        st.subheader("🔧 Binary Logs")
        try:
            binary_logs_dir = Path(__file__).resolve().parent.joinpath("..", "logs").resolve()
            if binary_logs_dir.exists():
                log_files = [f.name for f in binary_logs_dir.iterdir() if f.is_file() and f.name.startswith("ui-")]

                if log_files:
                    selected_log = st.selectbox("Select Log File", sorted(log_files, reverse=True))

                    if selected_log:
                        log_path = binary_logs_dir.joinpath(selected_log)
                        with open(log_path, 'r') as f:
                            content = f.read()

                        st.code(content, language="log")
                else:
                    st.info("No binary logs found")
            else:
                st.info("Binary logs directory not found")
        except Exception as e:
            st.error(f"Error reading binary logs: {e}")

    with log_tabs[2]:
        st.subheader("🔐 Audit Trail")
        st.info("Audit trail tracking all configuration changes and binary operations")
        st.write("**Features:**")
        st.write("• Track all YAML file modifications")
        st.write("• Record binary start/stop operations")
        st.write("• Log user actions and timestamps")
        st.write("• Maintain change history for rollback")


def show_backup_manager():
    """Backup manager interface"""
    st.header("💾 Backup Manager")

    backup_dir = Path("backups")

    if not backup_dir.exists():
        st.info("No backups directory found")
        return

    st.subheader("📋 Available Backups")

    try:
        backup_files = list(backup_dir.glob("*.bak.*"))

        if not backup_files:
            st.info("No backup files found")
            return

        # Group backups by original file
        backups_by_file = {}
        for backup in backup_files:
            # Parse filename: original_name.bak.timestamp
            parts = backup.name.split('.bak.')
            if len(parts) == 2:
                original_name = parts[0]
                timestamp = parts[1]

                backups_by_file.setdefault(original_name, []).append({
                    'path': backup,
                    'timestamp': timestamp,
                    'size': backup.stat().st_size
                })

        # Display backups
        for original_file, backups in backups_by_file.items():
            with st.expander(f"📁 {original_file} ({len(backups)} backups)"):
                for backup in sorted(backups, key=lambda x: x['timestamp'], reverse=True):
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"**Timestamp:** {backup['timestamp']}")

                    with col2:
                        st.write(f"**Size:** {backup['size']:,} bytes")

                    with col3:
                        if st.button("🔄 Restore", key=f"restore_{str(backup['path'])}"):
                            st.warning(f"Restore functionality would restore {original_file} from {backup['timestamp']}")

    except Exception as e:
        st.error(f"Error reading backups: {e}")


def show_system_status():
    """System status interface"""
    st.header("📊 System Status")

    # System metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Modules", len(eps_calculator.get_module_list()))

    with col2:
        # Calculate total EPS
        try:
            all_eps = eps_calculator.calculate_eps_for_all_modules()
            total_eps = sum(module.get("eps", 0) for module in all_eps.values())
            st.metric("Total EPS", f"{total_eps:.1f}")
        except Exception:
            st.metric("Total EPS", "N/A")

    with col3:
        # Available binaries
        binaries = process_manager.list_binaries()
        st.metric("Binaries", len(binaries))

    with col4:
        # Backup files
        backup_dir = Path("backups")
        backup_count = len(list(backup_dir.glob("*.bak.*"))) if backup_dir.exists() else 0
        st.metric("Backups", backup_count)

    # Detailed status
    st.subheader("🔍 Detailed Status")

    status_tabs = st.tabs(["Modules", "Binaries", "Configuration"])

    with status_tabs[0]:
        st.write("**Module Status:**")
        modules = eps_calculator.get_module_list()

        if modules:
            # Create summary table
            module_data = []
            for module in modules[:10]:  # Show first 10
                try:
                    eps_data = eps_calculator.calculate_eps(module)
                    module_data.append({
                        "Module": module,
                        "EPS": f"{eps_data.get('eps', 0):.1f}",
                        "Unique Keys": f"{eps_data.get('module_uniquekey', 'N/A'):,}" if isinstance(eps_data.get('module_uniquekey'), int) else eps_data.get('module_uniquekey', 'N/A'),
                        "Period": eps_data.get('module_period', 'N/A'),
                        "Submodules": len(eps_data.get('submodules', [])) if isinstance(eps_data.get('submodules'), (list, dict)) else eps_data.get('submodules', 'N/A')
                    })
                except Exception:
                    module_data.append({
                        "Module": module,
                        "EPS": "Error",
                        "Unique Keys": "N/A",
                        "Period": "N/A",
                        "Submodules": "N/A"
                    })

            if module_data:
                st.dataframe(module_data, use_container_width=True)

            if len(modules) > 10:
                st.info(f"Showing 10 of {len(modules)} modules")
        else:
            st.info("No modules found")

    with status_tabs[1]:
        st.write("**Binary Status:**")
        binaries = process_manager.list_binaries()

        if binaries:
            for binary in binaries:
                status = process_manager.get_status(binary)

                if status.get("status") == "running":
                    st.success(f"✅ {binary}: Running (PID {status.get('pid', 'N/A')})")
                elif status.get("status") == "exited":
                    st.error(f"❌ {binary}: Exited (Code {status.get('exit_code', 'N/A')})")
                else:
                    st.info(f"ℹ️ {binary}: Not managed")
        else:
            st.info("No binaries found")

    with status_tabs[2]:
        st.write("**Configuration Status:**")
        try:
            main_config, checksum = yaml_editor.read_main_config()
            enabled_count = sum(1 for m in main_config.get("include_module_dirs", {}).values()
                              if m.get("enabled", False))
            total_count = len(main_config.get("include_module_dirs", {}))

            st.success(f"✅ Main config: {total_count} modules, {enabled_count} enabled")

        except Exception as e:
            st.error(f"❌ Main config: Error reading ({e})")


def show_live_eps_monitor():
    """Live EPS monitoring interface"""
    st.header("📊 Live EPS Monitor")

    st.markdown("""
    Monitor real-time Events Per Second (EPS) from Kafka topics stored in ClickHouse.
    This shows the live ingestion rate for topics as data flows through the system.
    """)

    # Connection settings
    st.subheader("🔗 Connection Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        host = st.text_input("ClickHouse Host", value="164.52.213.158", help="IP address of the ClickHouse server")

    with col2:
        username = st.text_input("SSH Username", value=REMOTE_USER, help="SSH username for connection")

    with col3:
        # For simplicity, assume key-based auth, no password input for security
        st.info("Using SSH key authentication")

    # Topic selection
    st.subheader("🎯 Topic Selection")

    # Get available modules and their topics
    try:
        main_config, _ = yaml_editor.read_main_config()
        modules = main_config.get("include_module_dirs", {})

        # Extract enabled modules and their topics
        available_topics = []
        for module_name, module_config in modules.items():
            if module_config.get("enabled", False):
                try:
                    module_config_data, _ = yaml_editor.read_module_config(module_name)
                    topic = module_config_data.get("output", {}).get("kafka", {}).get("topic")
                    if topic:
                        available_topics.append((module_name, topic))
                except Exception:
                    continue

        if available_topics:
            topic_options = [f"{module} ({topic})" for module, topic in available_topics]
            selected_option = st.selectbox("Select Enabled Module Topic", topic_options)

            # Extract the topic from selection
            selected_topic = selected_option.split(" (")[-1].rstrip(")")
        else:
            st.warning("No enabled modules with Kafka topics found")
            selected_topic = st.text_input("Or enter topic manually", value="azure-redis-cache-input")

    except Exception as e:
        st.error(f"Error loading modules: {e}")
        selected_topic = st.text_input("Enter Kafka Topic", value="azure-redis-cache-input")

    # Monitoring controls
    st.subheader("📈 Monitoring Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Query Current EPS", type="primary"):
            with st.spinner("Connecting to ClickHouse..."):
                try:
                    # Connect and query
                    if clickhouse_monitor.connect():
                        success, eps_value, message = clickhouse_monitor.get_eps_for_topic(selected_topic)

                        if success:
                            st.success(f"✅ Current EPS for topic '{selected_topic}': **{eps_value:.2f}**")
                            st.metric("Live EPS", f"{eps_value:.2f}")
                        else:
                            st.error(f"❌ Failed to get EPS: {message}")
                    else:
                        st.error("❌ Failed to connect to ClickHouse server")

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                finally:
                    clickhouse_monitor.disconnect()

    with col2:
        if st.button("📊 Get Detailed Metrics"):
            with st.spinner("Fetching detailed metrics..."):
                try:
                    if clickhouse_monitor.connect():
                        success, metrics, message = clickhouse_monitor.get_topic_metrics(selected_topic)

                        if success:
                            st.success(f"✅ Detailed metrics for topic '{selected_topic}'")

                            # Display metrics in columns
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("1-Minute Rate", f"{metrics['one_minute_rate']:.2f}")
                                st.metric("5-Minute Rate", f"{metrics['five_minute_rate']:.2f}")

                            with col2:
                                st.metric("15-Minute Rate", f"{metrics['fifteen_minute_rate']:.2f}")
                                st.metric("Mean Rate", f"{metrics['mean_rate']:.2f}")

                            with col3:
                                st.metric("Total Count", f"{metrics['count']:,.0f}")
                                st.write(f"**Last Updated:** {metrics['timestamp']}")

                        else:
                            st.error(f"❌ Failed to get metrics: {message}")
                    else:
                        st.error("❌ Failed to connect to ClickHouse server")

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                finally:
                    clickhouse_monitor.disconnect()

    with col3:
        auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)

    # Auto-refresh functionality
    if auto_refresh:
        st.info("🔄 Auto-refresh enabled. Page will update every 30 seconds.")
        time.sleep(30)
        st.rerun()

    # Information section
    st.subheader("ℹ️ About EPS Monitoring")
    st.markdown("""
    **What is EPS?**
    - EPS (Events Per Second) represents the rate at which messages are being ingested into Kafka topics
    - Values are calculated over different time windows (1, 5, 15 minutes)
    - The 1-Minute Rate provides the most current view of ingestion speed

    **Data Source:**
    - Metrics are collected from ClickHouse `kafka_Broker_Topic_Metrics_data` table
    - Data is updated in real-time as Kafka brokers report metrics
    - Connection is made via SSH to the monitoring server

    **Usage Tips:**
    - Use "Query Current EPS" for instant readings
    - Use "Get Detailed Metrics" for comprehensive statistics
    - Enable auto-refresh for continuous monitoring during testing
    """)


# =============================================================================
# NEW UNIFIED PAGE FUNCTIONS
# =============================================================================

def show_live_metrics():
    """Enhanced Live EPS Monitor with ClickHouse integration"""
    st.header("📈 Live Metrics")
    st.markdown("Real-time EPS monitoring and performance metrics")
    
    # Create tabs for different metric views
    tab1, tab2, tab3 = st.tabs(["📊 EPS Dashboard", "📈 ClickHouse Metrics", "🔄 Auto-Refresh"])
    
    with tab1:
        # Reuse existing live EPS monitor functionality
        show_live_eps_monitor()
    
    with tab2:
        st.subheader("📊 ClickHouse Metrics")
        st.info("Real-time database metrics and performance indicators")
        # Add ClickHouse specific metrics here
        
    with tab3:
        st.subheader("🔄 Auto-Refresh Settings")
        auto_refresh = st.checkbox("Enable Auto-Refresh", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 10)
            st.info(f"Auto-refreshing every {refresh_interval} seconds")


def show_audit_and_logs():
    """Combined audit trail and logs with filtering"""
    st.header("📝 Audit & Logs")
    st.markdown("Unified view of system logs and configuration changes")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_type = st.selectbox(
            "Log Type",
            ["All", "🧠 Configuration", "⚙️ Binary", "🔄 Sync", "📈 EPS", "🔧 System"],
            index=0
        )
    
    with col2:
        time_range = st.selectbox(
            "Time Range", 
            ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            index=1
        )
    
    with col3:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Create tabs for different log views
    tab1, tab2 = st.tabs(["📋 Activity Timeline", "🔍 Search & Filter"])
    
    with tab1:
        st.subheader("📋 Recent Activity")
        # Timeline view of recent activities
        activities = [
            {"time": "2025-10-08 16:45:23", "type": "🧠 Config", "action": "Updated Mssql module unique keys", "user": "admin"},
            {"time": "2025-10-08 16:30:15", "type": "🔄 Sync", "action": "Synced configuration to e2e-108-10", "user": "admin"}, 
            {"time": "2025-10-08 16:15:08", "type": "📈 EPS", "action": "Calculated EPS for 3 modules", "user": "admin"},
            {"time": "2025-10-08 16:00:42", "type": "⚙️ Binary", "action": "Restarted vuDataSim process", "user": "admin"}
        ]
        
        for activity in activities:
            if log_type == "All" or activity["type"] in log_type:
                with st.container():
                    col1, col2, col3 = st.columns([2, 4, 1])
                    with col1:
                        st.text(activity["time"])
                    with col2:
                        st.markdown(f"{activity['type']} {activity['action']}")
                    with col3:
                        st.text(activity["user"])
                    st.markdown("---")
    
    with tab2:
        # Reuse existing logs functionality with search
        show_logs_and_audit()


def show_eps_tools():
    """Unified EPS workspace with calculator, tuner, and auto-tuner"""
    st.header("🧮 EPS Tools")
    st.markdown("Comprehensive EPS calculation, tuning, and optimization workspace")
    
    # Create tabs for the three EPS tools
    tab1, tab2, tab3 = st.tabs(["🧮 Calculator", "⚙️ Tuner", "🤖 Auto-Tuner"])
    
    with tab1:
        st.subheader("📊 EPS Calculator")
        # Import the cluster EPS calculator
        from ui.cluster_ui import render_eps_calculator
        render_eps_calculator()
    
    with tab2:
        st.subheader("⚙️ EPS Tuner")
        show_eps_tuner()
    
    with tab3:
        st.subheader("🤖 Auto-Tuner")
        show_auto_tuner()


def show_diff_and_versioning():
    """Combined diff preview and backup manager"""
    st.header("🧠 Diff & Versioning")
    st.markdown("Configuration comparison and backup management")
    
    # Create tabs for diff and backup functionality
    tab1, tab2 = st.tabs(["🔍 Diff Preview", "💾 Backup Manager"])
    
    with tab1:
        st.subheader("🔍 Configuration Diff")
        show_diff_preview()
    
    with tab2:
        st.subheader("💾 Backup Manager")
        show_backup_manager()


def show_binary_control_hub():
    """Combined local and remote binary control"""
    st.header("🧰 Binary Control Hub")
    st.markdown("Centralized binary process management for local and remote nodes")
    
    # Create tabs for local and remote control
    tab1, tab2 = st.tabs(["🔧 Local Control", "🌐 Remote Control"])
    
    with tab1:
        st.subheader("🔧 Local Binary Control")
        show_binary_control()
    
    with tab2:
        st.subheader("🌐 Remote Binary Control")  
        show_remote_binary_control()


def show_global_settings():
    """Global application settings"""
    st.header("🗂️ Global Settings")
    st.markdown("Application-wide configuration and preferences")
    
    # Settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["🌐 Connections", "📁 Paths", "🔔 Notifications", "🎨 Appearance"])
    
    with tab1:
        st.subheader("🌐 Connection Settings")
        st.text_input("Default SSH User", value="vunet")
        st.text_input("Default SSH Key Path", value="~/.ssh/id_rsa")
        st.number_input("Connection Timeout (seconds)", value=10, min_value=1, max_value=60)
        st.number_input("Max Retries", value=3, min_value=1, max_value=10)
    
    with tab2:
        st.subheader("📁 Default Paths")
        st.text_input("Configuration Directory", value="/home/vunet/vuDataSim/conf.d")
        st.text_input("Binary Directory", value="/home/vunet/vuDataSim/bin")
        st.text_input("Log Directory", value="./logs")
        st.text_input("Backup Directory", value="./backups")
    
    with tab3:
        st.subheader("🔔 Notification Settings")
        st.checkbox("Enable Email Notifications", value=False)
        st.checkbox("Enable Success Notifications", value=True)
        st.checkbox("Enable Error Alerts", value=True)
        st.number_input("Alert Threshold (EPS)", value=100000, min_value=0)
    
    with tab4:
        st.subheader("🎨 Appearance Settings")
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], index=0)
        st.checkbox("Compact Sidebar", value=False)
        st.checkbox("Show Breadcrumbs", value=True)
        st.selectbox("Page Layout", ["Wide", "Centered", "Compact"], index=0)
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")


def show_audit_trail(): 
    """Extended audit trail with search and filtering"""
    st.header("🧾 Audit Trail")
    st.markdown("Detailed audit log with advanced search and filtering")
    
    # Enhanced search and filtering
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Enter search term...")
    
    with col2:
        action_filter = st.selectbox("Action Type", ["All", "Create", "Update", "Delete", "Sync"])
    
    with col3:
        user_filter = st.selectbox("User", ["All", "admin", "operator", "viewer"])
    
    with col4:
        date_range = st.date_input("Date Range")
    
    # Detailed audit table
    st.subheader("📋 Audit Records")
    audit_data = [
        {"timestamp": "2025-10-08 16:45:23", "user": "admin", "action": "UPDATE", "resource": "Mssql/cpu_Stats", "details": "NumUniqKey: 3 → 2"},
        {"timestamp": "2025-10-08 16:30:15", "user": "admin", "action": "SYNC", "resource": "e2e-108-10", "details": "255 files synced"},
        {"timestamp": "2025-10-08 16:15:08", "user": "admin", "action": "CALCULATE", "resource": "EPS Tools", "details": "Calculated EPS for 3 modules"},
    ]
    
    st.dataframe(audit_data, use_container_width=True)


# Future Features (Placeholder implementations)
def show_realtime_analytics():
    """Real-time analytics dashboard"""
    st.header("📊 Real-time Analytics")
    st.info("🚧 Coming Soon: Advanced analytics and performance insights")
    st.markdown("**Planned Features:**")
    st.markdown("- Historical EPS trends")
    st.markdown("- Performance heatmaps")
    st.markdown("- Predictive analytics")
    st.markdown("- Custom dashboards")


def show_alerts_thresholds():
    """Alerts and threshold management"""
    st.header("🚨 Alerts & Thresholds")
    st.info("🚧 Coming Soon: Intelligent alerting system")
    st.markdown("**Planned Features:**")
    st.markdown("- EPS threshold alerts")
    st.markdown("- Node health monitoring")
    st.markdown("- Email/Slack notifications")
    st.markdown("- Custom alert rules")


def show_template_library():
    """Configuration template library"""
    st.header("🧱 Template Library")
    st.info("🚧 Coming Soon: Reusable configuration templates")
    st.markdown("**Planned Features:**")
    st.markdown("- Pre-built module templates")
    st.markdown("- Custom template creation")
    st.markdown("- Template versioning")
    st.markdown("- Community template sharing")


def show_config_testing():
    """Configuration testing and validation"""
    st.header("🧪 Config Testing")
    st.info("🚧 Coming Soon: Automated configuration testing")
    st.markdown("**Planned Features:**")
    st.markdown("- YAML syntax validation")
    st.markdown("- Logic consistency checks")
    st.markdown("- Performance impact simulation")
    st.markdown("- Automated test suites")


def show_dark_mode_settings():
    """Dark mode and theme settings"""
    st.header("🌓 Dark Mode")
    st.info("🚧 Coming Soon: Dark theme support")
    st.markdown("**Planned Features:**")
    st.markdown("- Dark/Light theme toggle")
    st.markdown("- Custom color schemes")
    st.markdown("- High contrast mode")
    st.markdown("- Theme scheduling")


if __name__ == "__main__":
    main()
