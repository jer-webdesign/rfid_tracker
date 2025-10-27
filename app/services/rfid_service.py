import serial
import time
import threading
from flask import current_app
from app.services.tracking_service import tracking_service
from app.services.sensor_service import sensor_manager

class RFIDReader:
    """Service for M5Stack UHF RFID Reader"""
    
    def __init__(self):
        self.serial = None
        self.running = False
        self.read_power = 26
    
    def connect(self) -> bool:
        """Connect to RFID reader"""
        try:
            port = current_app.config['RFID_PORT']
            baud_rate = current_app.config['BAUD_RATE']
            
            self.serial = serial.Serial(port, baudrate=baud_rate, timeout=1)
            time.sleep(2)
            
            self.read_power = current_app.config['RFID_READ_POWER']
            self.configure_power(self.read_power)
            
            tracking_service.update_status(rfid_reader='connected')
            print(f"RFID reader connected on {port}")
            return True
            
        except Exception as e:
            print(f"Error connecting RFID reader: {e}")
            tracking_service.update_status(rfid_reader='error')
            return False
    
    def configure_power(self, power_dbm: int):
        """Configure read power (controls distance)"""
        try:
            if self.serial:
                cmd = f"AT+POWER={power_dbm}\r\n"
                self.serial.write(cmd.encode())
                self.read_power = power_dbm
                print(f"RFID power set to {power_dbm} dBm")
        except Exception as e:
            print(f"Error configuring RFID power: {e}")
    
    def read_tag(self) -> str:
        """Read RFID tag"""
        try:
            if self.serial and self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line and len(line) >= 4:
                    return line
        except Exception as e:
            print(f"Error reading RFID tag: {e}")
        return None
    
    def monitor_loop(self):
        """Continuous RFID reading loop"""
        self.running = True
        
        while self.running:
            try:
                tag_id = self.read_tag()
                
                if tag_id:
                    # Check if human was detected
                    inside_detected, outside_detected = sensor_manager.check_human_detection()
                    
                    if inside_detected or outside_detected:
                        direction = sensor_manager.determine_direction()
                        
                        if direction:
                            tracking_service.add_record(tag_id, direction)
                    else:
                        print(f"Tag {tag_id} ignored - no human detection")
                
                time.sleep(0.1)  # 10Hz polling
                
            except Exception as e:
                print(f"RFID monitor error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.serial:
            self.serial.close()


# Global RFID reader instance
rfid_reader = RFIDReader()