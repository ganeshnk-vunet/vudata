#!/usr/bin/env python3
"""
Test script for timeout functionality
"""
import time
import sys
import os
sys.path.append('vudatasim-web-ui/src')

from core.binary_manager import process_manager

def test_timeout():
    print("Testing timeout functionality...")

    # Start binary with 10 second timeout
    result = process_manager.start_binary("vuDataSim", timeout=10)
    if not result.get("success"):
        print(f"Failed to start: {result.get('error')}")
        return

    print(f"Started binary with PID {result.get('pid')}, timeout 10s")

    # Monitor status
    for i in range(15):
        status = process_manager.get_status("vuDataSim")
        print(f"Status at {i}s: {status.get('status')}, elapsed: {status.get('elapsed_seconds', 0):.1f}s")

        if status.get("status") in ["timeout", "stopped", "exited"]:
            print(f"Process ended: {status}")
            break

        time.sleep(1)

    # Cleanup
    process_manager.cleanup_finished_processes()

if __name__ == "__main__":
    test_timeout()