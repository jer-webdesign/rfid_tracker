import serial
import time
import threading
from collections import deque
from flask import current_app
from app.services.tracking_service import tracking_service

class MMWaveSensor:
    """Service for S3KM1110 mmWave Sensor"""
    
    def __init__(self, location: str):
        self.location = location  # 'inside' or 'outside'
        self.serial = None
        self.running = False
        self.detection_range = 5
        self.recent_detections = deque(maxlen=10)
    
    def connect(self) -> bool:
        """Connect to the sensor"""
        try:
            port = current_app.config[f'SENSOR_{self.location.upper()}_PORT']
            baud_rate = current_app.config['BAUD_RATE']
            
            self.serial = serial.Serial(port, baudrate=baud_rate, timeout=1)
            time.sleep(2)  # Wait for initialization
            
            self.detection_range = current_app.config['SENSOR_DETECTION_RANGE']
            self.configure_range(self.detection_range)
            
            tracking_service.update_status(**{f'sensor_{self.location}': 'connected'})
            print(f"mmWave sensor ({self.location}) connected on {port}")
            return True
            
        except Exception as e:
            print(f"Error connecting sensor ({self.location}): {e}")
            tracking_service.update_status(**{f'sensor_{self.location}': 'error'})
            return False
    
    def configure_range(self, distance: int):
        """Configure detection range"""
        try:
            if self.serial:
                cmd = f"sensorStart {distance}\n"
                self.serial.write(cmd.encode())
                self.detection_range = distance
                print(f"Sensor ({self.location}) range: {distance}m")
        except Exception as e:
            print(f"Error configuring sensor range: {e}")
    
    def read_data(self) -> str:
        """Read sensor data"""
        try:
            if self.serial and self.serial.in_waiting:
                return self.serial.readline().decode('utf-8', errors='ignore').strip()
        except Exception as e:
            print(f"Error reading sensor ({self.location}): {e}")
        return None
    
    def detect_human(self) -> bool:
        """Check for human presence"""
        data = self.read_data()
        if data and ('presence' in data.lower() or 'occupied' in data.lower()):
            self.recent_detections.append(time.time())
            return True
        return False
    
    def is_recently_detected(self, timeout: int) -> bool:
        """Check if human detected within timeout"""
        if not self.recent_detections:
            return False
        current_time = time.time()
        return any(current_time - t < timeout for t in self.recent_detections)
    
    def get_latest_detection(self) -> float:
        """Get timestamp of latest detection"""
        return max(self.recent_detections) if self.recent_detections else 0
    
    def monitor_loop(self):
        """Continuous monitoring loop"""
        self.running = True
        while self.running:
            try:
                self.detect_human()
                time.sleep(0.1)  # 10Hz polling
            except Exception as e:
                print(f"Sensor ({self.location}) monitor error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.serial:
            self.serial.close()


class SensorManager:
    """Manager for both mmWave sensors"""
    
    def __init__(self):
        self.sensor_inside = MMWaveSensor('inside')
        self.sensor_outside = MMWaveSensor('outside')
    
    def initialize(self):
        """Initialize both sensors"""
        if self.sensor_inside.connect():
            threading.Thread(target=self.sensor_inside.monitor_loop, daemon=True).start()
        
        if self.sensor_outside.connect():
            threading.Thread(target=self.sensor_outside.monitor_loop, daemon=True).start()
    
    def check_human_detection(self):
        """Check both sensors for recent human detection"""
        timeout = current_app.config['HUMAN_DETECTION_TIMEOUT']
        
        inside_detected = self.sensor_inside.is_recently_detected(timeout)
        outside_detected = self.sensor_outside.is_recently_detected(timeout)
        
        return inside_detected, outside_detected
    
    def determine_direction(self) -> str:
        """Determine movement direction"""
        inside_detected, outside_detected = self.check_human_detection()
        
        if inside_detected and not outside_detected:
            return "OUT"
        elif outside_detected and not inside_detected:
            return "IN"
        elif inside_detected and outside_detected:
            inside_time = self.sensor_inside.get_latest_detection()
            outside_time = self.sensor_outside.get_latest_detection()
            return "OUT" if inside_time > outside_time else "IN"
        
        return None
    
    def configure_range(self, distance: int):
        """Configure range for both sensors"""
        self.sensor_inside.configure_range(distance)
        self.sensor_outside.configure_range(distance)
    
    def shutdown(self):
        """Shutdown both sensors"""
        self.sensor_inside.stop()
        self.sensor_outside.stop()


# Global sensor manager instance
sensor_manager = SensorManager()