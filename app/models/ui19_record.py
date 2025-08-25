from app import db
from datetime import datetime

class UI19Record(db.Model):
    """UI19 Termination Record model for South African employment termination documentation"""
    
    __tablename__ = 'ui19_records'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Employee relationship
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    
    # Company relationship (for multi-tenant support)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Termination details
    start_date = db.Column(db.Date, nullable=False)  # Employment start date
    end_date = db.Column(db.Date, nullable=False)    # Termination date
    termination_reason = db.Column(db.String(100), nullable=False)  # Dismissal/Resignation/etc
    notes = db.Column(db.Text, nullable=True)  # Additional comments
    
    # Record status
    status = db.Column(db.String(20), nullable=False, default='Generated')  # Generated/Submitted/Archived
    
    # Audit fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', backref=db.backref('ui19_records', lazy='dynamic'))
    company = db.relationship('Company', backref=db.backref('ui19_records', lazy='dynamic'))
    created_by_user = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<UI19Record {self.id}: {self.employee.full_name if self.employee else "Unknown"} - {self.termination_reason}>'
    
    def to_dict(self):
        """Convert UI19 record to dictionary"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.full_name if self.employee else 'Unknown',
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'termination_reason': self.termination_reason,
            'notes': self.notes,
            'status': self.status,
            'created_by': self.created_by_user.username if self.created_by_user else 'System',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }