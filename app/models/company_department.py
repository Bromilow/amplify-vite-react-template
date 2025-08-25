from datetime import datetime
from app import db


class CompanyDepartment(db.Model):
    """Model for company-specific departments"""
    __tablename__ = 'company_departments'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship back to company
    company = db.relationship('Company', backref='departments')
    
    # Unique constraint per company
    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='uq_company_department'),
    )
    
    def __repr__(self):
        return f'<CompanyDepartment {self.name} (Company {self.company_id})>'
    
    @classmethod
    def get_company_departments(cls, company_id):
        """Get all departments for a specific company"""
        return cls.query.filter_by(company_id=company_id).order_by(cls.name).all()
    
    @classmethod
    def get_or_create_department(cls, company_id, department_name):
        """Get existing department or create new one for the company"""
        department = cls.query.filter_by(
            company_id=company_id, 
            name=department_name
        ).first()
        
        if not department:
            department = cls(
                company_id=company_id,
                name=department_name,
                is_default=False
            )
            db.session.add(department)
            db.session.commit()
        
        return department
    
    @classmethod
    def seed_default_departments(cls, company_id):
        """Seed default departments for a new company"""
        default_departments = [
            'Engineering',
            'Research', 
            'QA',
            'Human Resources',
            'Consulting',
            'Sales',
            'Staff',
            'Finance',
            'Development'
        ]
        
        for dept_name in default_departments:
            existing = cls.query.filter_by(
                company_id=company_id,
                name=dept_name
            ).first()
            
            if not existing:
                department = cls(
                    company_id=company_id,
                    name=dept_name,
                    is_default=True
                )
                db.session.add(department)
        
        db.session.commit()
    
    @classmethod
    def is_department_in_use(cls, company_id, department_name):
        """Check if department is currently used by employees"""
        from app.models.employee import Employee
        return Employee.query.filter_by(
            company_id=company_id,
            department=department_name
        ).first() is not None