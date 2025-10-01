#!/usr/bin/env python3
"""
Main entry point for vuDataSim Web UI
"""
import sys
import os
import logging
from pathlib import Path

# Configure basic logging before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Start the vuDataSim Web UI"""
    try:
        # Import and run the Streamlit app
        from ui.app import main as run_app

        print("🚀 Starting vuDataSim Web UI...")
        print("📁 Configuration directory: conf.d/")
        print("🎯 Binary directory: bin/")
        print("🌐 Web interface will be available at: http://localhost:8501")

        # Run the Streamlit app
        run_app()

    except KeyboardInterrupt:
        print("\n👋 Shutting down vuDataSim Web UI...")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting vuDataSim Web UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()