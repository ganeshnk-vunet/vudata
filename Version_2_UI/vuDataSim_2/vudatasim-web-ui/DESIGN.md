# vuDataSim Web Interface - Design Documentation

## 🏗️ Architecture Overview

The vuDataSim Web Interface is built using **Streamlit** with a modular architecture that separates UI components from core business logic. The application provides centralized management for vuDataSim configurations across multiple nodes.

### 📁 Project Structure
```
vudatasim-web-ui/
├── src/
│   ├── core/                    # Core business logic
│   │   ├── cluster_manager.py   # Multi-node cluster management
│   │   ├── binary_manager.py    # Process management
│   │   ├── yaml_editor.py       # Configuration file operations
│   │   ├── eps_calculator.py    # EPS calculations
│   │   ├── diff_viewer.py       # Configuration diff viewer
│   │   ├── clickhouse_monitor.py # Database monitoring
│   │   ├── audit_logger.py      # Audit trail logging
│   │   └── config.py           # Application configuration
│   └── ui/                     # User interface components
│       ├── app.py              # Main Streamlit application
│       └── cluster_ui.py       # Cluster management UI components
├── logs/                       # Application logs
├── conf_snapshots/             # Node configuration snapshots
├── backups/                    # Configuration backups
└── nodes.yaml                  # Cluster node definitions
```

---

## 🧭 Navigation Structure

### Main Navigation Menu
The application uses a **sidebar navigation** with the following pages:

```
⚡ vuDataSim Web Interface
├── 📊 Dashboard
├── 🔧 Binary Control
├── 🌐 Remote Binary Control
├── 🌐 Cluster Manager          ⭐ PRIMARY FEATURE
├── 📁 Module Browser
├── ✏️ Submodule Editor
├── ⚡ EPS Tuner
├── 🤖 Auto-Tuner
├── ⚙️ Configuration Editor
├── 🔍 Diff Preview
├── 📈 Live EPS Monitor
├── 📝 Logs & Audit
├── 💾 Backup Manager
└── 🔧 System Status
```

---

## 📄 Page Designs & Features

### 1. 📊 **Dashboard**
**Purpose:** Main overview and quick access to key metrics

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Dashboard                                                │
├─────────────────────┬───────────────────────────────────────┤
│ 🔧 Binary Status    │ 📈 Quick Stats                       │
│ • Status: Running   │ • Active Modules: 25                 │
│ • PID: 12345       │ • Total EPS: 250,000                 │
│ • Uptime: 2h 30m   │ • Last Update: 2m ago                │
│ [Start] [Stop]     │                                       │
├─────────────────────┴───────────────────────────────────────┤
│ 🔔 Recent Activity                                          │
│ • Config updated: Apache module                             │
│ • EPS tuned: Mssql (99,946 → 150,000)                     │
│ • Node synced: e2e-108-10                                  │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **Binary Status Card:** Real-time process monitoring
- **Quick Metrics:** Key performance indicators
- **Recent Activity Feed:** Last actions and changes
- **Quick Actions:** Start/Stop/Restart buttons

---

### 2. 🔧 **Binary Control**
**Purpose:** Local binary process management

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Binary Control                                           │
├─────────────────────────────────────────────────────────────┤
│ Binary Selection: [vuDataSim ▼]                            │
│ Status: 🟢 Running (PID: 12345)                            │
│                                                             │
│ [▶️ Start] [⏹️ Stop] [🔄 Restart] [📊 View Logs]          │
├─────────────────────────────────────────────────────────────┤
│ 📊 Process Information                                      │
│ • Command: ./vuDataSim                                      │
│ • Working Dir: /home/vunet/vuDataSim/bin                   │
│ • Started: 2025-10-08 14:30:25                            │
│ • CPU Usage: 15.2%                                         │
│ • Memory: 256 MB                                           │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **Process Control:** Start, stop, restart operations
- **Real-time Status:** Live process monitoring
- **Resource Usage:** CPU and memory metrics
- **Log Viewing:** Real-time log streaming

---

### 3. 🌐 **Remote Binary Control**
**Purpose:** Manage binaries on remote nodes

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ 🌐 Remote Binary Control                                    │
├─────────────────────────────────────────────────────────────┤
│ Node: [e2e-108-10 ▼]  SSH Status: 🟢 Connected            │
│                                                             │
│ Remote Binary Status: 🟢 Running                           │
│ [▶️ Start] [⏹️ Stop] [🔄 Restart] [📊 Remote Logs]        │
├─────────────────────────────────────────────────────────────┤
│ 🔧 Remote Operations                                        │
│ • Deploy Binary: [📤 Upload & Deploy]                      │
│ • Configuration Sync: [🔄 Push Config]                     │
│ • Health Check: [🏥 Run Diagnostics]                       │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **Multi-Node Support:** Manage multiple remote instances
- **SSH Connection Management:** Secure remote access
- **Binary Deployment:** Upload and deploy new versions
- **Remote Monitoring:** Real-time status from remote nodes

---

### 4. 🌐 **Cluster Manager** ⭐ **PRIMARY FEATURE**
**Purpose:** Centralized multi-node configuration management

#### Tab Structure:
```
🌐 Cluster Configuration Manager
├── 📊 Overview
├── ⚙️ Node Management  
├── 🔄 Config Sync
├── 📁 Config Browser
├── 🔧 Bulk Editor
└── 📈 EPS Calculator    ← NEW!
```

#### 📊 **Overview Tab**
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Cluster Overview                                         │
├───────────┬───────────┬───────────┬─────────────────────────┤
│ Total     │ Enabled   │ Disabled  │ Synced                  │
│ Nodes: 3  │ Nodes: 2  │ Nodes: 1  │ Nodes: 2                │
├───────────┴───────────┴───────────┴─────────────────────────┤
│ 📋 Node Status Table                                        │
│ ┌─────────────┬─────────────┬────────┬────────┬─────────────┐│
│ │ Node        │ Host        │ Status │ Synced │ Last Sync   ││
│ ├─────────────┼─────────────┼────────┼────────┼─────────────┤│
│ │ e2e-108-10  │ 216.48.191.10│ 🟢 On │ ✅ Yes │ 2m ago      ││
│ │ node-02     │ 10.0.0.12   │ 🔴 Off │ ❌ No  │ Never       ││
│ └─────────────┴─────────────┴────────┴────────┴─────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### ⚙️ **Node Management Tab**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Node Management                                          │
├─────────────────────────────────────────────────────────────┤
│ [➕ Add New Node]                                           │
├─────────────────────────────────────────────────────────────┤
│ 🔧 Node Configuration                                       │
│ • Name: [e2e-108-10         ]                              │
│ • Host: [216.48.191.10      ]                              │
│ • User: [vunet              ]                              │
│ • SSH Key: [~/.ssh/id_rsa   ]                              │
│ • Config Dir: [/home/vunet/vuDataSim/conf.d]              │
│ • Binary Dir: [/home/vunet/vuDataSim/bin   ]              │
│ • Enabled: ☑️                                              │
│                                                             │
│ [💾 Save Node] [🗑️ Remove] [🔧 Test Connection]           │
└─────────────────────────────────────────────────────────────┘
```

#### 🔄 **Config Sync Tab**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Configuration Sync                                       │
├─────────────────────────────────────────────────────────────┤
│ [📥 Fetch from Nodes] [📤 Push to Nodes] [🔄 Full Sync]   │
├─────────────────────────────────────────────────────────────┤
│ 📊 Sync Status                                              │
│ • Last Fetch: 2025-10-08 16:45:23                         │
│ • Files Synced: 255/255 (100%)                            │
│ • Conflicts: 0                                             │
├─────────────────────────────────────────────────────────────┤
│ 🔄 Bulk Push Configuration                                  │
│ Target Nodes: [All Enabled ▼]                             │
│ [📤 Push All Local Configs]                               │
│                                                             │
│ ✅ Push completed: 255/255 files (100% success rate)      │
└─────────────────────────────────────────────────────────────┘
```

#### 📁 **Config Browser Tab**
```
┌─────────────────────────────────────────────────────────────┐
│ 📁 Configuration Browser                                    │
├─────────────────────────────────────────────────────────────┤
│ Node: [e2e-108-10 ▼] [🔄 Refresh]                         │
├─────────────────────────────────────────────────────────────┤
│ 📂 conf.d/                                                 │
│   ├── 📂 Apache/                                           │
│   │   ├── 📄 conf.yml                                      │
│   │   ├── 📄 access_logs.yml                               │
│   │   └── 📄 error_logs.yml                                │
│   ├── 📂 Mssql/                                            │
│   │   ├── 📄 conf.yml                                      │
│   │   ├── 📄 cpu_Stats.yml                                 │
│   │   └── 📄 db_uptime.yml                                 │
│   └── 📂 AWS_ALB/                                          │
│       ├── 📄 conf.yml                                      │
│       └── 📄 cloudwatch_aws_application_elb.yml            │
│                                                             │
│ [📝 Edit Selected] [📊 Calculate EPS] [📥 Download]       │
└─────────────────────────────────────────────────────────────┘
```

#### 🔧 **Bulk Editor Tab**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Bulk Submodule Editor                                   │
├─────────────────────────────────────────────────────────────┤
│ Preview Node: [e2e-108-10 ▼] [🔄 Refresh Configuration]   │
├─────────────────────────────────────────────────────────────┤
│ 📊 Configuration Summary                                    │
│ • Total Submodules: 222                                    │
│ • With Unique Keys: 125                                    │
│ • Total Modules: 25                                        │
├─────────────────────────────────────────────────────────────┤
│ ✏️ Bulk Edit Unique Keys                                   │
│                                                             │
│ Select pattern type: ● By Module ○ By Pattern ○ Individual │
│                                                             │
│ New NumUniqKey value: [2                    ]              │
│                                                             │
│ Select modules:                                             │
│ ☑️ Mssql     ☐ Apache    ☐ AWS_ALB   ☐ Tomcat            │
│ ☐ MongoDB    ☐ K8s       ☐ Nginx     ☐ WebLogic          │
│                                                             │
│ Target nodes: ☑️ e2e-108-10                               │
│                                                             │
│ [🔍 Preview Changes] [🚀 Apply Changes]                   │
├─────────────────────────────────────────────────────────────┤
│ 📋 Preview Changes                                          │
│ 59 submodules will be updated:                             │
│ ┌────────┬──────────────────┬─────────┬───────┬─────────┐   │
│ │ Module │ Submodule        │ Current │ New   │ Change  │   │
│ ├────────┼──────────────────┼─────────┼───────┼─────────┤   │
│ │ Mssql  │ cpu_Stats        │ 3       │ 2     │ -1      │   │
│ │ Mssql  │ db_uptime        │ 3       │ 2     │ -1      │   │
│ │ Mssql  │ hard_cluster     │ 3       │ 2     │ -1      │   │
│ └────────┴──────────────────┴─────────┴───────┴─────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 📈 **EPS Calculator Tab** ⭐ **NEW FEATURE**
```
┌─────────────────────────────────────────────────────────────┐
│ 📈 EPS Calculator & Viewer                                 │
├─────────────────────────────────────────────────────────────┤
│ Node: [e2e-108-10 ▼] Period: [1 second ▼] [🔄 Refresh]   │
├─────────────────────────────────────────────────────────────┤
│ ℹ️ Formula: EPS = (Module Level unique keys × Sum of       │
│              Submodule unique keys) ÷ period               │
├─────────────────────────────────────────────────────────────┤
│ 📊 Select Modules to Analyze                               │
│ [📊 Select All] [🗑️ Clear All] [🔥 Top 5] [⚡ High Perf] │
│                                                             │
│ ☑️ Mssql     ☑️ Tomcat    ☐ Apache    ☐ AWS_ALB          │
│ ☐ MongoDB    ☐ K8s       ☐ Nginx     ☐ WebLogic          │
│                                                             │
│ [🧮 Calculate EPS]                                         │
├─────────────────────────────────────────────────────────────┤
│ 📈 EPS Results                                              │
│ ┌─────────────┬─────────────┬─────────────┬─────────────┐   │
│ │ Total EPS   │ Modules     │ Time Period │ Avg/Module  │   │
│ │ 149,986     │ 2           │ 1s          │ 74,993      │   │
│ └─────────────┴─────────────┴─────────────┴─────────────┘   │
│                                                             │
│ 📊 Module Breakdown                                         │
│ ┌────────┬─────────┬──────────┬─────────┬──────────────────┐│
│ │ Module │ EPS     │ Mod Key  │ Subs    │ Calculation      ││
│ ├────────┼─────────┼──────────┼─────────┼──────────────────┤│
│ │ Mssql  │ 99,946  │ 1,694    │ 59      │ (1694×59)÷1     ││
│ │ Tomcat │ 50,040  │ 278      │ 180     │ (278×180)÷1     ││
│ └────────┴─────────┴──────────┴─────────┴──────────────────┘│
│                                                             │
│ [📊 View All Modules] [📄 Export Report]                  │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. 📁 **Module Browser**
**Purpose:** Navigate and manage configuration modules

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ 📁 Module Browser                                           │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Filters: ☑️ Show only enabled    [🔄 Refresh]          │
├─────────────────────────────────────────────────────────────┤
│ 📋 Available Modules                                        │
│ ┌──────────────┬────────┬────────────┬─────────────────────┐│
│ │ Module       │ Status │ EPS        │ Last Modified       ││
│ ├──────────────┼────────┼────────────┼─────────────────────┤│
│ │ 📂 Apache    │ 🟢 On  │ 8,960      │ 2025-10-08 14:30   ││
│ │ 📂 Mssql     │ 🟢 On  │ 99,946     │ 2025-10-08 16:45   ││
│ │ 📂 AWS_ALB   │ 🔴 Off │ 0          │ 2025-10-07 09:15   ││
│ │ 📂 Tomcat    │ 🟢 On  │ 50,040     │ 2025-10-08 12:20   ││
│ └──────────────┴────────┴────────────┴─────────────────────┘│
│                                                             │
│ [📝 Edit Module] [📊 View EPS] [⚙️ Configure]             │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **Module Listing:** All available configuration modules
- **Status Indicators:** Enabled/disabled state
- **EPS Preview:** Quick performance metrics
- **Filtering Options:** Show/hide disabled modules

---

### 6. ✏️ **Submodule Editor**
**Purpose:** Edit individual submodule configurations

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ ✏️ Submodule Editor                                         │
├─────────────────────────────────────────────────────────────┤
│ Module: [Mssql ▼]  Submodule: [cpu_Stats ▼]               │
├─────────────────────────────────────────────────────────────┤
│ 📝 Configuration Editor                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ uniquekey:                                              │ │
│ │   name: "fields,sql_instance"                           │ │
│ │   DataType: "String"                                    │ │
│ │   ValueType: "RandomFixed"                              │ │
│ │   Value: "mssql-2[2-4]"                                 │ │
│ │   NumUniqKey: 3                    ← EDITABLE          │ │
│ │                                                         │ │
│ │ group:                                                  │ │
│ │   - name: "CPU_Stats"                                   │ │
│ │     fields:                                             │ │
│ │       - name: "cpu_utilization"                         │ │
│ │         DataType: "Float"                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [💾 Save Changes] [🔄 Reset] [📊 Calculate EPS]           │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **YAML Editor:** Syntax-highlighted configuration editing
- **Validation:** Real-time configuration validation
- **EPS Preview:** Live calculation of changes
- **Backup:** Automatic backup before changes

---

### 7. ⚡ **EPS Tuner**
**Purpose:** Optimize EPS settings for performance

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ EPS Tuner                                               │
├─────────────────────────────────────────────────────────────┤
│ Target EPS: [250000        ] Current: 149,986              │
│ Module: [Mssql ▼]                                          │
├─────────────────────────────────────────────────────────────┤
│ 📊 Current Configuration                                    │
│ • Module Unique Key: 1,694                                 │
│ • Submodule Count: 59                                      │
│ • Total Submodule Keys: 59                                 │
│ • Current EPS: 99,946                                      │
├─────────────────────────────────────────────────────────────┤
│ 🎯 Recommended Changes                                      │
│ To reach 250,000 EPS:                                      │
│ • Increase Module Key to: 4,237                            │
│ • OR increase each Submodule Key to: 2.5 (rounded to 3)   │
│                                                             │
│ [🚀 Apply Recommendation] [📊 Simulate]                   │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **Target Setting:** Set desired EPS goals
- **Recommendations:** AI-powered optimization suggestions
- **Simulation:** Preview changes before applying
- **Automatic Tuning:** One-click optimization

---

### 8. 🤖 **Auto-Tuner**
**Purpose:** Automated performance optimization

#### Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 Auto-Tuner                                              │
├─────────────────────────────────────────────────────────────┤
│ 🎯 Optimization Goals                                       │
│ Target EPS: [500000        ]                               │
│ Max CPU Usage: [80    ]%                                   │
│ Max Memory: [2048    ]MB                                   │
├─────────────────────────────────────────────────────────────┤
│ 📊 Current Performance                                      │
│ • Total EPS: 149,986                                       │
│ • CPU Usage: 15.2%                                         │
│ • Memory Usage: 256 MB                                     │
│ • Top Modules: Mssql (99,946), Tomcat (50,040)           │
├─────────────────────────────────────────────────────────────┤
│ 🔧 Auto-Tuning Strategy                                    │
│ ● Balanced    ○ Performance    ○ Conservative               │
│                                                             │
│ [🚀 Start Auto-Tuning] [⏹️ Stop] [📊 View Report]        │
├─────────────────────────────────────────────────────────────┤
│ 📈 Tuning Progress                                          │
│ ████████████████░░░░ 80% Complete                          │
│ Current Phase: Optimizing Mssql module...                  │
│ EPS Progress: 149,986 → 387,450 (+237,464)               │
└─────────────────────────────────────────────────────────────┘
```

#### Features:
- **Goal Setting:** Define performance targets
- **Strategy Selection:** Different optimization approaches
- **Real-time Progress:** Live tuning status
- **Rollback Capability:** Undo changes if needed

---

## 🔧 Technical Implementation

### Core Technologies
- **Frontend:** Streamlit (Python web framework)
- **Backend:** Python 3.12+
- **Configuration:** YAML file management
- **Remote Access:** SSH/SFTP (paramiko library)
- **Monitoring:** ClickHouse database integration
- **Logging:** Python logging with audit trail

### Key Design Patterns

#### 1. **Modular Architecture**
```python
# Core business logic separated from UI
from core.cluster_manager import get_cluster_manager
from ui.cluster_ui import render_eps_calculator

# UI components are reusable
def show_cluster_manager():
    render_cluster_overview()
    render_eps_calculator()
```

#### 2. **Session State Management**
```python
# Persistent state across interactions
if 'selected_modules' not in st.session_state:
    st.session_state.selected_modules = []

# Results caching
if 'eps_results' in st.session_state:
    display_cached_results()
```

#### 3. **Error Handling & Validation**
```python
try:
    eps_data = cluster_mgr.get_quick_eps_summary(...)
    st.success("EPS calculation successful!")
except NodeConnectionError as e:
    st.error(f"Connection failed: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")
    logger.exception("EPS calculation failed")
```

### Security Features
- **SSH Key Authentication:** Secure remote node access
- **Input Validation:** YAML syntax validation
- **Audit Logging:** Complete change history
- **Backup Management:** Automatic backups before changes
- **Permission Checks:** Node accessibility validation

### Performance Optimizations
- **Lazy Loading:** Components load data on demand
- **Caching:** Session-based result caching
- **Batch Operations:** Bulk configuration updates
- **Connection Pooling:** Reuse SSH connections
- **Background Processing:** Long operations in background

---

## 🎨 UI/UX Design Principles

### Visual Hierarchy
1. **Primary Actions:** Large, prominent buttons with icons
2. **Secondary Actions:** Smaller buttons grouped logically
3. **Status Indicators:** Color-coded (🟢 Green, 🔴 Red, 🟡 Yellow)
4. **Data Tables:** Clean, sortable, with search capabilities

### Responsive Design
- **Wide Layout:** Utilizes full screen width
- **Column Layouts:** Organized information in logical columns
- **Expandable Sections:** Collapsible content areas
- **Mobile Friendly:** Responsive components

### Accessibility
- **High Contrast:** Clear visual distinction
- **Icon + Text:** Icons paired with descriptive text
- **Keyboard Navigation:** Full keyboard accessibility
- **Screen Reader Friendly:** Proper ARIA labels

### Interaction Patterns
- **Progressive Disclosure:** Show advanced options on demand
- **Immediate Feedback:** Real-time status updates
- **Confirmation Dialogs:** Prevent accidental destructive actions
- **Loading States:** Clear progress indicators

---

## 🚀 Future Enhancements

### Planned Features
1. **Real-time Monitoring Dashboard:** Live metrics streaming
2. **Advanced Analytics:** Historical performance analysis
3. **Alert System:** Threshold-based notifications
4. **API Integration:** REST API for external tools
5. **Multi-tenant Support:** Multiple cluster management
6. **Configuration Templates:** Reusable module templates
7. **Automated Testing:** Configuration validation pipeline
8. **Dark Mode:** Alternative theme support

### Scalability Considerations
- **Horizontal Scaling:** Support for 100+ nodes
- **Load Balancing:** Distribute operations across nodes
- **Database Integration:** Persistent configuration storage
- **Microservices:** Split into independent services
- **Container Support:** Docker deployment options

---

This design document provides a comprehensive overview of the vuDataSim Web Interface architecture, ensuring maintainable, scalable, and user-friendly cluster management capabilities.
