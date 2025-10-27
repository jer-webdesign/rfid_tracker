from flask import Flask
from flask_cors import CORS
from config import config

def create_app(config_name='production'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app)
    
    # Initialize services
    with app.app_context():
        from app.services.tracking_service import tracking_service
        
        # Use mock services if MOCK_MODE is enabled
        if app.config['MOCK_MODE']:
            print("=" * 50)
            print("RUNNING IN MOCK MODE (No hardware required)")
            print("=" * 50)
            from app.services.sensor_service_mock import sensor_manager
            from app.services.rfid_service_mock import rfid_reader
        else:
            from app.services.sensor_service import sensor_manager
            from app.services.rfid_service import rfid_reader
        
        tracking_service.initialize()
        sensor_manager.initialize()
        
        if rfid_reader.connect():
            import threading
            threading.Thread(target=rfid_reader.monitor_loop, daemon=True).start()
    
    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.config import config_bp
    from app.routes.system import system_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(system_bp)
    
    # Register test blueprint if in mock mode
    if app.config['MOCK_MODE']:
        from app.routes.test import test_bp
        app.register_blueprint(test_bp)
    
    @app.route('/')
    def index():
        mode = 'MOCK (Testing)' if app.config['MOCK_MODE'] else 'PRODUCTION (Hardware)'
        response = {
            'service': 'RFID Asset Tracking API',
            'version': '1.0.0',
            'status': 'running',
            'mode': mode
        }
        
        if app.config['MOCK_MODE']:
            response['test_endpoints'] = {
                'simulate_movement': '/api/test/simulate-movement',
                'trigger_sensor': '/api/test/trigger-sensor',
                'trigger_rfid': '/api/test/trigger-rfid',
                'sample_tags': '/api/test/sample-tags',
                'scenarios': '/api/test/scenarios'
            }
        
        return response
    
    return app