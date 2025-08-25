from datetime import datetime
from app import db


class Beneficiary(db.Model):
    """Beneficiary model for managing third-party payment recipients"""
    __tablename__ = 'beneficiaries'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Beneficiary Information
    type = db.Column(db.String(50), nullable=False)  # Medical Aid, Pension Fund, Garnishee Order, etc.
    name = db.Column(db.String(255), nullable=False)
    
    # Banking Information
    bank_name = db.Column(db.String(100), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    branch_code = db.Column(db.String(20), nullable=True)
    account_type = db.Column(db.String(20), nullable=True, default='Savings')  # Savings/Cheque
    
    # EFT Export Configuration
    include_in_eft_export = db.Column(db.Boolean, nullable=False, default=False)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref=db.backref('beneficiaries', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Beneficiary {self.name} ({self.type})>'
    
    def to_dict(self):
        """Convert beneficiary object to dictionary"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'type': self.type,
            'name': self.name,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'branch_code': self.branch_code,
            'account_type': self.account_type,
            'include_in_eft_export': self.include_in_eft_export,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }