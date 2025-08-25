from app.models.sars_config import SARSConfig, GlobalSARSConfig
from app import db
from decimal import Decimal


class SARSService:
    """Service class for managing SARS configuration and calculations"""
    
    @staticmethod
    def get_company_sars_config(company_id):
        """Get effective SARS configuration for a company with global fallbacks"""
        company_config = SARSConfig.get_for_company(company_id)
        return company_config.get_effective_config()
    
    @staticmethod
    def get_global_sars_config():
        """Get current global SARS configuration"""
        return GlobalSARSConfig.get_current()
    
    @staticmethod
    def update_company_sars_config(company_id, **kwargs):
        """Update company-specific SARS configuration"""
        config = SARSConfig.get_for_company(company_id)
        
        # Update fields if provided
        for field, value in kwargs.items():
            if hasattr(config, field):
                if value is not None and value != '':
                    # Convert percentage values to decimal
                    if field in ['uif_percent', 'sdl_percent'] and isinstance(value, (int, float, str)):
                        value = Decimal(str(value))
                    # Convert currency values to decimal
                    elif field in ['uif_salary_cap', 'uif_monthly_cap', 'medical_primary_credit', 'medical_dependant_credit']:
                        value = Decimal(str(value))
                    # Convert integer fields
                    elif field in ['tax_year_start_month', 'tax_year_start_day']:
                        value = int(value)
                    
                    setattr(config, field, value)
                else:
                    # Set to None to use global default
                    setattr(config, field, None)
        
        db.session.commit()
        return config
    
    @staticmethod
    def calculate_uif_deduction(gross_salary, company_id=None):
        """Calculate UIF deduction using company or global configuration"""
        if company_id:
            config = SARSService.get_company_sars_config(company_id)
        else:
            config = SARSService.get_global_sars_config().to_dict()
        
        # Apply salary cap first
        eligible_salary = min(Decimal(str(gross_salary)), Decimal(str(config['uif_salary_cap'])))
        
        # Calculate UIF (convert percentage to decimal)
        uif_rate = Decimal(str(config['uif_percent'])) / 100 if config['uif_percent'] > 1 else Decimal(str(config['uif_percent']))
        uif_amount = eligible_salary * uif_rate
        
        # Apply monthly cap
        return min(uif_amount, Decimal(str(config['uif_monthly_cap'])))
    
    @staticmethod
    def calculate_sdl_deduction(gross_salary, company_id=None):
        """Calculate SDL deduction using company or global configuration"""
        if company_id:
            config = SARSService.get_company_sars_config(company_id)
        else:
            config = SARSService.get_global_sars_config().to_dict()
        
        # Calculate SDL (convert percentage to decimal)
        sdl_rate = Decimal(str(config['sdl_percent'])) / 100 if config['sdl_percent'] > 1 else Decimal(str(config['sdl_percent']))
        return Decimal(str(gross_salary)) * sdl_rate
    
    @staticmethod
    def calculate_medical_aid_credit(dependants, company_id=None):
        """Calculate medical aid tax credit using company or global configuration"""
        if company_id:
            config = SARSService.get_company_sars_config(company_id)
        else:
            config = SARSService.get_global_sars_config().to_dict()
        
        primary_credit = Decimal(str(config['medical_primary_credit']))
        dependant_credit = Decimal(str(config['medical_dependant_credit']))
        
        if dependants == 0:
            return primary_credit
        elif dependants == 1:
            return primary_credit + primary_credit  # Main member + 1 dependant gets 2x primary
        else:
            # Main member + first dependant (2x primary) + additional dependants
            return (primary_credit * 2) + (Decimal(str(dependants - 1)) * dependant_credit)
    
    @staticmethod
    def get_tax_year_start_date(company_id=None, year=None):
        """Get tax year start date for a company"""
        from datetime import date
        
        if company_id:
            config = SARSService.get_company_sars_config(company_id)
        else:
            config = SARSService.get_global_sars_config().to_dict()
        
        if year is None:
            # Determine current tax year
            today = date.today()
            if today.month >= config['tax_year_start_month']:
                year = today.year
            else:
                year = today.year - 1
        
        return date(year, config['tax_year_start_month'], config['tax_year_start_day'])
    
    @staticmethod
    def get_template_context(company_id=None):
        """Get SARS configuration for template context"""
        if company_id:
            config = SARSService.get_company_sars_config(company_id)
        else:
            config = SARSService.get_global_sars_config().to_dict()
        
        return {
            'sars_config': config,
            'tax_authority_name': config['tax_authority_name'],
            'currency_symbol': config['currency_symbol'],
            'tax_year_start_display': config['tax_year_start_display'],
            'sars_uif_rate': config['uif_percent'],
            'sars_sdl_rate': config['sdl_percent'],
            'sars_uif_salary_cap': config['uif_salary_cap'],
            'sars_uif_monthly_cap': config['uif_monthly_cap'],
            'sars_medical_primary_credit': config['medical_primary_credit'],
            'sars_medical_dependant_credit': config['medical_dependant_credit'],
        }