#!/usr/bin/env python3
"""
Test script for ClickHouse connection
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.clickhouse_monitor import ClickHouseMonitor

def test_clickhouse_connection():
    """Test the ClickHouse connection and query functionality"""
    print("Testing ClickHouse connection...")

    try:
        with ClickHouseMonitor() as monitor:
            # Test basic connection
            if not monitor.connect():
                print("❌ Failed to connect to ClickHouse")
                return False

            print("✅ Successfully connected to ClickHouse")

            # Test EPS query for the topic from your example
            topic = "azuresql-single-database-jdbc-metrics"
            print(f"Testing EPS query for topic: {topic}")

            success, eps_value, message = monitor.get_eps_for_topic(topic)

            if success:
                print(f"✅ Successfully retrieved EPS: {eps_value}")
                print(f"📊 Current OneMinuteRate for topic '{topic}': {eps_value}")
            else:
                print(f"❌ Failed to get EPS: {message}")
                return False

            # Test comprehensive metrics
            print(f"Testing comprehensive metrics for topic: {topic}")
            success, metrics, message = monitor.get_topic_metrics(topic)

            if success:
                print("✅ Successfully retrieved comprehensive metrics:")
                for key, value in metrics.items():
                    print(f"  {key}: {value}")
            else:
                print(f"❌ Failed to get metrics: {message}")
                return False

        print("✅ All tests passed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 To fix this, install the clickhouse-driver package:")
        print("   pip install clickhouse-driver>=0.2.7")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        test_clickhouse_connection()
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()