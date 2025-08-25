from app import db
from datetime import datetime
from decimal import Decimal

class PayrollEntry(db.Model):
    """PayrollEntry model for storing manual payroll data per employee"""
    
    __tablename__ = 'payroll_entries'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    
    # Pay period
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)

    # Month/year string for filtering (YYYY-MM)
    month_year = db.Column(db.String(7))
    
    # Hours worked
    ordinary_hours = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    overtime_hours = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    sunday_hours = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    public_holiday_hours = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    
    # Rate and allowances
    hourly_rate = db.Column(db.Numeric(8, 2), nullable=False)
    allowances = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    bonus_amount = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    deductions_other = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    union_fee = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    
    # Piece work fields
    pieces_produced = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    piece_rate = db.Column(db.Numeric(10, 4), nullable=True)
    
    # Calculated deductions
    paye = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    uif = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    sdl = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    
    # Medical aid calculations
    medical_aid_tax_credit = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    fringe_benefit_medical = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    
    # Net pay
    net_pay = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Verification status for payroll approval workflow
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Finalization status for payroll locking workflow
    is_finalized = db.Column(db.Boolean, nullable=False, default=False)
    finalized_at = db.Column(db.DateTime, nullable=True)
    finalized_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PayrollEntry Employee ID: {self.employee_id} - {self.pay_period_start} to {self.pay_period_end}>'
    
    @property
    def gross_pay(self):
        """Calculate gross pay based on salary type (monthly, hourly, daily, piece)"""
        if self.employee and self.employee.salary_type == 'monthly':
            # For monthly employees, use their monthly salary
            ordinary_pay = Decimal(str(self.employee.salary))
        elif self.employee and self.employee.salary_type == 'daily':
            # For daily employees, multiply hours by daily rate
            ordinary_pay = self.ordinary_hours * Decimal(str(self.employee.salary))
        elif self.employee and self.employee.salary_type == 'piece':
            # For piece work employees, multiply pieces produced by piece rate
            pieces = self.pieces_produced or Decimal('0')
            rate = self.piece_rate or Decimal('0')
            ordinary_pay = pieces * rate
        else:
            # For hourly employees, use hourly rate
            ordinary_pay = self.ordinary_hours * self.hourly_rate

        # Calculate overtime and special pay (only for hourly/daily employees)
        overtime_pay = Decimal('0')
        sunday_pay = Decimal('0')
        holiday_pay = Decimal('0')
        
        if self.employee and self.employee.salary_type not in ['monthly', 'piece']:
            overtime_pay = self.overtime_hours * (self.hourly_rate * Decimal('1.5'))  # Overtime at 1.5x rate
            sunday_pay = self.sunday_hours * (self.hourly_rate * Decimal('2'))  # Sunday work at 2x rate
            holiday_pay = self.public_holiday_hours * (self.hourly_rate * Decimal('2'))  # Holiday work at 2x rate

        return ordinary_pay + overtime_pay + sunday_pay + holiday_pay + self.allowances + (self.bonus_amount or Decimal('0'))
    
    @property
    def total_deductions(self):
        """Calculate total deductions including recurring deductions (medical aid, union, etc.)"""
        base_deductions = self.paye + self.uif + self.sdl + self.deductions_other

        total_recurring = Decimal('0')
        if self.employee_id:
            from app.models.employee_recurring_deduction import EmployeeRecurringDeduction
            deductions = EmployeeRecurringDeduction.query.filter_by(
                employee_id=self.employee_id,
                is_active=True
            ).all()

            for deduction in deductions:
                total_recurring += deduction.calculate_deduction_amount(self.gross_pay)

        return base_deductions + total_recurring
    
    def calculate_medical_tax_credit(self, dependants):
        """Calculate Medical Tax Credit (MTC) using SARS 2024/2025 rates"""
        if not dependants or dependants == 0:
            return Decimal('0')
        elif dependants == 1:
            return Decimal('364')  # Main member
        elif dependants == 2:
            return Decimal('728')  # Main member + 1 dependant (364 + 364)
        else:
            # Main member + first dependant + additional dependants at R246 each
            return Decimal('728') + (Decimal(str(dependants - 2)) * Decimal('246'))

    def calculate_statutory_deductions(self):
        """Calculate PAYE, UIF, and SDL based on gross pay with medical aid considerations"""
        base_gross = self.gross_pay
        
        # Add medical aid fringe benefit if any
        gross_for_tax = base_gross + (self.fringe_benefit_medical or Decimal('0'))
        
        # UIF: Dynamic rate of gross pay, with dynamic salary and monthly caps
        from app.services.sars_service import SARSService
        sars_config = SARSService.get_company_sars_config(self.employee.company_id)
        
        uif_eligible_salary = min(gross_for_tax, Decimal(str(sars_config['uif_salary_cap'])))
        uif_amount = uif_eligible_salary * Decimal(str(sars_config['uif_percent']))
        self.uif = min(uif_amount, Decimal(str(sars_config['uif_monthly_cap'])))
        
        # SDL: Dynamic rate of gross pay for employers with payroll > R500k annually
        self.sdl = gross_for_tax * Decimal(str(sars_config['sdl_percent']))
        
        # PAYE calculation (2024/2025 South African tax brackets)
        if gross_for_tax <= Decimal('7100'):
            self.paye = Decimal('0')
        elif gross_for_tax <= Decimal('11000'):
            self.paye = (gross_for_tax - Decimal('7100')) * Decimal('0.18')
        elif gross_for_tax <= Decimal('17500'):
            self.paye = Decimal('702') + (gross_for_tax - Decimal('11000')) * Decimal('0.26')
        elif gross_for_tax <= Decimal('27000'):
            self.paye = Decimal('2392') + (gross_for_tax - Decimal('17500')) * Decimal('0.31')
        elif gross_for_tax <= Decimal('39000'):
            self.paye = Decimal('5337') + (gross_for_tax - Decimal('27000')) * Decimal('0.36')
        elif gross_for_tax <= Decimal('55000'):
            self.paye = Decimal('9657') + (gross_for_tax - Decimal('39000')) * Decimal('0.39')
        else:
            self.paye = Decimal('15897') + (gross_for_tax - Decimal('55000')) * Decimal('0.41')
        
        # Apply medical tax credit if applicable
        if self.medical_aid_tax_credit and self.medical_aid_tax_credit > 0:
            self.paye = max(self.paye - self.medical_aid_tax_credit, Decimal('0'))
        
        # Ensure PAYE is not negative
        self.paye = max(self.paye, Decimal('0'))
        
        # Calculate net pay
        self.net_pay = base_gross - self.total_deductions
    
    def to_dict(self):
        """Convert payroll entry to dictionary"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'pay_period_start': self.pay_period_start.isoformat() if self.pay_period_start else None,
            'pay_period_end': self.pay_period_end.isoformat() if self.pay_period_end else None,
            'month_year': self.month_year,
            'ordinary_hours': float(self.ordinary_hours),
            'overtime_hours': float(self.overtime_hours),
            'sunday_hours': float(self.sunday_hours),
            'public_holiday_hours': float(self.public_holiday_hours),
            'hourly_rate': float(self.hourly_rate),
            'allowances': float(self.allowances),
            'bonus_amount': float(self.bonus_amount or 0),
            'deductions_other': float(self.deductions_other),
            'union_fee': float(self.union_fee),
            'paye': float(self.paye),
            'uif': float(self.uif),
            'sdl': float(self.sdl),
            'net_pay': float(self.net_pay),
            'gross_pay': float(self.gross_pay),
            'total_deductions': float(self.total_deductions),
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by': self.verified_by,
            'is_finalized': self.is_finalized,
            'finalized_at': self.finalized_at.isoformat() if self.finalized_at else None,
            'finalized_by': self.finalized_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }