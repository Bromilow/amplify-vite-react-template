from app import db
from datetime import datetime

class ReminderNotification(db.Model):
    """ReminderNotification model for in-app notification system"""
    
    __tablename__ = 'reminder_notifications'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('compliance_reminders.id'), nullable=False, index=True)
    
    # Notification content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reminder_notifications', lazy='dynamic'))
    reminder = db.relationship('ComplianceReminder', backref=db.backref('notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ReminderNotification {self.title} - User: {self.user_id}>'
    
    def to_dict(self):
        """Convert notification object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reminder_id': self.reminder_id,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'reminder': {
                'title': self.reminder.title,
                'due_date': self.reminder.due_date.isoformat() if self.reminder.due_date else None,
                'category': self.reminder.category
            } if self.reminder else None
        }
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_unread_count(cls, user_id):
        """Get count of unread notifications for a user"""
        return cls.query.filter_by(user_id=user_id, is_read=False).count()
    
    @classmethod
    def get_recent_for_user(cls, user_id, limit=10):
        """Get recent notifications for a user"""
        return cls.query.filter_by(user_id=user_id)\
            .order_by(cls.created_at.desc())\
            .limit(limit).all()
    
    @classmethod
    def create_notification(cls, user_id, reminder_id, title, message):
        """Create a new notification"""
        # Check if notification already exists for this user/reminder combination today
        today = datetime.utcnow().date()
        existing = cls.query.filter(
            cls.user_id == user_id,
            cls.reminder_id == reminder_id,
            db.func.date(cls.created_at) == today
        ).first()
        
        if existing:
            return existing  # Don't create duplicate notifications for the same day
        
        notification = cls(
            user_id=user_id,
            reminder_id=reminder_id,
            title=title,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        return notification