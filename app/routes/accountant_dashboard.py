from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Company, Employee, PayrollEntry, ComplianceReminder
from app.services.portfolio_service import PortfolioService
from app.services.compliance_calendar_service import ComplianceCalendarService
from app import db
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
import calendar

# Create accountant dashboard blueprint
accountant_dashboard_bp = Blueprint('accountant_dashboard', __name__, url_prefix='/accountant')

@accountant_dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Accountant portfolio dashboard for multi-company management"""
    
    # Ensure user is an accountant
    if not current_user.is_accountant:
        flash('Access denied. This area is for accountants only.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    data = PortfolioService.get_overview_data(current_user)

    # Get table data for new portfolio view
    table_data = PortfolioService.get_portfolio_table_data(current_user.id)
    data['table_data'] = table_data

    # Add current server time for display
    data['current_time'] = datetime.utcnow()

    # Flatten compliance metrics for template variables
    compliance_metrics = data.get('compliance_metrics', {})
    data['companies_compliant'] = compliance_metrics.get('compliant_companies', 0)
    data['upcoming_deadlines_count'] = compliance_metrics.get('this_week_count', 0)
    data['overdue_items_count'] = compliance_metrics.get('overdue_count', 0)
    
    # Add notifications count for compliance dashboard
    data['notifications_count'] = PortfolioService.get_notifications_count(current_user.id)
    
    # Add portfolio reminders for calendar display using ComplianceCalendarService
    try:
        portfolio_reminders = ComplianceCalendarService.get_calendar_events(current_user.id)
        data['portfolio_reminders'] = portfolio_reminders
        current_app.logger.debug(f"Dashboard: {len(portfolio_reminders)} calendar events loaded")
        print(f"Dashboard: Generated {len(portfolio_reminders)} portfolio reminders")
        if portfolio_reminders:
            print(f"Sample event: {portfolio_reminders[0]}")
    except Exception as e:
        current_app.logger.error(f"Error loading portfolio reminders for dashboard: {str(e)}")
        print(f"ERROR loading portfolio reminders: {str(e)}")
        data['portfolio_reminders'] = []

    return render_template('dashboard/accountant_dashboard.html', **data)

@accountant_dashboard_bp.route('/switch-company/<int:company_id>')
@login_required
def switch_company(company_id):
    """Switch to specific company view"""
    
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash('You do not have access to this company.', 'error')
        return redirect(url_for('accountant_dashboard.dashboard'))
    
    # Set company in session (use selected_company_id for consistency)
    session['selected_company_id'] = company_id
    session['current_company_id'] = company_id
    
    # Get company name for flash message
    company = Company.query.get(company_id)
    if company:
        flash(f'Switched to {company.name}', 'success')
    
    # Handle next parameter for redirection
    next_url = request.args.get('next')
    if next_url:
        if next_url.startswith('/dashboard'):
            return redirect(url_for('dashboard.overview'))
        elif next_url.startswith('/employees'):
            return redirect(url_for('employees.index'))
        else:
            # For any other valid internal URLs
            return redirect(next_url)
    
    # Default redirect
    return redirect(url_for('dashboard.overview'))

@accountant_dashboard_bp.route('/clear-cache')
@login_required
def clear_cache():
    """Clear portfolio dashboard cache for current user"""
    if not current_user.is_accountant:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    try:
        PortfolioService.clear_user_cache(current_user.id)
        flash('Dashboard cache cleared successfully.', 'success')
        current_app.logger.info(f"Cache cleared for user {current_user.id}")
    except Exception as e:
        flash('Error clearing cache.', 'error')
        current_app.logger.error(f"Error clearing cache for user {current_user.id}: {str(e)}")
    
    return redirect(url_for('accountant_dashboard.dashboard'))

def _calculate_pending_issues(company_id):
    """Calculate pending payroll issues for a company"""
    issues = 0
    
    # Check for employees without tax numbers
    employees_without_tax = Employee.query.filter_by(company_id=company_id)\
        .filter(Employee.tax_number.is_(None)).count()
    issues += employees_without_tax
    
    # Check for missing payroll entries this month
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_payroll = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == company_id)\
        .filter(PayrollEntry.pay_period_end >= current_month_start)\
        .count()
    
    employee_count = Employee.query.filter_by(company_id=company_id).count()
    if employee_count > 0 and current_month_payroll == 0:
        issues += 1  # No payroll run this month
    
    return issues

def _get_upcoming_payroll_actions(companies):
    """Get upcoming payroll actions timeline"""
    actions = []
    today = datetime.now().date()
    
    for company in companies:
        # Monthly payroll typically due end of month
        # Get last day of current month
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)
        
        # Check if payroll has been run this month
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        payroll_done = db.session.query(PayrollEntry)\
            .join(Employee)\
            .filter(Employee.company_id == company.id)\
            .filter(PayrollEntry.pay_period_end >= current_month_start)\
            .count() > 0
        
        if not payroll_done:
            days_until_due = (month_end - today).days
            actions.append({
                'company_name': company.name,
                'company_id': company.id,
                'action': 'Monthly Payroll Processing',
                'due_date': month_end,
                'days_until': days_until_due,
                'priority': 'high' if days_until_due <= 3 else 'medium' if days_until_due <= 7 else 'low'
            })
    
    # Sort by due date
    actions.sort(key=lambda x: x['due_date'])
    return actions

def _get_compliance_notifications(companies):
    """Get compliance notifications across all companies"""
    notifications = []
    
    for company in companies:
        # Check for employees without tax numbers
        employees_without_tax = Employee.query.filter_by(company_id=company.id)\
            .filter(Employee.tax_number.is_(None)).count()
        
        if employees_without_tax > 0:
            notifications.append({
                'type': 'warning',
                'company_name': company.name,
                'company_id': company.id,
                'title': 'Missing Tax Numbers',
                'message': f'{employees_without_tax} employee(s) missing tax numbers',
                'action': 'Update Employee Records'
            })
        
        # Check for overdue payroll
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        payroll_done = db.session.query(PayrollEntry)\
            .join(Employee)\
            .filter(Employee.company_id == company.id)\
            .filter(PayrollEntry.pay_period_end >= current_month_start)\
            .count() > 0
        
        employee_count = Employee.query.filter_by(company_id=company.id).count()
        if employee_count > 0 and not payroll_done and datetime.now().day > 25:
            notifications.append({
                'type': 'danger',
                'company_name': company.name,
                'company_id': company.id,
                'title': 'Payroll Overdue',
                'message': 'Monthly payroll not processed',
                'action': 'Process payroll immediately'
            })
        
        # Check for employees without medical aid scheme names
        employees = Employee.query.filter_by(company_id=company.id).all()
        employees_without_medical = sum(
            1 for e in employees if e.medical_aid_member and e.medical_aid_scheme is None
        )
        
        if employees_without_medical > 0:
            notifications.append({
                'type': 'info',
                'company_name': company.name,
                'company_id': company.id,
                'title': 'Medical Aid Details',
                'message': f'{employees_without_medical} employee(s) with medical aid contributions need scheme names',
                'action': 'Update medical aid details'
            })
    
    return notifications

def _get_portfolio_compliance_metrics(companies):
    """Calculate portfolio-wide compliance metrics using dynamic SARS rules"""
    today = datetime.now().date()
    week_from_now = today + timedelta(days=7)
    month_from_now = today + timedelta(days=30)
    
    company_ids = [company.id for company in companies]
    
    try:
        # Generate compliance events for next 30 days using dynamic rules
        events = ComplianceCalendarService.generate_portfolio_compliance_events(
            company_ids, today, month_from_now
        )
        
        overdue_count = 0
        this_week_count = 0
        total_active = len(events)
        compliant_companies = 0
        
        # Count overdue and this week events
        for event in events:
            event_date = datetime.fromisoformat(event['start']).date()
            days_until = (event_date - today).days
            
            if days_until < 0:
                overdue_count += 1
            elif days_until <= 7:
                this_week_count += 1
        
        # Count companies with no overdue events
        company_overdue_map = {}
        for event in events:
            event_date = datetime.fromisoformat(event['start']).date()
            company_id = event.get('company_id')
            
            if company_id not in company_overdue_map:
                company_overdue_map[company_id] = False
            
            if event_date < today:
                company_overdue_map[company_id] = True
        
        compliant_companies = sum(1 for has_overdue in company_overdue_map.values() if not has_overdue)
        
        return {
            'overdue_count': overdue_count,
            'this_week_count': this_week_count,
            'compliant_companies': compliant_companies,
            'total_active': total_active
        }
        
    except Exception as e:
        current_app.logger.error(f"Error calculating portfolio compliance metrics: {str(e)}")
        # Return zero metrics on error
        return {
            'overdue_count': 0,
            'this_week_count': 0,
            'compliant_companies': len(companies),
            'total_active': 0
        }



@accountant_dashboard_bp.route('/calendar-data')
@login_required
def portfolio_calendar_data():
    """API endpoint for filtered calendar data"""

    # Ensure user is an accountant
    if not current_user.is_accountant:
        current_app.logger.warning(f"Non-accountant user {current_user.id} attempted to access calendar data")
        return jsonify({'error': 'Access denied'}), 403

    # Get filter parameters
    company_ids = request.args.getlist('companies')
    categories = request.args.getlist('categories')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    current_app.logger.debug(
        f"/calendar-data params: companies={company_ids}, categories={categories}, "
        f"start={start_date}, end={end_date}"
    )
    
    # Get user's companies
    user_companies = current_user.companies.all()
    user_company_ids = [c.id for c in user_companies]
    
    # Filter by selected companies or use all
    if company_ids:
        # Convert to ints and verify access
        valid_ids = []
        for cid in company_ids:
            try:
                cid_int = int(cid)
            except (TypeError, ValueError):
                continue
            if cid_int in user_company_ids:
                valid_ids.append(cid_int)
        company_ids = valid_ids
    else:
        company_ids = user_company_ids

    # Abort if no valid company ids
    if not company_ids:
        return jsonify([])
    
    # Parse date range for dynamic event generation
    start_parsed = None
    end_parsed = None
    
    if start_date:
        try:
            start_parsed = datetime.fromisoformat(start_date).date()
        except ValueError:
            current_app.logger.warning('Invalid start date: %s', start_date)
    
    if end_date:
        try:
            end_parsed = datetime.fromisoformat(end_date).date()
        except ValueError:
            current_app.logger.warning('Invalid end date: %s', end_date)
    
    # Use default date range if not provided (3 months ahead)
    if not start_parsed:
        start_parsed = datetime.now().date()
    if not end_parsed:
        end_parsed = start_parsed + timedelta(days=90)
    
    # Generate dynamic compliance events using ComplianceCalendarService
    try:
        events = ComplianceCalendarService.get_calendar_events(
            current_user.id, start_parsed, end_parsed
        )
        
        # Filter by categories if specified
        if categories:
            # Map category filters to event properties
            category_map = {
                'tax': ['EMP201', 'EMP501', 'IRP5'],
                'payroll': ['EMP201', 'UIF'],
                'employment': ['SDL'],
                'custom': []  # Custom reminders still from old system
            }
            
            allowed_keywords = []
            for cat in categories:
                if cat in category_map:
                    allowed_keywords.extend(category_map[cat])
            
            if allowed_keywords:
                events = [e for e in events if any(keyword in e['title'] for keyword in allowed_keywords)]
        
        current_app.logger.info(f"Generated {len(events)} dynamic compliance events for calendar")
        
    except Exception as e:
        current_app.logger.error(f"Error generating dynamic compliance events: {str(e)}")
        # Fallback to empty events array
        events = []

    # Debug: print generated events to server logs for troubleshooting
    print("Calendar API Events:", events)
    if events:
        print(f"Sample event: {events[0]}")

    return jsonify(events)