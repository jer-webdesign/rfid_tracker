# ========================================
# FILE: app.py
# ========================================
#!/usr/bin/env python3
"""
RFID Asset Tracking System - Application Entry Point
"""
import os
from app import create_app

# Get environment
env = os.getenv('FLASK_ENV', 'production')

# Create Flask app
app = create_app(env)

if __name__ == '__main__':
    try:
        print(f"Starting RFID Tracking Server ({env} mode)...")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=app.config['DEBUG'],
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        from app.services.rfid_service import rfid_reader
        from app.services.sensor_service import sensor_manager
        
        rfid_reader.stop()
        sensor_manager.shutdown()
        
    except Exception as e:
        print(f"Fatal error: {e}")