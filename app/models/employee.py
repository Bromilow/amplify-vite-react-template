from app import db
from datetime import datetime

class Employee(db.Model):
    """Employee model for payroll management system"""
    
    __tablename__ = 'employees'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Company relationship (for multi-tenant support)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Personal information
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    id_number = db.Column(db.String(13), nullable=True)  # South African ID number
    passport_number = db.Column(db.String(20), nullable=True)  # International passport number
    identification_type = db.Column(db.String(20), nullable=False, default='sa_id')  # 'sa_id' or 'passport'
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # Male/Female/Other
    marital_status = db.Column(db.String(20), nullable=True)
    tax_number = db.Column(db.String(50), unique=True, nullable=True)
    cell_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    physical_address = db.Column(db.Text, nullable=True)
    
    # Employment information
    department = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    employment_type = db.Column(db.String(50), nullable=False, default='Full-Time')  # Full-Time/Part-Time/Contract/Temp/Seasonal
    employment_status = db.Column(db.String(20), nullable=False, default='Active')  # Active/Suspended/Terminated
    termination_reason = db.Column(db.String(100), nullable=True)  # Dismissal/Resignation/Contract Expired/Death/Retirement
    reporting_manager = db.Column(db.String(100), nullable=True)
    union_member = db.Column(db.Boolean, nullable=False, default=False)
    union_name = db.Column(db.String(100), nullable=True)
    # union_fee_type and union_fee_amount removed - superseded by EmployeeRecurringDeduction system
    
    # Compensation information
    salary_type = db.Column(db.String(20), nullable=False, default='monthly')  # 'monthly', 'hourly', 'daily' or 'piece'
    salary = db.Column(db.Numeric(10, 2), nullable=False)  # Monthly salary or hourly rate
    overtime_eligible = db.Column(db.Boolean, nullable=False, default=True)
    allowances = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    bonus_type = db.Column(db.String(20), nullable=True)  # Fixed/Discretionary/None
    
    # Payroll configuration fields (values set via New Employee Defaults during creation)
    ordinary_hours_per_day = db.Column(db.Numeric(4, 2), nullable=True)
    work_days_per_month = db.Column(db.Integer, nullable=True)
    overtime_calc_method = db.Column(db.String(20), nullable=True)
    overtime_multiplier = db.Column(db.Numeric(4, 2), nullable=True)
    sunday_multiplier = db.Column(db.Numeric(4, 2), nullable=True)
    holiday_multiplier = db.Column(db.Numeric(4, 2), nullable=True)
    
    # Statutory deductions (values set via New Employee Defaults during creation)
    uif_contributing = db.Column(db.Boolean, nullable=True)
    sdl_contributing = db.Column(db.Boolean, nullable=True)
    paye_exempt = db.Column(db.Boolean, nullable=True)
    
    # Medical aid information
    # medical_aid_scheme, medical_aid_number, medical_aid_principal_member, medical_aid_employee, medical_aid_employer, medical_aid_dependants removed - duplicated in EmployeeMedicalAidInfo table
    medical_aid_fringe_benefit = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Changed to Numeric for taxable amount

    # Link to the medical aid beneficiary used for recurring deductions
    linked_medical_beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=True)
    linked_medical_beneficiary = db.relationship('Beneficiary', foreign_keys=[linked_medical_beneficiary_id])
    
    # Leave and banking information (values set during creation)
    annual_leave_days = db.Column(db.Integer, nullable=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(30), nullable=False)
    account_type = db.Column(db.String(20), nullable=True)  # Savings/Cheque
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.full_name}>'
    
    @property
    def full_name(self):
        """Return the employee's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def annual_salary(self):
        """Calculate annual salary based on salary type"""
        if self.salary_type == 'monthly':
            return float(self.salary) * 12
        elif self.salary_type == 'hourly':
            # Assume 40 hours/week, 52 weeks/year for hourly calculation
            return float(self.salary) * 40 * 52
        elif self.salary_type == 'daily':
            # Assume 5 working days/week, 52 weeks/year
            return float(self.salary) * 5 * 52
        return 0.0
    
    @property
    def monthly_salary(self):
        """Calculate monthly salary"""
        if self.salary_type == 'monthly':
            return float(self.salary)
        elif self.salary_type == 'hourly':
            # Assume 40 hours/week, 4.33 weeks/month for hourly calculation
            return float(self.salary) * 40 * 4.33
        elif self.salary_type == 'daily':
            # Approximate average 21.67 working days per month
            return float(self.salary) * 21.67
        return 0.0

    @property
    def medical_aid_member(self):
        return any(
            d.is_active and d.beneficiary and d.beneficiary.type == 'Medical Aid'
            for d in self.recurring_deductions
        )
    
    def to_dict(self):
        """Convert employee object to dictionary"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'id_number': self.id_number,
            'identification_type': self.identification_type,
            'passport_number': self.passport_number,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'marital_status': self.marital_status,
            'tax_number': self.tax_number,
            'cell_number': self.cell_number,
            'email': self.email,
            'physical_address': self.physical_address,
            'department': self.department,
            'job_title': self.job_title,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'employment_type': self.employment_type,
            'employment_status': self.employment_status,
            'reporting_manager': self.reporting_manager,
            'union_member': self.union_member,
            'salary_type': self.salary_type,
            'salary': float(self.salary) if self.salary else None,
            'overtime_eligible': self.overtime_eligible,
            'ordinary_hours_per_day': float(self.ordinary_hours_per_day),
            'work_days_per_month': self.work_days_per_month,
            'overtime_calc_method': self.overtime_calc_method,
            'allowances': float(self.allowances) if self.allowances else None,
            'bonus_type': self.bonus_type,
            'uif_contributing': self.uif_contributing,
            'sdl_contributing': self.sdl_contributing,
            'paye_exempt': self.paye_exempt,
            'medical_aid_member': self.medical_aid_member,
            # medical_aid_scheme, medical_aid_number, medical_aid_principal_member, medical_aid_employee, medical_aid_employer, medical_aid_dependants removed - use EmployeeMedicalAidInfo
            'medical_aid_fringe_benefit': float(self.medical_aid_fringe_benefit) if self.medical_aid_fringe_benefit else None,
            'linked_medical_beneficiary_id': self.linked_medical_beneficiary_id,
            'annual_leave_days': self.annual_leave_days,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'annual_salary': self.annual_salary,
            'monthly_salary': self.monthly_salary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # Relationships
    company = db.relationship('Company', backref='employees')
    payroll_entries = db.relationship('PayrollEntry', backref='employee', lazy=True, cascade='all, delete-orphan', order_by='PayrollEntry.pay_period_end.desc()')
    
    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('company_id', 'id_number', name='uq_company_id_number'),
    )
