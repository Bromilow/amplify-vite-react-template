from datetime import datetime
from app import db


class EmployeeMedicalAidInfo(db.Model):
    """Stores detailed medical aid information for an employee."""

    __tablename__ = 'employee_medical_aid_info'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, unique=True, index=True)
    scheme_name = db.Column(db.String(100), nullable=True)
    membership_number = db.Column(db.String(50), nullable=True)
    number_of_dependants = db.Column(db.Integer, nullable=True, default=0)
    main_member = db.Column(db.Boolean, nullable=False, default=True)
    linked_beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=True)
    additional_dependants = db.Column(db.Integer, nullable=True, default=0)
    employer_contribution_override = db.Column(db.Numeric(10, 2), nullable=True)
    employee_contribution_override = db.Column(db.Numeric(10, 2), nullable=True)
    use_sars_calculation = db.Column(db.Boolean, nullable=False, default=True)
    effective_from = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship('Employee', backref=db.backref('medical_aid_info', uselist=False, cascade='all, delete-orphan'))
    linked_beneficiary = db.relationship('Beneficiary', backref=db.backref('medical_aid_infos', lazy='dynamic'))

    def __repr__(self):
        return f'<EmployeeMedicalAidInfo {self.employee_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'scheme_name': self.scheme_name,
            'membership_number': self.membership_number,
            'number_of_dependants': self.number_of_dependants,
            'main_member': self.main_member,
            'linked_beneficiary_id': self.linked_beneficiary_id,
            'additional_dependants': self.additional_dependants,
            'employer_contribution_override': float(self.employer_contribution_override) if self.employer_contribution_override is not None else None,
            'employee_contribution_override': float(self.employee_contribution_override) if self.employee_contribution_override is not None else None,
            'use_sars_calculation': self.use_sars_calculation,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
