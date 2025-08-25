from app import db
from app.models import Company, User
from flask import session

class CompanyService:
    """Service class for company-related business logic and multi-tenant operations"""
    
    @staticmethod
    def get_user_companies(user_id):
        """Get all companies accessible to a user"""
        user = User.query.get(user_id)
        if not user:
            return []
        return user.companies.all()
    
    @staticmethod
    def set_current_company(user_id, company_id):
        """Set the current company for a user session"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Verify user has access to this company
        if not user.has_company_access(company_id):
            return False
        
        # Update user's current company
        user.current_company_id = company_id
        db.session.commit()
        
        # Store in session for quick access
        session['current_company_id'] = company_id
        return True
    
    @staticmethod
    def get_current_company():
        """Get the current company from session or user record"""
        return session.get('current_company_id')
    
    @staticmethod
    def create_company(name, registration_number=None, industry=None, **kwargs):
        """Create a new company"""
        company = Company()
        company.name = name
        company.registration_number = registration_number
        company.industry = industry
        
        # Set optional fields
        for field in ['address', 'phone', 'email', 'tax_year_end',
                     'default_hourly_rate', 'default_daily_rate',
                     'overtime_multiplier', 'sunday_multiplier',
                     'public_holiday_multiplier', 'uif_monthly_ceiling', 'uif_percent',
                     'sdl_percent', 'default_pay_date']:
            if field in kwargs:
                setattr(company, field, kwargs[field])
        
        db.session.add(company)
        db.session.commit()
        return company
    
    @staticmethod
    def grant_company_access(user_id, company_id):
        """Grant a user access to a company"""
        user = User.query.get(user_id)
        company = Company.query.get(company_id)
        
        if not user or not company:
            return False
        
        if company not in user.companies:
            user.companies.append(company)
            db.session.commit()
        
        return True
    
    @staticmethod
    def revoke_company_access(user_id, company_id):
        """Revoke a user's access to a company"""
        user = User.query.get(user_id)
        company = Company.query.get(company_id)
        
        if not user or not company:
            return False
        
        if company in user.companies:
            user.companies.remove(company)
            db.session.commit()
        
        return True
    
    @staticmethod
    def get_company_stats(company_id):
        """Get statistics for a specific company"""
        from app.models import Employee, PayrollEntry
        
        stats = {
            'total_employees': Employee.query.filter_by(company_id=company_id).count(),
            'active_employees': Employee.query.filter_by(
                company_id=company_id, 
                employment_status='Active'
            ).count(),
            'total_payroll_entries': PayrollEntry.query.join(Employee).filter(
                Employee.company_id == company_id
            ).count()
        }
        
        return stats