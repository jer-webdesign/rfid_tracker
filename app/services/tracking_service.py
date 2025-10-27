import threading
from typing import List, Dict, Optional
from flask import current_app
from app.models import TrackingRecord, SystemStatus
from app.utils.helpers import load_json_file, save_json_file

class TrackingService:
    """Service for managing tracking records"""
    
    def __init__(self):
        self.records: List[dict] = []
        self.status = SystemStatus()
        self.lock = threading.Lock()
    
    def initialize(self):
        """Initialize tracking service and load existing data"""
        data_file = current_app.config['DATA_FILE']
        self.records = load_json_file(data_file, default=[])
        self.status.total_records = len(self.records)
        print(f"Loaded {len(self.records)} existing records")
    
    def add_record(self, rfid_tag: str, direction: str) -> dict:
        """Add new tracking record"""
        record = TrackingRecord.create(rfid_tag, direction.upper())
        record_dict = record.to_dict()
        
        with self.lock:
            self.records.append(record_dict)
            self.status.last_tag_read = record_dict
            self.status.total_records = len(self.records)
            self._save()
        
        print(f"Recorded: {rfid_tag} - {direction} at {record.read_date}")
        return record_dict
    
    def get_all_records(self, filters: Optional[Dict] = None) -> List[dict]:
        """Get all records with optional filters"""
        with self.lock:
            filtered = self.records.copy()
        
        if filters:
            if 'direction' in filters:
                filtered = [r for r in filtered if r['direction'] == filters['direction'].upper()]
            
            if 'start_date' in filters:
                filtered = [r for r in filtered if r['read_date'] >= filters['start_date']]
            
            if 'end_date' in filters:
                filtered = [r for r in filtered if r['read_date'] <= filters['end_date']]
            
            if 'rfid_tag' in filters:
                filtered = [r for r in filtered if r['rfid_tag'] == filters['rfid_tag']]
        
        # Sort by date (newest first)
        filtered.sort(key=lambda x: x['read_date'], reverse=True)
        
        # Apply limit
        if filters and 'limit' in filters:
            filtered = filtered[:filters['limit']]
        
        return filtered
    
    def get_tag_records(self, tag_id: str) -> List[dict]:
        """Get all records for specific tag"""
        return self.get_all_records({'rfid_tag': tag_id})
    
    def clear_all_records(self):
        """Clear all tracking records"""
        with self.lock:
            self.records.clear()
            self.status.total_records = 0
            self.status.last_tag_read = None
            self._save()
    
    def get_statistics(self) -> dict:
        """Calculate tracking statistics"""
        with self.lock:
            total = len(self.records)
            in_count = sum(1 for r in self.records if r['direction'] == 'IN')
            out_count = sum(1 for r in self.records if r['direction'] == 'OUT')
            
            # Count unique tags
            unique_tags = len(set(r['rfid_tag'] for r in self.records))
            
            # Get most active tags
            tag_counts = {}
            for record in self.records:
                tag = record['rfid_tag']
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_records': total,
            'in_count': in_count,
            'out_count': out_count,
            'unique_tags': unique_tags,
            'current_balance': in_count - out_count,
            'top_tags': [{'tag': tag, 'count': count} for tag, count in top_tags]
        }
    
    def get_status(self) -> dict:
        """Get system status"""
        return self.status.to_dict()
    
    def update_status(self, **kwargs):
        """Update system status"""
        for key, value in kwargs.items():
            if hasattr(self.status, key):
                setattr(self.status, key, value)
    
    def _save(self):
        """Save records to file"""
        data_file = current_app.config['DATA_FILE']
        save_json_file(data_file, self.records)


# Global tracking service instance
tracking_service = TrackingService()