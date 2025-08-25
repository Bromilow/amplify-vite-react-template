from datetime import datetime
from decimal import Decimal
from app import db


class CompanyDeductionDefault(db.Model):
    """Model for storing default recurring deduction configurations per company"""
    __tablename__ = 'company_deduction_defaults'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=False, index=True)
    
    # Deduction configuration
    amount = db.Column(db.Numeric(10, 2), nullable=True)
    amount_type = db.Column(db.String(10), nullable=False, default='fixed')  # 'fixed', 'percent', or 'calculated'
    include_in_eft_export = db.Column(db.Boolean, nullable=False, default=False)  # Inherited from beneficiary
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('deduction_defaults', lazy='dynamic'))
    beneficiary = db.relationship('Beneficiary', backref=db.backref('company_defaults', lazy='dynamic'))
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('company_id', 'beneficiary_id', name='uq_company_beneficiary_default'),
    )
    
    def __repr__(self):
        return f'<CompanyDeductionDefault {self.company.name} -> {self.beneficiary.name}: {self.amount_type} {self.amount}>'
    
    def to_dict(self):
        """Convert deduction default object to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'beneficiary_id': self.beneficiary_id,
            'beneficiary_name': self.beneficiary.name,
            'beneficiary_type': self.beneficiary.type,
            'amount': float(self.amount) if self.amount is not None else None,
            'amount_type': self.amount_type,
            'include_in_eft_export': self.include_in_eft_export,
            'formatted_amount': self.get_formatted_amount(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_formatted_amount(self):
        """Get formatted amount string for display"""
        amt_type = (self.amount_type or '').lower()
        if amt_type == 'percent' and self.amount is not None:
            return f"{self.amount}%"
        if amt_type == 'calculated':
            return 'Calculated'
        if self.amount is None:
            return 'N/A'
        return f"R{self.amount:,.2f}"
    
    def calculate_deduction_amount(self, gross_salary):
        """Calculate the actual deduction amount based on type and value"""
        amt_type = (self.amount_type or '').lower()
        if amt_type == 'percent' and self.amount is not None:
            return (Decimal(str(gross_salary)) * self.amount / 100).quantize(Decimal('0.01'))
        if amt_type == 'calculated':
            # Calculation will be handled at employee deduction level
            return Decimal('0')
        return self.amount or Decimal('0')
    
    @classmethod
    def get_company_defaults(cls, company_id):
        """Get all deduction defaults for a company"""
        return cls.query.filter_by(company_id=company_id).all()
    
    @classmethod
    def get_default_for_beneficiary(cls, company_id, beneficiary_id):
        """Get specific default for company-beneficiary combination"""
        return cls.query.filter_by(company_id=company_id, beneficiary_id=beneficiary_id).first()