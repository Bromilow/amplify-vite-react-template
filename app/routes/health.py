from flask import Blueprint, jsonify
from app import db

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/')
def health_check():
    """Simple health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'message': 'PayrollPro is running'
    })

@health_bp.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'message': 'pong'})
