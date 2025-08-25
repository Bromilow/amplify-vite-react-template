from app import db
from datetime import datetime
from decimal import Decimal


class GlobalSARSConfig(db.Model):
    """Global SARS configuration settings that apply system-wide as defaults"""
    __tablename__ = 'global_sars_config'

    id = db.Column(db.Integer, primary_key=True)
    
    # Tax rates and caps
    uif_percent = db.Column(db.Numeric(5, 3), nullable=False, default=Decimal("1.000"))  # 1% as 1.000
    sdl_percent = db.Column(db.Numeric(5, 3), nullable=False, default=Decimal("1.000"))  # 1% as 1.000
    uif_salary_cap = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("17712.00"))  # Monthly salary cap
    uif_monthly_cap = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("177.12"))  # Monthly contribution cap
    
    # Tax year configuration
    tax_year_start_month = db.Column(db.Integer, nullable=False, default=3)  # March
    tax_year_start_day = db.Column(db.Integer, nullable=False, default=1)    # 1st
    
    # Medical aid tax credits
    medical_primary_credit = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("364.00"))
    medical_dependant_credit = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("246.00"))
    
    # Authority and display
    tax_authority_name = db.Column(db.String(64), nullable=False, default="SARS")
    currency_symbol = db.Column(db.String(5), nullable=False, default="R")
    
    # Metadata
    tax_year_display = db.Column(db.String(20), nullable=False, default="2024/2025")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<GlobalSARSConfig {self.tax_year_display}>'

    @classmethod
    def get_current(cls):
        """Get the current active global SARS configuration"""
        config = cls.query.filter_by(is_active=True).first()
        if not config:
            # Create default configuration if none exists
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config

    def get_tax_year_start_display(self):
        """Get formatted tax year start date for display"""
        months = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_name = months[self.tax_year_start_month] if 1 <= self.tax_year_start_month <= 12 else "March"
        return f"{self.tax_year_start_day} {month_name}"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'uif_percent': float(self.uif_percent),
            'sdl_percent': float(self.sdl_percent),
            'uif_salary_cap': float(self.uif_salary_cap),
            'uif_monthly_cap': float(self.uif_monthly_cap),
            'tax_year_start_month': self.tax_year_start_month,
            'tax_year_start_day': self.tax_year_start_day,
            'medical_primary_credit': float(self.medical_primary_credit),
            'medical_dependant_credit': float(self.medical_dependant_credit),
            'tax_authority_name': self.tax_authority_name,
            'currency_symbol': self.currency_symbol,
            'tax_year_display': self.tax_year_display,
            'tax_year_start_display': self.get_tax_year_start_display()
        }


class SARSConfig(db.Model):
    """Company-specific SARS configuration that overrides global defaults"""
    __tablename__ = 'sars_config'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, unique=True)

    # Tax rates and caps (nullable to allow fallback to global)
    uif_percent = db.Column(db.Numeric(5, 3), nullable=True)
    sdl_percent = db.Column(db.Numeric(5, 3), nullable=True)
    uif_salary_cap = db.Column(db.Numeric(10, 2), nullable=True)
    uif_monthly_cap = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Tax year configuration
    tax_year_start_month = db.Column(db.Integer, nullable=True)
    tax_year_start_day = db.Column(db.Integer, nullable=True)
    
    # Medical aid tax credits
    medical_primary_credit = db.Column(db.Numeric(10, 2), nullable=True)
    medical_dependant_credit = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Authority and display
    tax_authority_name = db.Column(db.String(64), nullable=True)
    currency_symbol = db.Column(db.String(5), nullable=True)
    
    # Company-specific settings
    use_global_defaults = db.Column(db.Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship("Company", back_populates="sars_config")

    def __repr__(self):
        return f'<SARSConfig Company {self.company_id}>'

    def get_effective_config(self):
        """Get effective configuration with global fallbacks"""
        global_config = GlobalSARSConfig.get_current()
        
        return {
            'uif_percent': self.uif_percent or global_config.uif_percent,
            'sdl_percent': self.sdl_percent or global_config.sdl_percent,
            'uif_salary_cap': self.uif_salary_cap or global_config.uif_salary_cap,
            'uif_monthly_cap': self.uif_monthly_cap or global_config.uif_monthly_cap,
            'tax_year_start_month': self.tax_year_start_month or global_config.tax_year_start_month,
            'tax_year_start_day': self.tax_year_start_day or global_config.tax_year_start_day,
            'medical_primary_credit': self.medical_primary_credit or global_config.medical_primary_credit,
            'medical_dependant_credit': self.medical_dependant_credit or global_config.medical_dependant_credit,
            'tax_authority_name': self.tax_authority_name or global_config.tax_authority_name,
            'currency_symbol': self.currency_symbol or global_config.currency_symbol,
            'tax_year_display': global_config.tax_year_display,
            'tax_year_start_display': self.get_tax_year_start_display()
        }

    def get_tax_year_start_display(self):
        """Get formatted tax year start date for display"""
        global_config = GlobalSARSConfig.get_current()
        month = self.tax_year_start_month or global_config.tax_year_start_month
        day = self.tax_year_start_day or global_config.tax_year_start_day
        
        months = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_name = months[month] if 1 <= month <= 12 else "March"
        return f"{day} {month_name}"

    @classmethod
    def get_for_company(cls, company_id):
        """Get or create SARS config for a company"""
        config = cls.query.filter_by(company_id=company_id).first()
        if not config:
            config = cls(company_id=company_id)
            db.session.add(config)
            db.session.commit()
        return config

    def to_dict(self):
        """Convert to dictionary with effective values"""
        effective = self.get_effective_config()
        return {
            'id': self.id,
            'company_id': self.company_id,
            'use_global_defaults': self.use_global_defaults,
            **{k: float(v) if isinstance(v, Decimal) else v for k, v in effective.items()}
        }