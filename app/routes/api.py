from flask import Blueprint, jsonify, request
from app.services.tracking_service import tracking_service
from app.utils.helpers import validate_direction

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    from app.services.rfid_service import rfid_reader
    from app.services.sensor_service import sensor_manager
    
    return jsonify({
        'status': 'success',
        'data': tracking_service.get_status(),
        'config': {
            'rfid_power': rfid_reader.read_power,
            'sensor_range': sensor_manager.sensor_inside.detection_range
        }
    })


@api_bp.route('/records', methods=['GET'])
def get_records():
    """Get tracking records with filters"""
    filters = {}
    
    if request.args.get('direction'):
        filters['direction'] = request.args.get('direction')
    
    if request.args.get('limit'):
        filters['limit'] = int(request.args.get('limit'))
    
    if request.args.get('start_date'):
        filters['start_date'] = request.args.get('start_date')
    
    if request.args.get('end_date'):
        filters['end_date'] = request.args.get('end_date')
    
    records = tracking_service.get_all_records(filters)
    
    return jsonify({
        'status': 'success',
        'count': len(records),
        'data': records
    })


@api_bp.route('/records/<tag_id>', methods=['GET'])
def get_tag_records(tag_id):
    """Get records for specific RFID tag"""
    records = tracking_service.get_tag_records(tag_id)
    
    return jsonify({
        'status': 'success',
        'tag_id': tag_id,
        'count': len(records),
        'data': records
    })


@api_bp.route('/records', methods=['POST'])
def add_manual_record():
    """Manually add tracking record"""
    data = request.get_json()
    
    if not data or 'rfid_tag' not in data or 'direction' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields: rfid_tag, direction'
        }), 400
    
    if not validate_direction(data['direction']):
        return jsonify({
            'status': 'error',
            'message': 'Direction must be IN or OUT'
        }), 400
    
    record = tracking_service.add_record(data['rfid_tag'], data['direction'])
    
    return jsonify({
        'status': 'success',
        'message': 'Record added successfully',
        'data': record
    })


@api_bp.route('/records', methods=['DELETE'])
def clear_records():
    """Clear all tracking records"""
    if request.args.get('confirm') != 'true':
        return jsonify({
            'status': 'error',
            'message': 'Add ?confirm=true to clear all records'
        }), 400
    
    tracking_service.clear_all_records()
    
    return jsonify({
        'status': 'success',
        'message': 'All records cleared'
    })


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get tracking statistics"""
    stats = tracking_service.get_statistics()
    
    return jsonify({
        'status': 'success',
        'data': stats
    })


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with custom timestamp format: YYYY-MM-DD-HH-MM-SS-milliseconds"""
    from datetime import datetime
    # Format: years-months-days-hours-minutes-seconds-milliseconds (milliseconds = 3 digits)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]
    return jsonify({
        'status': 'healthy',
        'timestamp': timestamp
    })