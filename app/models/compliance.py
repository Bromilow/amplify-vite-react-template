from app import db
from datetime import datetime


class ComplianceReminderRule(db.Model):
    """System-wide compliance rules for dynamic calendar generation (EMP201, EMP501, SDL, IRP5)"""
    __tablename__ = 'compliance_reminder_rules'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule identification
    title = db.Column(db.String(255), nullable=False)  # e.g. "EMP201 Monthly Return"
    description = db.Column(db.Text, nullable=True)    # What it's for, why it's important
    category = db.Column(db.String(50), nullable=False, default='tax')  # tax, payroll, employment, custom
    
    # Frequency configuration
    frequency = db.Column(db.String(20), nullable=False)  # "monthly", "annual", "biannual"
    due_day = db.Column(db.Integer, nullable=False)       # e.g. 7 for 7th of month
    due_month = db.Column(db.Integer, nullable=True)      # e.g. 8 for August (annual/biannual only)
    
    # Application scope and reminders
    applies_to = db.Column(db.String(20), nullable=False)  # "company", "employee", "accountant"
    reminder_days = db.Column(db.String(100), nullable=True)  # comma-separated days before due date
    
    # Status and metadata
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ComplianceReminderRule {self.title} - {self.frequency}>'
    
    def get_reminder_days(self):
        """Get reminder days as a list of integers"""
        if not self.reminder_days:
            return []
        try:
            return [int(x.strip()) for x in self.reminder_days.split(',') if x.strip()]
        except ValueError:
            return []
    
    def set_reminder_days(self, days_list):
        """Set reminder days from a list of integers"""
        if not days_list:
            self.reminder_days = None
        else:
            self.reminder_days = ','.join(map(str, days_list))
    
    @classmethod
    def get_rules_by_scope(cls, scope):
        """Get all active rules for a specific scope (company, employee, accountant)"""
        return cls.query.filter(
            cls.applies_to == scope,
            cls.is_active == True
        ).all()

    def get_months_list(self):
        """Return the months this rule applies to as a list of integers"""
        if self.frequency == 'monthly':
            return list(range(1, 13))
        if not self.due_month:
            return []
        if self.frequency == 'biannual':
            second = (self.due_month + 5) % 12 + 1
            return [self.due_month, second]
        return [self.due_month]

    def set_months_list(self, month_list):
        """Set due_month from a list (uses first value)"""
        if month_list:
            self.due_month = int(month_list[0])

    def is_applicable_for_month(self, month):
        """Check if rule applies to a specific month"""
        if self.frequency == 'monthly':
            return True
        applicable_months = self.get_months_list()
        return month in applicable_months if applicable_months else False

    def get_next_due_date(self, current_date=None):
        """Calculate next due date based on rule configuration"""
        from datetime import date, timedelta
        from calendar import monthrange
        
        if current_date is None:
            current_date = date.today()
        
        if not self.due_day:
            return None
            
        if self.frequency == 'monthly':
            # Next occurrence on due_day
            next_month = current_date.month
            next_year = current_date.year
            
            # If we've passed this month's deadline, move to next month
            try:
                candidate_date = date(next_year, next_month, self.due_day)
                if candidate_date <= current_date:
                    if next_month == 12:
                        next_month = 1
                        next_year += 1
                    else:
                        next_month += 1
                    candidate_date = date(next_year, next_month, self.due_day)
                return candidate_date
            except ValueError:
                # Handle months with fewer days (e.g., Feb 30)
                last_day = monthrange(next_year, next_month)[1]
                return date(next_year, next_month, min(self.due_day, last_day))
                
        elif self.frequency in ['annual', 'biannual']:
            applicable_months = self.get_months_list()
            if not applicable_months:
                return None
                
            # Find next applicable month
            current_year = current_date.year
            for month in sorted(applicable_months):
                try:
                    candidate_date = date(current_year, month, self.due_day)
                    if candidate_date > current_date:
                        return candidate_date
                except ValueError:
                    # Handle day overflow
                    last_day = monthrange(current_year, month)[1]
                    candidate_date = date(current_year, month, min(self.due_day, last_day))
                    if candidate_date > current_date:
                        return candidate_date
            
            # If no applicable month found this year, try next year
            next_year = current_year + 1
            first_month = sorted(applicable_months)[0]
            try:
                return date(next_year, first_month, self.due_day)
            except ValueError:
                last_day = monthrange(next_year, first_month)[1]
                return date(next_year, first_month, min(self.due_day, last_day))
        
        return None

    def to_dict(self):
        """Convert rule object to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'frequency': self.frequency,
            'due_day': self.due_day,
            'due_month': self.due_month,
            'applies_to': self.applies_to,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'next_due_date': None
        }
        
        # Calculate next due date separately to avoid double computation
        next_due = self.get_next_due_date()
        if next_due is not None:
            result['next_due_date'] = next_due.isoformat()
        
        return result

    @classmethod
    def get_active_rules(cls):
        """Get all active compliance rules"""
        return cls.query.filter_by(is_active=True).all()



    @classmethod
    def get_monthly_rules(cls):
        """Get all active monthly rules"""
        return cls.query.filter_by(is_active=True, frequency='monthly').all()

    @classmethod
    def get_annual_rules(cls):
        """Get all active annual and biannual rules"""
        return cls.query.filter(
            cls.is_active == True,
            cls.frequency.in_(['annual', 'biannual'])
        ).all()