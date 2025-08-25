from app import db
from datetime import datetime

class Company(db.Model):
    """Company model for multi-tenant payroll management"""
    
    __tablename__ = 'companies'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Company information
    name = db.Column(db.String(150), nullable=False)
    registration_number = db.Column(db.String(50), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    
    # Contact information
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    
    # Settings
    tax_year_end = db.Column(db.String(10), nullable=True)  # SA tax year ends in February - default from SARS config
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # SARS Declaration Fields
    uif_reference_number = db.Column(db.String(10), nullable=True)  # format: '1234567/8'
    paye_reference_number = db.Column(db.String(10), nullable=True)  # format: '7123456789'
    employer_first_name = db.Column(db.String(50), nullable=True)
    employer_last_name = db.Column(db.String(50), nullable=True)
    employer_id_number = db.Column(db.String(13), nullable=True)  # South African ID
    
    # Payroll Configuration (kept for existing functionality)
    default_hourly_rate = db.Column(db.Numeric(8, 2), nullable=True)
    default_daily_rate = db.Column(db.Numeric(8, 2), nullable=True)
    overtime_multiplier = db.Column(db.Numeric(4, 2), nullable=True, default=1.50)
    sunday_multiplier = db.Column(db.Numeric(4, 2), nullable=True, default=2.00)
    public_holiday_multiplier = db.Column(db.Numeric(4, 2), nullable=True, default=2.50)
    uif_monthly_ceiling = db.Column(db.Numeric(10, 2), nullable=True)  # Default from SARS config
    uif_percent = db.Column(db.Numeric(5, 2), nullable=True)  # Default from SARS config
    sdl_percent = db.Column(db.Numeric(5, 2), nullable=True)  # Default from SARS config
    default_pay_date = db.Column(db.String(20), nullable=True)
    default_ordinary_hours_per_day = db.Column(db.Numeric(4, 2), nullable=True, default=8.0)
    default_work_days_per_month = db.Column(db.Integer, nullable=True, default=22)
    
    # Employee Defaults
    default_salary_type = db.Column(db.String(10), nullable=True, default='monthly')
    default_salary = db.Column(db.Numeric(10, 2), nullable=True)  # Default monthly salary
    default_piece_rate = db.Column(db.Numeric(10, 4), nullable=True)  # Default piece work rate
    default_bonus_type = db.Column(db.String(50), nullable=True)
    default_annual_leave_days = db.Column(db.Integer, nullable=True, default=15)
    default_sick_leave_days = db.Column(db.Integer, nullable=True, default=10)
    
    # Statutory Defaults
    default_uif = db.Column(db.Boolean, nullable=True, default=True)
    default_sdl = db.Column(db.Boolean, nullable=True, default=True)
    default_paye_exempt = db.Column(db.Boolean, nullable=True, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # SARS configuration relationship
    sars_config = db.relationship("SARSConfig", back_populates="company", uselist=False)
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    def to_dict(self):
        """Convert company object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'registration_number': self.registration_number,
            'industry': self.industry,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'tax_year_end': self.tax_year_end,
            'is_active': self.is_active,
            'uif_reference_number': self.uif_reference_number,
            'paye_reference_number': self.paye_reference_number,
            'employer_first_name': self.employer_first_name,
            'employer_last_name': self.employer_last_name,
            'employer_id_number': self.employer_id_number,
            'default_hourly_rate': float(self.default_hourly_rate) if self.default_hourly_rate else None,
            'default_daily_rate': float(self.default_daily_rate) if self.default_daily_rate else None,
            'overtime_multiplier': float(self.overtime_multiplier) if self.overtime_multiplier else None,
            'sunday_multiplier': float(self.sunday_multiplier) if self.sunday_multiplier else None,
            'public_holiday_multiplier': float(self.public_holiday_multiplier) if self.public_holiday_multiplier else None,
            'uif_monthly_ceiling': float(self.uif_monthly_ceiling) if self.uif_monthly_ceiling else None,
            'uif_percent': float(self.uif_percent) if self.uif_percent else None,
            'sdl_percent': float(self.sdl_percent) if self.sdl_percent else None,
            'default_pay_date': self.default_pay_date,
            'default_ordinary_hours_per_day': float(self.default_ordinary_hours_per_day) if self.default_ordinary_hours_per_day else None,
            'default_work_days_per_month': self.default_work_days_per_month,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # Relationships will be defined via backref in other models