from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class TrackingRecord:
    """Model for tracking record"""
    rfid_tag: str
    direction: str  # 'IN' or 'OUT'
    read_date: str
    
    @classmethod
    def create(cls, rfid_tag: str, direction: str):
        """Create new tracking record with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]
        return cls(rfid_tag=rfid_tag, direction=direction, read_date=timestamp)
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SystemStatus:
    """Model for system status"""
    rfid_reader: str = 'disconnected'
    sensor_inside: str = 'disconnected'
    sensor_outside: str = 'disconnected'
    last_tag_read: Optional[dict] = None
    total_records: int = 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)