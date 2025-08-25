from app import db
from datetime import datetime, date

class ComplianceReminder(db.Model):
    """ComplianceReminder model for managing company-specific regulatory and custom deadlines"""
    
    __tablename__ = 'compliance_reminders'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to company
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Reminder details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    
    # Reminder configuration (stored as comma-separated string for SQLite compatibility)
    reminder_days = db.Column(db.String(100), nullable=False, default='7,3,1')
    category = db.Column(db.String(50), nullable=False, default='custom')  # 'tax', 'payroll', 'employment', 'custom'
    
    # Recurring settings
    is_recurring = db.Column(db.Boolean, nullable=False, default=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # 'monthly', 'quarterly', 'annually'
    
    # Status
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Audit fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('compliance_reminders', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_reminders', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ComplianceReminder {self.title} - Due: {self.due_date}>'
    
    def get_reminder_days(self):
        """Get reminder days as a list of integers"""
        if not self.reminder_days:
            return [7, 3, 1]  # Default values
        try:
            return [int(x.strip()) for x in self.reminder_days.split(',') if x.strip()]
        except (ValueError, AttributeError):
            return [7, 3, 1]  # Fallback to defaults
    
    def set_reminder_days(self, day_list):
        """Set reminder days from a list of integers"""
        if not day_list:
            self.reminder_days = '7,3,1'
        else:
            self.reminder_days = ','.join(map(str, day_list))
    
    def to_dict(self):
        """Convert reminder object to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'reminder_days': self.get_reminder_days(),
            'category': self.category,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def days_until_due(self):
        """Calculate days until due date"""
        if not self.due_date:
            return None
        today = date.today()
        delta = self.due_date - today
        return delta.days
    
    def is_overdue(self):
        """Check if reminder is overdue"""
        return self.days_until_due() < 0 if self.days_until_due() is not None else False
    
    def is_due_soon(self):
        """Check if reminder is due within reminder_days"""
        reminder_days_list = self.get_reminder_days()
        if not reminder_days_list or self.days_until_due() is None:
            return False
        days_until = self.days_until_due()
        return days_until >= 0 and days_until <= max(reminder_days_list)
    
    def get_calendar_event(self):
        """Convert reminder to FullCalendar event format"""
        # Color coding by category
        category_colors = {
            'tax': '#dc3545',      # Red
            'payroll': '#fd7e14',  # Orange  
            'employment': '#ffc107', # Yellow
            'custom': '#6f42c1'    # Purple
        }
        
        color = category_colors.get(self.category, '#6c757d')
        
        # Add urgency indicator for overdue items
        if self.is_overdue():
            color = '#dc3545'  # Red for overdue
            title = f"⚠️ {self.title} (OVERDUE)"
        elif self.is_due_soon():
            title = f"📅 {self.title}"
        else:
            title = self.title
            
        return {
            'id': f'reminder-{self.id}',
            'title': title,
            'start': self.due_date.isoformat(),
            'color': color,
            'textColor': 'white',
            'extendedProps': {
                'type': 'compliance_reminder',
                'category': self.category,
                'description': self.description,
                'is_recurring': self.is_recurring,
                'is_overdue': self.is_overdue(),
                'days_until': self.days_until_due()
            }
        }
    
    @classmethod
    def get_upcoming_for_company(cls, company_id, days_ahead=30):
        """Get upcoming reminders for a company within specified days"""
        from datetime import timedelta
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        return cls.query.filter(
            cls.company_id == company_id,
            cls.is_active == True,
            cls.due_date >= today,
            cls.due_date <= end_date
        ).order_by(cls.due_date.asc()).all()
    
    @classmethod
    def get_overdue_for_company(cls, company_id):
        """Get overdue reminders for a company"""
        today = date.today()
        
        return cls.query.filter(
            cls.company_id == company_id,
            cls.is_active == True,
            cls.due_date < today
        ).order_by(cls.due_date.asc()).all()
    
    @classmethod
    def get_by_category(cls, company_id, category):
        """Get reminders by category for a company"""
        return cls.query.filter(
            cls.company_id == company_id,
            cls.category == category,
            cls.is_active == True
        ).order_by(cls.due_date.asc()).all()