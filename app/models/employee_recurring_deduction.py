from datetime import datetime
from decimal import Decimal
from app import db


class EmployeeRecurringDeduction(db.Model):
    """Model for tracking recurring payroll deductions per employee"""
    __tablename__ = 'employee_recurring_deductions'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=False, index=True)
    
    # Deduction Configuration
    amount_type = db.Column(db.String(10), nullable=False, default='Fixed')  # 'Fixed', 'Percentage', or 'Calculated'
    value = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    
    # Status and Control
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    effective_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', backref=db.backref('recurring_deductions', 
                                                            cascade='all, delete-orphan', 
                                                            lazy='dynamic'))
    beneficiary = db.relationship('Beneficiary', backref=db.backref('employee_deductions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<EmployeeRecurringDeduction {self.employee.full_name} -> {self.beneficiary.name}>'
    
    def calculate_deduction_amount(self, gross_salary):
        """Calculate the deduction amount based on type and value"""
        print(f"[DEBUG] Calculating deduction for employee {self.employee_id}, beneficiary {self.beneficiary_id}, type {self.amount_type}")
        if self.amount_type == 'Percentage':
            return (Decimal(str(gross_salary)) * (self.value or Decimal('0'))) / Decimal('100')
        if self.amount_type == 'Calculated':
            from app.services.payroll_service import calculate_medical_aid_deduction
            amount = Decimal(str(calculate_medical_aid_deduction(self.employee)))
            print(f"[DEBUG] Calculated medical aid deduction: {amount}")
            return amount
        return self.value or Decimal('0')
    
    def to_dict(self):
        """Convert deduction object to dictionary"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'beneficiary_id': self.beneficiary_id,
            'amount_type': self.amount_type,
            'value': float(self.value) if self.value is not None else None,
            'notes': self.notes,
            'is_active': self.is_active,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }