# Bulk Submodule Configuration Editor

## Overview

The Bulk Submodule Configuration Editor is a powerful feature that allows you to edit unique key values (`NumUniqKey`) across all submodules in your vuDataSim cluster without manually editing individual files. This centralized approach enables efficient management of configuration parameters across multiple nodes.

## Key Features

### 🎯 **Centralized Management**
- Edit unique key values for all submodules from a single interface
- No need to manually edit individual YAML files
- Supports both local and remote node configurations

### 🔧 **Multiple Editing Modes**
1. **Individual Edit**: Edit specific submodules one by one
2. **Pattern Edit**: Apply changes to groups of submodules based on patterns
3. **Bulk Operations**: Perform mathematical operations on all unique key values

### 🌐 **Multi-Node Support**
- Apply changes to all nodes in your cluster simultaneously
- Automatic backup creation before making changes
- Real-time progress tracking and detailed result reporting

### 📊 **Live Preview**
- See exactly which submodules will be affected before applying changes
- Preview current vs. new values with change calculations
- Comprehensive statistics and summaries

## How to Access

1. Start the vuDataSim Web UI: `python main.py`
2. Navigate to **"Cluster Manager"** in the sidebar
3. Click on the **"🔧 Bulk Editor"** tab

## Usage Guide

### Configuration Preview

The editor starts by showing you a summary of your current configuration:

- **Total Submodules**: Total number of submodule files found
- **With Unique Keys**: Number of submodules that have `NumUniqKey` configuration
- **Total Modules**: Number of parent modules
- **Total Unique Keys**: Sum of all current `NumUniqKey` values

### Editing Modes

#### 1. Individual Edit Mode

**Best for**: Making specific changes to individual submodules

**How to use**:
1. Expand the module you want to edit
2. Modify the "New value" field for specific submodules
3. Select target nodes
4. Choose whether to create a backup
5. Click "Apply Changes"

**Example**:
```
📁 Apache (1 submodules with unique keys)
  📄 status
    Current: 25,000
    New value: [30,000] ← Edit this field
```

#### 2. Pattern Edit Mode

**Best for**: Applying the same value to multiple submodules based on patterns

**How to use**:
1. Select pattern type:
   - **By Module**: All submodules in selected modules
   - **By Submodule Name**: All submodules with specific names
   - **All Submodules**: Every submodule with unique keys
2. Set the new value
3. Review the preview table
4. Select target nodes and apply

**Example**:
```
Pattern: By Module
Selected Modules: [Apache, Nginx, Tomcat]
New Value: 50,000
→ Will update all submodules in these 3 modules
```

#### 3. Bulk Operations Mode

**Best for**: Mathematical transformations across all submodules

**Available operations**:
- **Multiply by factor**: Scale all values (e.g., 2.0x for doubling)
- **Add/Subtract value**: Adjust all values by a fixed amount
- **Set minimum value**: Ensure no value is below a threshold
- **Set maximum value**: Cap all values at a maximum

**Example**:
```
Operation: Multiply by factor
Factor: 1.5
Filter: [K8s, old-k8s] (optional)
→ Will multiply all K8s submodule values by 1.5
```

### Target Node Selection

For each operation, you can choose which nodes to apply changes to:
- **All enabled nodes**: Apply to every active node in your cluster
- **Specific nodes**: Select individual nodes from the list
- **Single node**: Apply to just one node for testing

### Backup Options

**Highly recommended**: Always enable "Create backup before changes"
- Automatic backup creation before any modifications
- Stored in the `backups/` directory with timestamps
- Can be restored if something goes wrong

## Results and Monitoring

After applying changes, you'll see detailed results:

### Success Indicators
- ✅ **Green**: All operations successful
- ⚠️ **Yellow**: Partial success (some operations failed)
- ❌ **Red**: All operations failed

### Detailed Reporting
```
📊 Results Summary
✅ node1: All 15 updates successful
⚠️ node2: 12/15 updates successful
❌ node3: All updates failed

Details for node2:
✅ Apache/status: NumUniqKey = 30,000
✅ Nginx/access: NumUniqKey = 25,000
❌ Tomcat/metrics: Connection failed
```

## Configuration File Structure

The editor works with submodule files that have this structure:

```yaml
# Example: Apache/status.yml
uniquekey:
  name: "host"
  DataType: IPv4
  ValueType: "RandomFixed"
  Value: "10.10.10.1"
  NumUniqKey: 25000  ← This value is edited

# Other configuration...
group:
  - name: good
    fields: [...]
```

## Best Practices

### 🔒 **Safety First**
- Always create backups before making changes
- Test changes on a single node first
- Review the preview carefully before applying

### 📈 **Performance Considerations**
- Higher `NumUniqKey` values = more unique data = higher resource usage
- Consider your system's capacity when setting values
- Monitor EPS (Events Per Second) after changes

### 🎯 **Efficient Workflows**
1. **Small changes**: Use Individual Edit mode
2. **Module-wide updates**: Use Pattern Edit by Module
3. **Scaling operations**: Use Bulk Operations with multiplication
4. **Standardization**: Use Pattern Edit to set consistent values

### 🌐 **Multi-Node Management**
- Fetch configurations from nodes before editing to see current state
- Apply changes to all nodes simultaneously for consistency
- Monitor results on each node to ensure successful deployment

## Troubleshooting

### Common Issues

**"No submodules found"**
- Ensure the configuration directory exists
- Check that modules have `Include_sub_modules` specified in their `conf.yml`
- Verify submodule files exist and are readable

**"Connection failed to node"**
- Check SSH connectivity to the target node
- Verify SSH key permissions and paths
- Ensure the node is enabled in the configuration

**"Permission denied"**
- Check file permissions on target nodes
- Verify SSH user has write access to configuration directories
- Ensure configuration directories exist on target nodes

### Recovery Steps

If something goes wrong:
1. Check the detailed error messages in the results
2. Restore from backup if needed
3. Verify connectivity to affected nodes
4. Re-apply changes to failed nodes only

## Advanced Features

### Custom Filters
- Filter by module names in bulk operations
- Combine multiple pattern types for complex selections
- Preview changes before applying to minimize risks

### Progress Tracking
- Real-time progress bars during bulk operations
- Individual node status updates
- Comprehensive success/failure reporting

### Integration with EPS Calculator
- Changes to `NumUniqKey` directly affect EPS calculations
- Use in conjunction with the EPS tuner for optimal performance
- Monitor the impact of changes on overall system performance

## API Integration

The bulk editor functionality is also available programmatically:

```python
from core.cluster_manager import ClusterManager

cluster_mgr = ClusterManager()

# Get current configuration summary
summary = cluster_mgr.get_submodule_unique_key_summary()

# Prepare bulk updates
updates = {
    "Apache/status": 30000,
    "Nginx/access": 25000,
    "Tomcat/metrics": 40000
}

# Apply to all enabled nodes with backup
results = cluster_mgr.bulk_edit_all_nodes_unique_keys(
    updates, 
    create_backup=True
)
```

This enables automation and integration with other tools in your vuDataSim ecosystem.
