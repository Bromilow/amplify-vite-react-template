from app import db
from app.models import Employee, PayrollEntry
from datetime import date
from sqlalchemy import func, desc, or_
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class EmployeeService:
    """Service class for employee-related business logic"""
    
    @staticmethod
    def initialize_sample_data():
        """Initialize the database with sample employee data if empty"""
        
        # Skip sample data initialization in multi-tenant mode
        # TODO: Create company-specific sample data after multi-tenant setup is complete
        return
        
        # Sample employee data with South African localization
        sample_employees = [
            {
                'employee_id': 'EMP001',
                'first_name': 'John',
                'last_name': 'Smith',
                'id_number': '8501155310081',
                'tax_number': 'TX001234567',
                'cell_number': '+27721234567',
                'email': 'john.smith@company.co.za',
                'department': 'Engineering',
                'start_date': date(2023, 1, 15),
                'salary': Decimal('6250.00'),  # Monthly salary
                'salary_type': 'monthly',
                'bank_name': 'Standard Bank',
                'account_number': '401234567890'
            },
            {
                'employee_id': 'EMP002',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'id_number': '9203185420083',
                'tax_number': 'TX002345678',
                'cell_number': '+27829876543',
                'email': 'sarah.johnson@company.co.za',
                'department': 'Human Resources',
                'start_date': date(2022, 8, 10),
                'salary': Decimal('5666.67'),  # Monthly salary
                'salary_type': 'monthly',
                'bank_name': 'FNB',
                'account_number': '302345678901'
            },
            {
                'employee_id': 'EMP003',
                'first_name': 'Michael',
                'last_name': 'Davis',
                'id_number': '8712259876054',
                'tax_number': 'TX003456789',
                'cell_number': '+27731122334',
                'email': 'michael.davis@company.co.za',
                'department': 'Marketing',
                'start_date': date(2023, 3, 20),
                'salary': Decimal('4583.33'),  # Monthly salary
                'salary_type': 'monthly',
                'bank_name': 'Nedbank',
                'account_number': '103456789012'
            },
            {
                'employee_id': 'EMP004',
                'first_name': 'Emily',
                'last_name': 'Wilson',
                'id_number': '9410024567083',
                'tax_number': 'TX004567890',
                'cell_number': '+27845678901',
                'email': 'emily.wilson@company.co.za',
                'department': 'Finance',
                'start_date': date(2022, 11, 5),
                'salary': Decimal('5166.67'),  # Monthly salary
                'salary_type': 'monthly',
                'bank_name': 'ABSA',
                'account_number': '204567890123'
            },
            {
                'employee_id': 'EMP005',
                'first_name': 'Robert',
                'last_name': 'Brown',
                'id_number': '8001015309087',
                'tax_number': 'TX005678901',
                'cell_number': '+27761234567',
                'email': None,
                'department': 'Sales',
                'start_date': date(2023, 2, 1),
                'salary': Decimal('25.00'),  # Hourly rate
                'salary_type': 'hourly',
                'bank_name': 'Capitec Bank',
                'account_number': '505678901234'
            }
        ]
        
        # Create and save sample employees
        for emp_data in sample_employees:
            employee = Employee(**emp_data)
            db.session.add(employee)
        
        try:
            db.session.commit()
            logger.info("Sample employee data initialized successfully")
        except Exception as e:
            db.session.rollback()
            logger.error("Error initializing sample data: %s", e)
    
    @staticmethod
    def get_dashboard_stats(company_id=None):
        """Get dashboard statistics scoped to company"""
        from app.models import PayrollEntry, Company, Employee
        from datetime import datetime, date
        
        query = Employee.query
        if company_id:
            query = query.filter_by(company_id=company_id)

        total_employees = query.count()

        # Retrieve payroll entries scoped to the company
        if company_id:
            payroll_query = db.session.query(PayrollEntry)\
                .join(Employee)\
                .filter(Employee.company_id == company_id)
        else:
            payroll_query = db.session.query(PayrollEntry).join(Employee)
        payroll_entry_count = payroll_query.count()
        logger.debug("Payroll entries returned: %s", payroll_entry_count)
        print(f"[DEBUG] Payroll entries for company {company_id}: {payroll_entry_count}")
        
        # Calculate total monthly payroll from verified PayrollEntry records
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        payroll_query = PayrollEntry.query.filter(
            func.extract('month', PayrollEntry.created_at) == current_month,
            func.extract('year', PayrollEntry.created_at) == current_year,
            PayrollEntry.is_verified == True
        )
        if company_id:
            payroll_query = payroll_query.join(Employee).filter(Employee.company_id == company_id)
        
        verified_entries = payroll_query.all()
        total_monthly_payroll = sum(entry.net_pay for entry in verified_entries if entry.net_pay)
        
        # Count unverified payroll entries for current period
        unverified_query = PayrollEntry.query.filter(
            func.extract('month', PayrollEntry.created_at) == current_month,
            func.extract('year', PayrollEntry.created_at) == current_year,
            PayrollEntry.is_verified == False
        )
        if company_id:
            unverified_query = unverified_query.join(Employee).filter(Employee.company_id == company_id)
        unverified_entries = unverified_query.count()
        
        # Get next payroll date from company settings
        next_payroll_date = "N/A"
        if company_id:
            company = Company.query.get(company_id)
            if company and company.default_pay_date:
                if company.default_pay_date in ["End of Month", "Start of Month"]:
                    next_payroll_date = company.default_pay_date
                else:
                    # Custom date format
                    try:
                        day = int(company.default_pay_date)
                        next_month = current_month + 1 if current_month < 12 else 1
                        next_year = current_year if current_month < 12 else current_year + 1
                        next_date = date(next_year, next_month, min(day, 28))  # Ensure valid date
                        next_payroll_date = next_date.strftime("%d %b %Y")
                    except (ValueError, TypeError):
                        next_payroll_date = company.default_pay_date
        
        # Count distinct departments (scoped to company if specified)
        dept_count_query = db.session.query(func.count(func.distinct(Employee.department)))
        if company_id:
            dept_count_query = dept_count_query.filter_by(company_id=company_id)
        departments = dept_count_query.scalar() or 0
        
        return {
            'total_employees': total_employees,
            'active_employees': total_employees,  # All employees are considered active for now
            'inactive_employees': 0,
            'total_monthly_payroll': float(total_monthly_payroll),
            'unverified_entries': unverified_entries,
            'next_payroll_date': next_payroll_date,
            'departments': departments
        }
    
    @staticmethod
    def get_recent_employees(company_id=None, limit=5):
        """Get recently hired employees scoped to company"""
        query = Employee.query
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.order_by(desc(Employee.start_date)).limit(limit).all()
    
    @staticmethod
    def get_employees_paginated(search='', department='', status='', page=1, per_page=10, company_id=None):
        """Get paginated employee list with search and filters"""
        
        query = Employee.query
        
        # Apply company filter first
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        # Apply search filter
        if search:
            search_filter = or_(
                Employee.first_name.ilike(f'%{search}%'),
                Employee.last_name.ilike(f'%{search}%'),
                Employee.employee_id.ilike(f'%{search}%'),
                Employee.id_number.ilike(f'%{search}%'),
                Employee.tax_number.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Apply department filter
        if department:
            query = query.filter(Employee.department == department)
        
        # Order by last name, then first name
        query = query.order_by(Employee.last_name, Employee.first_name)
        
        # Paginate results using Flask-SQLAlchemy helper
        pagination = db.paginate(
            query,
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'employees': pagination.items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        }
    
    @staticmethod
    def get_employee_by_id(employee_id):
        """Get employee by ID"""
        return Employee.query.get(employee_id)
    
    @staticmethod
    def search_employees(query, limit=10, company_id=None):
        """Search employees by name, ID, or tax number"""
        
        search_filter = or_(
            Employee.first_name.ilike(f'%{query}%'),
            Employee.last_name.ilike(f'%{query}%'),
            Employee.employee_id.ilike(f'%{query}%'),
            Employee.id_number.ilike(f'%{query}%'),
            Employee.tax_number.ilike(f'%{query}%')
        )
        
        query_obj = Employee.query.filter(search_filter)
        if company_id:
            query_obj = query_obj.filter_by(company_id=company_id)
        
        return query_obj.limit(limit).all()
    
    @staticmethod
    def get_departments(company_id=None):
        """Get list of all departments"""
        
        query = db.session.query(Employee.department.distinct())\
                          .filter(Employee.department.isnot(None))
        
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        departments = query.all()
        return [dept[0] for dept in departments]
    
    @staticmethod
    def get_employment_statuses():
        """Get list of employment statuses"""
        
        # Since we simplified the model, return basic statuses
        return ['Active', 'Inactive']
    
    @staticmethod
    def get_employees_by_department(department_name):
        """Get all employees in a specific department"""
        
        return Employee.query.filter_by(department=department_name)\
                           .order_by(Employee.last_name, Employee.first_name).all()
    
    @staticmethod
    def get_active_employees():
        """Get all active employees"""
        
        return Employee.query.order_by(Employee.last_name, Employee.first_name).all()
    
    @staticmethod
    def get_department_breakdown():
        """Get employee breakdown by department"""
        
        return db.session.query(
            Employee.department,
            func.count(Employee.id).label('count'),
            func.avg(Employee.salary).label('avg_salary')
        ).group_by(Employee.department).all()
    
    @staticmethod
    def get_payroll_stats():
        """Get payroll-related statistics"""
        
        all_employees = Employee.query.all()
        
        salaried_employees = [emp for emp in all_employees if emp.salary_type == 'monthly']
        hourly_employees = [emp for emp in all_employees if emp.salary_type == 'hourly']
        
        total_monthly_salaries = sum(emp.monthly_salary for emp in salaried_employees)
        total_monthly_hourly = sum(emp.monthly_salary for emp in hourly_employees)
        
        return {
            'total_employees': len(all_employees),
            'salaried_employees': len(salaried_employees),
            'hourly_employees': len(hourly_employees),
            'total_monthly_salaries': total_monthly_salaries,
            'total_monthly_hourly': total_monthly_hourly,
            'total_monthly_payroll': total_monthly_salaries + total_monthly_hourly
        }
    
    @staticmethod
    def calculate_employee_payroll(employee_id, start_date, end_date):
        """Calculate payroll for a specific employee and period"""
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        # Basic calculation (can be expanded with more complex logic)
        if employee.salary:
            # Monthly salary calculation
            monthly_salary = float(employee.salary) / 12
            gross_pay = monthly_salary
        elif employee.hourly_rate:
            # Hourly calculation (assuming 160 hours per month)
            hours_worked = 160  # This would come from time tracking in a real system
            gross_pay = float(employee.hourly_rate) * hours_worked
        else:
            gross_pay = 0
        
        # Basic tax calculations (simplified)
        federal_tax = gross_pay * 0.15
        state_tax = gross_pay * 0.05
        social_security = gross_pay * 0.062
        medicare = gross_pay * 0.0145
        
        total_deductions = federal_tax + state_tax + social_security + medicare
        net_pay = gross_pay - total_deductions
        
        return {
            'gross_pay': gross_pay,
            'federal_tax': federal_tax,
            'state_tax': state_tax,
            'social_security': social_security,
            'medicare': medicare,
            'total_deductions': total_deductions,
            'net_pay': net_pay
        }
    
    @staticmethod
    def generate_payroll_report(report_type, period):
        """Generate payroll reports"""
        
        active_employees = Employee.query.filter_by(employment_status='Active').all()
        
        if report_type == 'summary':
            return {
                'type': 'Summary Report',
                'period': period,
                'total_employees': len(active_employees),
                'total_gross_pay': sum(emp.annual_salary / 12 for emp in active_employees),
                'departments': EmployeeService.get_department_breakdown()
            }
        
        return {'type': report_type, 'period': period, 'data': []}
