import json
import os
from typing import List
from datetime import datetime

def ensure_directory(filepath: str):
    """Ensure directory exists for file"""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def load_json_file(filepath: str, default=None):
    """Load JSON file with error handling"""
    if default is None:
        default = []
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return default


def save_json_file(filepath: str, data):
    """Save data to JSON file"""
    try:
        ensure_directory(filepath)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


def validate_direction(direction: str) -> bool:
    """Validate direction value"""
    return direction.upper() in ['IN', 'OUT']


def parse_date_filter(date_str: str) -> str:
    """Parse and validate date string"""
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d-%H-%M-%S-%f")
        return date_str
    except ValueError:
        return None