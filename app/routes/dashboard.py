from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
import calendar
import os
from app.services.employee_service import EmployeeService
from app.services.company_service import CompanyService
from app.services.payroll_service import calculate_ytd_totals
from app.services.compliance_calendar_service import ComplianceCalendarService
from app.models import Company, CompanyDeductionDefault, Beneficiary, EmployeeRecurringDeduction, Employee, PayrollEntry
from app import db
from sqlalchemy import func
from decimal import Decimal

# Create dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page with basic stats and leave summary"""

    selected_company_id = session.get('selected_company_id')

    # Auto-select company for single-company users
    if not selected_company_id:
        user_companies = current_user.companies.all()
        if len(user_companies) == 1:
            selected_company_id = user_companies[0].id
            session['selected_company_id'] = selected_company_id

    stats = EmployeeService.get_dashboard_stats(selected_company_id)

    leave_summary = None
    gpt_status = bool(os.getenv('OPENAI_API_KEY'))
    if selected_company_id:
        company = Company.query.get(selected_company_id)
        if company:
            employees = Employee.query.filter_by(company_id=selected_company_id).all()
            if employees:
                total_allocated = 0
                total_taken = 0
                for emp in employees:
                    allocated = emp.annual_leave_days or company.default_annual_leave_days or 0
                    total_allocated += allocated
                    total_taken += getattr(emp, 'leave_taken', 0) or 0
                leave_summary = {
                    'total': total_allocated,
                    'taken': total_taken,
                    'remaining': max(total_allocated - total_taken, 0)
                }

    return render_template(
        'dashboard/index.html',
        stats=stats,
        leave_summary=leave_summary,
        gpt_status=gpt_status,
    )


def _get_next_pay_date(company):
    """Calculate the next pay date based on company settings"""
    today = date.today()
    pay_setting = company.default_pay_date or 'End of Month'

    if pay_setting == 'End of Month':
        year, month = today.year, today.month
        day = calendar.monthrange(year, month)[1]
        pay_date = date(year, month, day)
        if pay_date < today:
            month += 1
            if month > 12:
                month -= 12
                year += 1
            day = calendar.monthrange(year, month)[1]
            pay_date = date(year, month, day)
        return pay_date

    if pay_setting.isdigit():
        target_day = int(pay_setting)
        year, month = today.year, today.month
        if today.day > target_day:
            month += 1
            if month > 12:
                month -= 12
                year += 1
        day = min(target_day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    return None


def _get_upcoming_events(company):
    """Build a list of upcoming events for a company"""
    events = []
    if not company:
        return events

    from app.models import Employee

    today = date.today()

    # Employee birthdays and contract end dates
    employees = Employee.query.filter_by(company_id=company.id).all()
    for emp in employees:
        if emp.date_of_birth:
            birthday_this_year = emp.date_of_birth.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)
            events.append({
                'label': f"{emp.full_name}'s Birthday",
                'date': birthday_this_year,
                'icon': 'fa fa-birthday-cake'
            })

        if emp.end_date and emp.end_date >= today:
            events.append({
                'label': f"{emp.full_name}'s Contract Ends",
                'date': emp.end_date,
                'icon': 'fa fa-file-contract'
            })

    # Next pay day
    pay_day = _get_next_pay_date(company)
    if pay_day:
        events.append({
            'label': 'Next Pay Day',
            'date': pay_day,
            'icon': 'fa fa-money-bill'
        })

    events.sort(key=lambda e: e['date'])
    return events[:10]


def _get_deduction_stats(company_id):
    """Return deduction statistics for a company."""
    if not company_id:
        return {"total": 0, "amount": 0.0, "top_types": [], "distribution": {}}

    today = date.today()
    base_filters = [
        Employee.company_id == company_id,
        EmployeeRecurringDeduction.is_active.is_(True),
        func.coalesce(EmployeeRecurringDeduction.effective_date, today) <= today,
        func.coalesce(EmployeeRecurringDeduction.end_date, today) >= today,
    ]

    total = (
        db.session.query(func.count(EmployeeRecurringDeduction.id))
        .join(Employee)
        .filter(*base_filters)
        .scalar()
        or 0
    )

    amount = (
        db.session.query(func.coalesce(func.sum(EmployeeRecurringDeduction.value), 0))
        .join(Employee)
        .filter(*base_filters)
        .scalar()
        or 0
    )

    counts = (
        db.session.query(Beneficiary.type, func.count(EmployeeRecurringDeduction.id))
        .join(EmployeeRecurringDeduction)
        .join(Employee)
        .filter(*base_filters)
        .group_by(Beneficiary.type)
        .order_by(func.count(EmployeeRecurringDeduction.id).desc())
        .all()
    )

    distribution = {t: c for t, c in counts}
    top_types = [t for t, _ in counts[:3]]

    return {
        "total": int(total),
        "amount": float(amount),
        "top_types": top_types,
        "distribution": distribution,
    }

@dashboard_bp.route('/set-company', methods=['POST'])
@login_required
def set_company():
    """Handle company selection for multi-company users"""
    company_id = request.form.get('company_id')
    
    if not company_id:
        flash('Please select a company.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Verify user has access to this company
    if not current_user.has_company_access(int(company_id)):
        flash('You do not have access to this company.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Set company in session
    session['current_company_id'] = int(company_id)
    flash('Company selected successfully.', 'success')
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/select-company/<int:company_id>')
@login_required
def select_company(company_id):
    """Select a company and set it in session"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash('You do not have access to this company.', 'error')
        return redirect(url_for('accountant_dashboard.dashboard') if current_user.is_accountant else url_for('dashboard.overview'))
    
    # Set company in session
    session['selected_company_id'] = company_id
    session['current_company_id'] = company_id
    
    # Get company name for flash message
    company = Company.query.get(company_id)
    if company:
        flash(f'Switched to {company.name}', 'success')
    
    return redirect(url_for('dashboard.overview'))

@dashboard_bp.route('/clear-company')
@login_required
def clear_company():
    """Clear company selection and redirect to portfolio dashboard"""
    session.pop('selected_company_id', None)
    flash('Company context cleared.', 'info')
    
    # Redirect to portfolio dashboard for accountants, overview for others
    if current_user.is_accountant:
        return redirect(url_for('accountant_dashboard.dashboard'))
    else:
        return redirect(url_for('dashboard.overview'))

@dashboard_bp.route('/overview')
@login_required
def overview():
    """Multi-tenant dashboard overview for all users"""
    
    print(f"DEBUG: Overview accessed - current_user.is_authenticated: {current_user.is_authenticated}")
    print(f"DEBUG: Overview accessed - current_user.get_id(): {current_user.get_id()}")
    
    user_companies = current_user.companies.all()
    selected_company_id = session.get('selected_company_id')
    
    # For single-company users, auto-set company if not already set
    if len(user_companies) == 1 and not selected_company_id:
        company = user_companies[0]
        session['selected_company_id'] = company.id
        selected_company_id = company.id
    
    # Get stats for selected company or overall stats for multi-company users
    company_data = None
    deduction_defaults = []
    company_beneficiaries = []
    upcoming_events = []
    current_month = datetime.now().strftime('%B %Y')

    progress = None
    current_period = None
    deduction_stats = {"total": 0, "amount": 0.0, "top_types": [], "distribution": {}}
    leave_summary = None
    gpt_status = bool(os.getenv('OPENAI_API_KEY'))

    if selected_company_id:
        stats = EmployeeService.get_dashboard_stats(selected_company_id)
        company_data = next((c for c in user_companies if c.id == selected_company_id), None)
        company_name = company_data.name if company_data else "Unknown Company"

        # Get deduction defaults and beneficiaries for the selected company
        deduction_defaults = CompanyDeductionDefault.get_company_defaults(selected_company_id)
        company_beneficiaries = Beneficiary.query.filter_by(company_id=selected_company_id).order_by(Beneficiary.name.asc()).all()
        upcoming_events = _get_upcoming_events(company_data)
        deduction_stats = _get_deduction_stats(selected_company_id)

        # Leave summary calculation
        employees = Employee.query.filter_by(company_id=selected_company_id).all()
        if employees:
            total_allocated = 0
            total_taken = 0
            for emp in employees:
                allocated = emp.annual_leave_days or company_data.default_annual_leave_days or 0
                total_allocated += allocated
                total_taken += getattr(emp, 'leave_taken', 0) or 0
            leave_summary = {
                'total': total_allocated,
                'taken': total_taken,
                'remaining': max(total_allocated - total_taken, 0)
            }

        # Payroll progress tracking
        from datetime import date
        import calendar

        today = date.today()
        current_period = today.strftime('%Y-%m')
        month_start = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)

        total_employees = Employee.query.filter_by(company_id=selected_company_id).count()

        processed = db.session.query(PayrollEntry).join(Employee)\
            .filter(Employee.company_id == selected_company_id)\
            .filter(PayrollEntry.pay_period_start >= month_start)\
            .filter(PayrollEntry.pay_period_end <= month_end)\
            .count()

        verified = db.session.query(PayrollEntry).join(Employee)\
            .filter(Employee.company_id == selected_company_id)\
            .filter(PayrollEntry.pay_period_start >= month_start)\
            .filter(PayrollEntry.pay_period_end <= month_end)\
            .filter(PayrollEntry.is_verified.is_(True))\
            .count()

        finalized = db.session.query(PayrollEntry).join(Employee)\
            .filter(Employee.company_id == selected_company_id)\
            .filter(PayrollEntry.pay_period_start >= month_start)\
            .filter(PayrollEntry.pay_period_end <= month_end)\
            .filter(PayrollEntry.is_finalized.is_(True))\
            .count()

        def pct(count):
            return int((count / total_employees) * 100) if total_employees else 0

        progress = {
            'total': total_employees,
            'processed': processed,
            'verified': verified,
            'finalized': finalized,
            'processed_percent': pct(processed),
            'verified_percent': pct(verified),
            'finalized_percent': pct(finalized)
        }

        # Department breakdown
        dept_rows = db.session.query(Employee.department, func.count(Employee.id))\
            .filter(Employee.company_id == selected_company_id)\
            .group_by(Employee.department).all()
        department_stats = {dept: count for dept, count in dept_rows}
        largest_department = max(department_stats, key=department_stats.get) if department_stats else None
        
        # Calculate YTD company totals
        today = date.today()
        tax_year_start = date(today.year if today.month >= 3 else today.year - 1, 3, 1)
        
        # Get all employees for the company and calculate YTD totals
        company_employees = Employee.query.filter_by(company_id=selected_company_id).all()
        
        ytd_stats = {
            'gross_total': 0.0,
            'paye_total': 0.0,
            'uif_total': 0.0,
            'sdl_total': 0.0,
            'net_total': 0.0,
            'finalized_periods': 0
        }
        
        if company_employees:
            for emp in company_employees:
                emp_ytd = calculate_ytd_totals(emp.id, tax_year_start)
                ytd_stats['gross_total'] += emp_ytd.get('gross_pay_ytd', 0)
                ytd_stats['paye_total'] += emp_ytd.get('paye_ytd', 0)
                ytd_stats['uif_total'] += emp_ytd.get('uif_ytd', 0)
                ytd_stats['sdl_total'] += emp_ytd.get('sdl_ytd', 0)
                ytd_stats['net_total'] += emp_ytd.get('net_pay_ytd', 0)
        
        # Count finalized payroll periods
        finalized_periods = db.session.query(PayrollEntry.month_year)\
            .join(Employee)\
            .filter(Employee.company_id == selected_company_id)\
            .filter(PayrollEntry.is_finalized.is_(True))\
            .distinct().count()
        ytd_stats['finalized_periods'] = finalized_periods
        
        # Compliance metrics
        unverified_count = stats.get('unverified_entries', 0)
        exempt_count = Employee.query.filter_by(company_id=selected_company_id, paye_exempt=True).count()
        missing_salary_count = Employee.query.filter_by(company_id=selected_company_id).filter(
            (Employee.salary.is_(None)) | (Employee.salary == 0)
        ).count()
    else:
        # Multi-company overview - aggregate stats across all companies
        stats = EmployeeService.get_dashboard_stats()  # All companies
        company_name = None
        department_stats = {}
        largest_department = None
        ytd_stats = {'gross_total': 0.0, 'paye_total': 0.0, 'uif_total': 0.0, 'sdl_total': 0.0, 'net_total': 0.0, 'finalized_periods': 0}
        unverified_count = 0
        exempt_count = 0
        missing_salary_count = 0

    # Generate current month calendar HTML
    current_month = datetime.now()
    cal = calendar.HTMLCalendar(calendar.SUNDAY)
    calendar_html = cal.formatmonth(current_month.year, current_month.month)
    # Apply basic Bootstrap styling
    calendar_html = calendar_html.replace(
        '<table border="0" cellpadding="0" cellspacing="0" class="month">',
        '<table class="table table-bordered">'
    )
    # Highlight today
    today = datetime.now().date()
    if today.month == current_month.month and today.year == current_month.year:
        calendar_html = calendar_html.replace(f'>{today.day}<', f' class="table-primary fw-bold">{today.day}<')
    
    # Add compliance calendar events for company dashboard
    compliance_events = []
    if selected_company_id:
        try:
            compliance_events = ComplianceCalendarService.get_company_calendar_events(selected_company_id)
        except Exception as e:
            print(f"Error loading compliance events for company {selected_company_id}: {str(e)}")
    
    return render_template(
        'dashboard/overview.html',
        stats=stats,
        user_companies=user_companies,
        current_company_id=selected_company_id,
        company_data=company_data,
        company_name=company_name,
        deduction_defaults=deduction_defaults,
        company_beneficiaries=company_beneficiaries,
        company=company_data,
        show_edit_button=False,
        current_month=current_month,
        calendar_html=calendar_html,
        upcoming_events=upcoming_events,
        current_period=current_period,
        progress=progress,
        deduction_stats=deduction_stats,
        department_stats=department_stats,
        largest_department=largest_department,
        leave_summary=leave_summary,
        gpt_status=gpt_status,
        ytd_stats=ytd_stats,
        unverified_count=unverified_count,
        exempt_count=exempt_count,
        missing_salary_count=missing_salary_count,
        compliance_events=compliance_events,
    )

@dashboard_bp.route('/calendar-data')
@login_required
def company_calendar_data():
    """API endpoint for company calendar compliance events"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id:
        return jsonify({'error': 'No company selected'}), 400
    
    # Verify user has access to this company
    if not current_user.has_company_access(selected_company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get date range parameters
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    try:
        # Parse dates if provided
        start_parsed = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date() if start_date else None
        end_parsed = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date() if end_date else None
    except ValueError:
        start_parsed = None
        end_parsed = None
    
    # Generate compliance events for the company
    try:
        events = ComplianceCalendarService.get_company_calendar_events(
            selected_company_id, start_parsed, end_parsed
        )
        print(f"Company {selected_company_id} calendar API: Generated {len(events)} events")
        return jsonify(events)
    except Exception as e:
        print(f"Error generating company calendar events: {str(e)}")
        return jsonify({'error': 'Failed to load calendar events'}), 500

@dashboard_bp.route('/companies/new', methods=['GET', 'POST'])
@login_required
def new_company():
    """Create a new company for users without companies"""
    if request.method == 'POST':
        # Get form data
        company_name = request.form.get('company_name', '').strip()
        industry = request.form.get('industry', '').strip()
        registration_number = request.form.get('registration_number', '').strip()
        company_email = request.form.get('company_email', '').strip()
        company_phone = request.form.get('company_phone', '').strip()
        company_address = request.form.get('company_address', '').strip()
        tax_year_end = request.form.get('tax_year_end', 'February')

        # Get payroll configuration data
        default_hourly_rate = request.form.get('default_hourly_rate')
        overtime_multiplier = request.form.get('overtime_multiplier', '1.50')
        sunday_multiplier = request.form.get('sunday_multiplier', '2.00')
        public_holiday_multiplier = request.form.get('public_holiday_multiplier', '2.50')
        uif_monthly_ceiling = request.form.get('uif_monthly_ceiling', '17712.00')
        uif_percent = request.form.get('uif_percent', '1.00')
        sdl_percent = request.form.get('sdl_percent', '1.00')
        default_pay_date = request.form.get('default_pay_date', '').strip()
        

        
        # Validate required fields
        if not company_name:
            flash('Company name is required.', 'error')
            return render_template('dashboard/new_company.html')
        
        try:
            # Create new company using service
            company = CompanyService.create_company(
                name=company_name,
                registration_number=registration_number if registration_number else None,
                industry=industry if industry else None,
                email=company_email if company_email else None,
                phone=company_phone if company_phone else None,
                address=company_address if company_address else None,
                tax_year_end=tax_year_end,
                default_hourly_rate=Decimal(default_hourly_rate) if default_hourly_rate else None,
                overtime_multiplier=Decimal(overtime_multiplier),
                sunday_multiplier=Decimal(sunday_multiplier),
                public_holiday_multiplier=Decimal(public_holiday_multiplier),
                uif_monthly_ceiling=Decimal(uif_monthly_ceiling),
                uif_percent=Decimal(uif_percent),
                sdl_percent=Decimal(sdl_percent),
                default_pay_date=default_pay_date or None,
            )
            
            # Associate company with current user
            CompanyService.grant_company_access(current_user.id, company.id)
            
            # Initialize default departments for the new company
            from app.models.company_department import CompanyDepartment
            CompanyDepartment.seed_default_departments(company.id)
            
            # Set as current company
            current_user.current_company_id = company.id
            session['selected_company_id'] = company.id
            session['current_company_id'] = company.id
            
            from app import db
            db.session.commit()
            
            flash(f'Company "{company_name}" created successfully!', 'success')
            return redirect(url_for('dashboard.overview'))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            print(f"Company creation error: {e}")
            flash('Failed to create company. Please try again.', 'error')
            return render_template('dashboard/new_company.html')
    
    # GET request - show company creation form
    return render_template('dashboard/new_company.html')

@dashboard_bp.route('/company/<int:company_id>/edit', methods=['POST'])
@login_required
def edit_company(company_id):
    """Edit company details and payroll configuration"""
    from app.models.company import Company
    from app import db
    
    # Verify user has access to this company
    company = Company.query.filter_by(id=company_id).first()
    if not company or not current_user.has_company_access(company_id):
        flash('Company not found or access denied.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    try:
        # Get form data
        company_name = request.form.get('company_name', '').strip()
        industry = request.form.get('industry', '').strip()
        registration_number = request.form.get('registration_number', '').strip()
        company_email = request.form.get('company_email', '').strip()
        company_phone = request.form.get('company_phone', '').strip()
        company_address = request.form.get('company_address', '').strip()
        tax_year_end = request.form.get('tax_year_end', 'February')
        
        # Payroll configuration is edited separately
        
        # Validate required fields
        if not company_name:
            flash('Company name is required.', 'error')
            return redirect(url_for('dashboard.overview'))
        
        # Update company details
        company.name = company_name
        company.industry = industry if industry else None
        company.registration_number = registration_number if registration_number else None
        company.email = company_email if company_email else None
        company.phone = company_phone if company_phone else None
        company.address = company_address if company_address else None
        company.tax_year_end = tax_year_end
        
        db.session.commit()
        flash(f'Company "{company_name}" updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Company update error: {e}")
        flash('Failed to update company. Please try again.', 'error')
    
    return redirect(url_for('dashboard.overview'))

@dashboard_bp.route('/migrate-companies', methods=['POST'])
@login_required
def migrate_companies():
    """Backfill default values for existing companies without payroll configuration"""
    from app.models.company import Company
    from app import db
    from decimal import Decimal
    
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    try:
        # Get all companies that need migration
        companies = Company.query.all()
        migrated_count = 0
        
        for company in companies:
            updated = False
            
            # Set default payroll configuration values where missing
            if company.overtime_multiplier is None:
                company.overtime_multiplier = Decimal("1.50")
                updated = True
            
            if company.sunday_multiplier is None:
                company.sunday_multiplier = Decimal("2.00")
                updated = True
            
            if company.public_holiday_multiplier is None:
                company.public_holiday_multiplier = Decimal("2.50")
                updated = True
            
            if company.uif_monthly_ceiling is None:
                company.uif_monthly_ceiling = Decimal("17712.00")
                updated = True
            
            if company.uif_percent is None:
                company.uif_percent = Decimal("1.00")
                updated = True
            
            if company.sdl_percent is None:
                company.sdl_percent = Decimal("1.00")
                updated = True
            
            if updated:
                migrated_count += 1
        
        db.session.commit()
        flash(f'Migration completed successfully. Updated {migrated_count} companies with default payroll settings.', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Company migration error: {e}")
        flash('Migration failed. Please try again.', 'error')
    
    return redirect(url_for('dashboard.overview'))

@dashboard_bp.route('/companies/<int:company_id>/employee-defaults', methods=['POST'])
@login_required
def update_employee_defaults(company_id):
    """Update employee default settings for a company"""
    from app.models.company import Company
    from app import db
    from decimal import Decimal
    
    # Check if user has access to this company
    company = Company.query.get_or_404(company_id)
    if not current_user.has_company_access(company_id):
        flash('Access denied. You do not have permission to edit this company.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    try:
        # Payroll & Salary Defaults
        company.default_salary_type = request.form.get('default_salary_type', 'monthly')
        company.default_salary = Decimal(request.form.get('default_salary', 0)) if request.form.get('default_salary') else None
        company.default_bonus_type = request.form.get('default_bonus_type') or None
        
        # Handle pay date logic (dropdown + custom date)
        pay_date_selection = request.form.get('default_pay_date')
        if pay_date_selection == 'Custom Date':
            custom_pay_day = request.form.get('custom_pay_day')
            if custom_pay_day and custom_pay_day.isdigit():
                day = int(custom_pay_day)
                if 1 <= day <= 31:
                    company.default_pay_date = str(day)
                else:
                    company.default_pay_date = 'End of Month'  # Default fallback
            else:
                company.default_pay_date = 'End of Month'  # Default fallback
        else:
            company.default_pay_date = pay_date_selection or 'End of Month'
        
        # Default Work Schedule
        doh = request.form.get('default_ordinary_hours_per_day')
        if doh:
            try:
                company.default_ordinary_hours_per_day = Decimal(doh)
            except:
                company.default_ordinary_hours_per_day = 8
        else:
            company.default_ordinary_hours_per_day = 8

        dwp = request.form.get('default_work_days_per_month')
        if dwp:
            try:
                company.default_work_days_per_month = int(dwp)
            except:
                company.default_work_days_per_month = 22
        else:
            company.default_work_days_per_month = 22
        
        # Parse and validate numeric fields
        default_hourly_rate = request.form.get('default_hourly_rate')
        if default_hourly_rate:
            try:
                company.default_hourly_rate = Decimal(default_hourly_rate)
            except:
                flash('Invalid default hourly rate', 'error')
                return redirect(url_for('dashboard.overview'))
        else:
            company.default_hourly_rate = None

        default_daily_rate = request.form.get('default_daily_rate')
        if default_daily_rate:
            try:
                company.default_daily_rate = Decimal(default_daily_rate)
            except:
                flash('Invalid default daily rate', 'error')
                return redirect(url_for('dashboard.overview'))
        else:
            company.default_daily_rate = None

        default_piece_rate = request.form.get('default_piece_rate')
        if default_piece_rate:
            try:
                company.default_piece_rate = Decimal(default_piece_rate)
            except:
                flash('Invalid default piece rate', 'error')
                return redirect(url_for('dashboard.overview'))
        else:
            company.default_piece_rate = None
        
        # Pay Structure Multipliers
        overtime_multiplier = request.form.get('overtime_multiplier')
        if overtime_multiplier:
            try:
                company.overtime_multiplier = Decimal(overtime_multiplier)
            except:
                company.overtime_multiplier = Decimal('1.50')
        else:
            company.overtime_multiplier = Decimal('1.50')
        
        sunday_multiplier = request.form.get('sunday_multiplier')
        if sunday_multiplier:
            try:
                company.sunday_multiplier = Decimal(sunday_multiplier)
            except:
                company.sunday_multiplier = Decimal('2.00')
        else:
            company.sunday_multiplier = Decimal('2.00')
        
        public_holiday_multiplier = request.form.get('public_holiday_multiplier')
        if public_holiday_multiplier:
            try:
                company.public_holiday_multiplier = Decimal(public_holiday_multiplier)
            except:
                company.public_holiday_multiplier = Decimal('2.50')
        else:
            company.public_holiday_multiplier = Decimal('2.50')

        # Statutory Defaults
        company.default_uif = request.form.get('default_uif') == '1'
        company.default_sdl = request.form.get('default_sdl') == '1'
        company.default_paye_exempt = request.form.get('default_paye_exempt') == '1'
        
        # SARS Statutory Configuration
        uif_monthly_ceiling = request.form.get('uif_monthly_ceiling')
        if uif_monthly_ceiling:
            try:
                company.uif_monthly_ceiling = Decimal(uif_monthly_ceiling)
            except:
                company.uif_monthly_ceiling = Decimal('17712.00')
        else:
            company.uif_monthly_ceiling = Decimal('17712.00')
        
        uif_percent = request.form.get('uif_percent')
        if uif_percent:
            try:
                company.uif_percent = Decimal(uif_percent)
            except:
                company.uif_percent = Decimal('1.00')
        else:
            company.uif_percent = Decimal('1.00')
        
        sdl_percent = request.form.get('sdl_percent')
        if sdl_percent:
            try:
                company.sdl_percent = Decimal(sdl_percent)
            except:
                company.sdl_percent = Decimal('1.00')
        else:
            company.sdl_percent = Decimal('1.00')
        
        # Leave Defaults
        default_annual_leave_days = request.form.get('default_annual_leave_days')
        if default_annual_leave_days:
            try:
                company.default_annual_leave_days = int(default_annual_leave_days)
            except:
                company.default_annual_leave_days = 15
        else:
            company.default_annual_leave_days = 15
        
        default_sick_leave_days = request.form.get('default_sick_leave_days')
        if default_sick_leave_days:
            try:
                company.default_sick_leave_days = int(default_sick_leave_days)
            except:
                company.default_sick_leave_days = 10
        else:
            company.default_sick_leave_days = 10
        
        db.session.commit()
        flash('Employee defaults updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Employee defaults update error: {e}")
        flash('An error occurred while updating employee defaults. Please try again.', 'error')
    
    return redirect(url_for('dashboard.overview'))
