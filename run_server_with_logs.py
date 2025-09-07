#!/usr/bin/env python3
"""
Run the server with detailed logging to see exactly what's happening
"""

import logging
import sys
import os
from datetime import datetime

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'server_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

# Enable debug logging for our modules
logging.getLogger('src').setLevel(logging.DEBUG)
logging.getLogger('__main__').setLevel(logging.DEBUG)

print("🔍 Starting server with detailed logging...")
print("📝 Logs will be saved to server_debug_*.log file")
print("🚨 Watch for ERROR or EXCEPTION messages")
print("-" * 60)

# Import and run the main server
if __name__ == "__main__":
    try:
        import uvicorn
        from main import app
        
        # Run with debug logging
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="debug",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
