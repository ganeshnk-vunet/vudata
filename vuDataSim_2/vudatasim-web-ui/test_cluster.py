#!/usr/bin/env python3
"""
Test script for cluster management functionality
"""
import sys
from pathlib import Path

# Add the src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.cluster_manager import ClusterManager, get_cluster_manager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test cluster manager functionality"""
    print("🌐 Testing Cluster Manager")
    print("=" * 50)
    
    try:
        # Initialize cluster manager
        cluster_mgr = get_cluster_manager()
        print("✅ Cluster manager initialized successfully")
        
        # Get cluster status
        status = cluster_mgr.get_cluster_status()
        print(f"📊 Cluster Status:")
        print(f"   Total Nodes: {status['total_nodes']}")
        print(f"   Enabled Nodes: {status['enabled_nodes']}")
        print(f"   Disabled Nodes: {status['disabled_nodes']}")
        
        # List nodes
        nodes = cluster_mgr.get_nodes()
        print(f"\n📋 Configured Nodes:")
        for node_name, node_config in nodes.items():
            enabled = "🟢" if node_config.get('enabled', True) else "🔴"
            print(f"   {enabled} {node_name}: {node_config.get('host', 'N/A')}")
        
        # Test fetch from first enabled node (if any)
        enabled_nodes = cluster_mgr.get_enabled_nodes()
        if enabled_nodes:
            test_node = list(enabled_nodes.keys())[0]
            print(f"\n🔄 Testing fetch from node: {test_node}")
            
            try:
                success = cluster_mgr.fetch_node_config(test_node)
                if success:
                    print(f"✅ Successfully fetched config from {test_node}")
                    
                    # List files
                    files = cluster_mgr.get_node_snapshot_files(test_node)
                    print(f"📁 Found {len(files)} configuration files:")
                    for file_path in files[:5]:  # Show first 5 files
                        print(f"   📄 {file_path.name}")
                    if len(files) > 5:
                        print(f"   ... and {len(files) - 5} more files")
                        
                else:
                    print(f"❌ Failed to fetch config from {test_node}")
                    
            except Exception as e:
                print(f"⚠️  Error fetching from {test_node}: {e}")
        else:
            print("\n⚠️  No enabled nodes found for testing")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
