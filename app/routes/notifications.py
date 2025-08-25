from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.notification_service import NotificationService
from app.models import ReminderNotification

# Create notifications blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/api/unread-count')
@login_required
def unread_count():
    """Get count of unread notifications for current user"""
    count = ReminderNotification.get_unread_count(current_user.id)
    return jsonify({'count': count})

@notifications_bp.route('/api/recent')
@login_required
def recent_notifications():
    """Get recent notifications for current user"""
    limit = request.args.get('limit', 10, type=int)
    notifications = NotificationService.get_dashboard_notifications(current_user.id, limit)
    
    return jsonify([notification.to_dict() for notification in notifications])

@notifications_bp.route('/api/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a specific notification as read"""
    success = NotificationService.mark_notification_as_read(notification_id, current_user.id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Notification not found'}), 404

@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for current user"""
    count = NotificationService.mark_all_notifications_as_read(current_user.id)
    return jsonify({'success': True, 'marked_count': count})

@notifications_bp.route('/api/test-dispatch', methods=['POST'])
@login_required
def test_dispatch():
    """Test endpoint to manually trigger notification dispatch (admin only)"""
    if not current_user.is_global_admin:
        return jsonify({'error': 'Admin access required'}), 403

    notifications_sent = NotificationService.scan_and_dispatch_reminders()
    return jsonify({
        'success': True,
        'notifications_sent': notifications_sent,
        'message': f'Dispatched {notifications_sent} notifications'
    })


@notifications_bp.route('/unread')
@login_required
def unread():
    """Return unread notifications with count"""
    notifications = ReminderNotification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).order_by(ReminderNotification.created_at.desc()).all()

    from datetime import datetime
    results = []
    for n in notifications:
        delta = datetime.utcnow() - n.created_at
        if delta.days >= 1:
            time_ago = f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            time_ago = f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            time_ago = f"{delta.seconds // 60}m ago"
        else:
            time_ago = "just now"

        results.append({
            'id': n.id,
            'title': n.reminder.title if n.reminder else n.title,
            'time_ago': time_ago,
            'category': n.reminder.category if n.reminder else 'general'
        })

    return jsonify({'count': len(results), 'notifications': results})
