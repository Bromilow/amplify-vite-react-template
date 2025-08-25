from flask import Blueprint, render_template, request, flash, redirect, url_for, make_response, abort, session, jsonify, send_file
from flask_login import login_required, current_user
from app.models import Employee, PayrollEntry, Company
from app.models.employee_recurring_deduction import EmployeeRecurringDeduction
from app import db
from datetime import datetime, date, timedelta
import io
import zipfile
from decimal import Decimal
from sqlalchemy import func, desc
import calendar

# Import WeasyPrint conditionally to handle system dependencies
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    print(f"WeasyPrint not available: {e}")
    WEASYPRINT_AVAILABLE = False
    HTML = None

# Create payroll blueprint
payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')

def calculate_employee_recurring_deductions(employee_id, gross_salary):
    """Calculate recurring deductions for an employee based on EmployeeRecurringDeduction records"""
    deductions = EmployeeRecurringDeduction.query.filter_by(
        employee_id=employee_id, 
        is_active=True
    ).all()
    
    total_medical_aid = Decimal('0')
    total_union = Decimal('0')
    total_other = Decimal('0')
    
    for deduction in deductions:
        amount = deduction.calculate_deduction_amount(gross_salary)
        
        # Categorize by beneficiary type
        if deduction.beneficiary.type == 'Medical Aid':
            total_medical_aid += amount
        elif deduction.beneficiary.type == 'Union':
            total_union += amount
        else:
            total_other += amount
    
    return {
        'medical_aid': total_medical_aid,
        'union': total_union,
        'other': total_other,
        'total': total_medical_aid + total_union + total_other
    }

@payroll_bp.route('/')
@login_required
def index():
    """Payroll dashboard with overview of payroll data"""
    
    # Get selected company from session
    selected_company_id = session.get('selected_company_id')
    
    # Redirect to company selection if no company is selected
    if not selected_company_id:
        flash('Please select a company to view payroll.', 'warning')
        if current_user.is_accountant:
            return redirect(url_for('accountant_dashboard.dashboard'))
        else:
            return redirect(url_for('dashboard.overview'))
    
    # Get company details
    company = Company.query.get(selected_company_id)
    if not company:
        flash('Selected company not found.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    # Get company-scoped employees
    company_employees = Employee.query.filter_by(company_id=selected_company_id).all()
    
    # Calculate payroll statistics for company
    total_employees = len(company_employees)
    salaried_employees = [emp for emp in company_employees if emp.salary_type == 'monthly']
    hourly_employees = [emp for emp in company_employees if emp.salary_type == 'hourly']
    
    total_monthly_payroll = sum(emp.monthly_salary for emp in company_employees)
    total_salaried_payroll = sum(emp.monthly_salary for emp in salaried_employees)
    total_hourly_payroll = sum(emp.monthly_salary for emp in hourly_employees)
    
    # Get current payroll period
    today = date.today()
    current_month_start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    current_month_end = today.replace(day=last_day)
    
    # Check if payroll has been processed this month
    payroll_processed = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.pay_period_start >= current_month_start)\
        .count() > 0
    
    payroll_status = "Completed" if payroll_processed else "Pending"
    
    stats = {
        'total_employees': total_employees,
        'salaried_employees': len(salaried_employees),
        'hourly_employees': len(hourly_employees),
        'total_monthly_payroll': float(total_monthly_payroll),
        'total_salaried_payroll': float(total_salaried_payroll),
        'total_hourly_payroll': float(total_hourly_payroll),
        'payroll_status': payroll_status,
        'current_period_start': current_month_start,
        'current_period_end': current_month_end
    }
    
    # Get verification status for each employee for current period
    employee_verification_status = {}
    for employee in company_employees:
        payroll_entry = PayrollEntry.query.filter_by(
            employee_id=employee.id,
            pay_period_start=current_month_start,
            pay_period_end=current_month_end
        ).first()
        employee_verification_status[employee.id] = {
            'is_verified': payroll_entry.is_verified if payroll_entry else False,
            'has_entry': payroll_entry is not None
        }
    
    return render_template('payroll/index.html',
                         stats=stats,
                         employees=company_employees,
                         company=company,
                         employee_verification_status=employee_verification_status)



@payroll_bp.route('/process', methods=['POST'])
@login_required
def process():
    """Process payroll for selected period"""
    
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'error')
        return redirect(url_for('payroll.index'))
    
    # Get period dates from form
    period_start_str = request.form.get('period_start')
    period_end_str = request.form.get('period_end')
    
    if not period_start_str or not period_end_str:
        flash('Please provide both start and end dates.', 'error')
        return redirect(url_for('payroll.new'))
    
    period_start = datetime.strptime(period_start_str, '%Y-%m-%d').date()
    period_end = datetime.strptime(period_end_str, '%Y-%m-%d').date()
    
    # Get company employees
    employees = Employee.query.filter_by(company_id=selected_company_id).all()
    
    try:
        processed_count = 0
        for employee in employees:
            # Check if payroll entry already exists for this period
            existing_entry = PayrollEntry.query.filter_by(
                employee_id=employee.id,
                pay_period_start=period_start,
                pay_period_end=period_end
            ).first()

            if not existing_entry:
                # Create new payroll entry with default values
                payroll_entry = PayrollEntry()
                payroll_entry.employee_id = employee.id
                payroll_entry.pay_period_start = period_start
                payroll_entry.pay_period_end = period_end
                payroll_entry.month_year = datetime.now().strftime('%Y-%m')
        
                if employee.salary_type == 'daily':
                    payroll_entry.ordinary_hours = Decimal('0')
                    payroll_entry.hourly_rate = employee.salary / (employee.ordinary_hours_per_day or 8)
                else:
                    payroll_entry.ordinary_hours = Decimal(str((employee.ordinary_hours_per_day or 8) * (employee.work_days_per_month or 22)))
                    payroll_entry.hourly_rate = employee.salary if employee.salary_type == 'hourly' else employee.salary / ((employee.ordinary_hours_per_day or 8) * (employee.work_days_per_month or 22))
                payroll_entry.overtime_hours = Decimal('0.00')
                payroll_entry.sunday_hours = Decimal('0.00')
                payroll_entry.public_holiday_hours = Decimal('0.00')
        
                payroll_entry.allowances = Decimal('0.00')
                payroll_entry.deductions_other = Decimal('0.00')
                payroll_entry.union_fee = Decimal('0.00')
                
                # Calculate statutory deductions
                gross_pay = payroll_entry.gross_pay
                payroll_entry.paye = gross_pay * Decimal('0.18')  # Simplified PAYE calculation
                
                # UIF: Dynamic rate of gross pay, with dynamic caps
                from app.services.sars_service import SARSService
                sars_config = SARSService.get_company_sars_config(company_id)
                
                uif_eligible_salary = min(gross_pay, Decimal(str(sars_config['uif_salary_cap'])))
                uif_amount = uif_eligible_salary * Decimal(str(sars_config['uif_percent']))
                payroll_entry.uif = min(uif_amount, Decimal(str(sars_config['uif_monthly_cap'])))
                
                payroll_entry.sdl = gross_pay * Decimal(str(sars_config['sdl_percent']))  # SDL
                
                # Calculate net pay
                payroll_entry.net_pay = gross_pay - payroll_entry.total_deductions
                
                db.session.add(payroll_entry)
                processed_count += 1
            else:
                if not existing_entry.month_year:
                    existing_entry.month_year = datetime.now().strftime('%Y-%m')
        
        db.session.commit()
        flash('Payroll processed successfully. View the summary below.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing payroll: {str(e)}', 'error')
        return redirect(url_for('payroll.index'))
    
    return redirect(url_for('payroll.reports'))



@payroll_bp.route('/payslips')
@login_required
def payslips():
    """Generate payslips for current period"""
    
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('payroll.index'))
    
    # Get current period
    today = date.today()
    period_start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    period_end = today.replace(day=last_day)
    
    # Get payroll entries for current period
    payroll_entries = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.pay_period_start >= period_start)\
        .all()
    
    return render_template('payroll/payslips.html',
                         payroll_entries=payroll_entries,
                         period_start=period_start,
                         period_end=period_end)

@payroll_bp.route('/reports/dashboard')
@login_required
def reports_dashboard():
    """Combined payroll reports and history"""
    
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('payroll.index'))
    
    # Get current month data
    today = date.today()
    month_start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    month_end = today.replace(day=last_day)
    
    # Get current month payroll entries
    current_entries = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.pay_period_start >= month_start)\
        .filter(PayrollEntry.pay_period_end <= month_end)\
        .all()
    
    # Calculate current period totals
    current_totals = {
        'gross_pay': sum(entry.gross_pay for entry in current_entries),
        'paye': sum(entry.paye for entry in current_entries),
        'uif': sum(entry.uif for entry in current_entries),
        'sdl': sum(entry.sdl for entry in current_entries),
        'other_deductions': sum((entry.deductions_other + entry.union_fee) for entry in current_entries),
        'net_pay': sum(entry.net_pay for entry in current_entries)
    }
    
    # Get historical payroll data grouped by month (excluding current month)
    historical_data = db.session.query(
        func.date_trunc('month', PayrollEntry.pay_period_start).label('period'),
        func.count(PayrollEntry.id).label('employee_count'),
        func.sum((PayrollEntry.ordinary_hours * PayrollEntry.hourly_rate) + PayrollEntry.allowances).label('gross_pay'),
        func.sum(PayrollEntry.paye).label('paye'),
        func.sum(PayrollEntry.uif).label('uif'),
        func.sum(PayrollEntry.sdl).label('sdl'),
        func.sum(PayrollEntry.deductions_other + PayrollEntry.union_fee).label('other_deductions'),
        func.sum(PayrollEntry.net_pay).label('net_pay')
    )\
    .join(Employee)\
    .filter(Employee.company_id == selected_company_id)\
    .filter(PayrollEntry.pay_period_start < month_start)\
    .group_by(func.date_trunc('month', PayrollEntry.pay_period_start))\
    .order_by(desc(func.date_trunc('month', PayrollEntry.pay_period_start)))\
    .limit(12)\
    .all()
    
    # Get detailed entries for historical periods (for expandable sections)
    historical_entries = {}
    for period_data in historical_data:
        period_start = period_data.period.date()
        period_end = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        entries = db.session.query(PayrollEntry)\
            .join(Employee)\
            .filter(Employee.company_id == selected_company_id)\
            .filter(PayrollEntry.pay_period_start >= period_start)\
            .filter(PayrollEntry.pay_period_end <= period_end)\
            .all()
        
        historical_entries[period_start.strftime('%Y-%m')] = entries
    
    report_data = {
        'current_period': {
            'start': month_start,
            'end': month_end,
            'entries': current_entries,
            'totals': current_totals,
            'employee_count': len(current_entries)
        },
        'historical_data': historical_data,
        'historical_entries': historical_entries
    }
    
    return render_template('payroll/reports.html',
                         report_data=report_data,
                         current_date=date.today())



@payroll_bp.route('/save-entry', methods=['POST'])
@login_required
def save_entry():
    """Save payroll entry and mark as verified"""
    
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        return jsonify({'success': False, 'message': 'No company selected'}), 400
    
    try:
        employee_id = request.form.get('employee_id')
        employee = Employee.query.filter_by(id=employee_id, company_id=selected_company_id).first()
        
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
        # Get period dates
        period_start_str = request.form.get('period_start')
        period_end_str = request.form.get('period_end')
        
        if not period_start_str or not period_end_str:
            return jsonify({'success': False, 'message': 'Period dates required'}), 400
        
        period_start = datetime.strptime(period_start_str, '%Y-%m-%d').date()
        period_end = datetime.strptime(period_end_str, '%Y-%m-%d').date()
        
        # Check if entry already exists
        existing_entry = PayrollEntry.query.filter_by(
            employee_id=employee_id,
            pay_period_start=period_start,
            pay_period_end=period_end
        ).first()
        
        if existing_entry:
            payroll_entry = existing_entry
            if not payroll_entry.month_year:
                payroll_entry.month_year = datetime.now().strftime('%Y-%m')
        else:
            payroll_entry = PayrollEntry()
            payroll_entry.employee_id = employee_id
            payroll_entry.pay_period_start = period_start
            payroll_entry.pay_period_end = period_end
            payroll_entry.month_year = datetime.now().strftime('%Y-%m')
        
        # Update payroll entry fields
        payroll_entry.ordinary_hours = Decimal(request.form.get('ordinary_hours', '0'))
        payroll_entry.overtime_hours = Decimal(request.form.get('overtime_hours', '0'))
        payroll_entry.sunday_hours = Decimal(request.form.get('sunday_hours', '0'))
        payroll_entry.public_holiday_hours = Decimal(request.form.get('public_holiday_hours', '0'))
        payroll_entry.allowances = Decimal(request.form.get('allowances', '0'))
        payroll_entry.bonus_amount = Decimal(request.form.get('bonus_amount', '0'))
        payroll_entry.deductions_other = Decimal('0')
        
        # Handle piece work fields
        if employee.salary_type == 'piece':
            pieces_produced = Decimal(request.form.get('pieces_produced', '0'))
            piece_rate = employee.piece_rate or Decimal('0')
            
            # Validate piece work data
            if pieces_produced <= 0:
                return jsonify({'success': False, 'message': 'Units produced must be greater than 0 for piece work employees'}), 400
            if piece_rate <= 0:
                return jsonify({'success': False, 'message': 'Piece rate must be greater than 0 for piece work employees'}), 400
            
            payroll_entry.pieces_produced = pieces_produced
            payroll_entry.piece_rate = piece_rate
            # For piece work, hourly rate is not used in calculations
            payroll_entry.hourly_rate = Decimal('0')
        else:
            # Calculate hourly rate for time-based employees
            if employee.salary_type == 'hourly':
                payroll_entry.hourly_rate = employee.salary
            elif employee.salary_type == 'daily':
                payroll_entry.hourly_rate = employee.salary / (employee.ordinary_hours_per_day or 8)
            else:
                payroll_entry.hourly_rate = employee.salary / ((employee.ordinary_hours_per_day or 8) * (employee.work_days_per_month or 22))
        
        # Calculate gross pay for deduction calculations
        gross_pay = payroll_entry.gross_pay
        
        # Calculate recurring deductions from EmployeeRecurringDeduction system
        recurring_deductions = calculate_employee_recurring_deductions(employee_id, gross_pay)
        payroll_entry.union_fee = recurring_deductions['union']
        
        # Calculate statutory deductions (UIF, SDL, PAYE)
        if employee.paye_exempt:
            payroll_entry.paye = Decimal('0')
        else:
            payroll_entry.paye = gross_pay * Decimal('0.18')
        # UIF and SDL with dynamic SARS configuration
        from app.services.sars_service import SARSService
        sars_config = SARSService.get_company_sars_config(selected_company_id)
        
        uif_amount = gross_pay * Decimal(str(sars_config['uif_percent']))
        payroll_entry.uif = min(uif_amount, Decimal(str(sars_config['uif_monthly_cap'])))  # UIF with dynamic cap
        payroll_entry.sdl = gross_pay * Decimal(str(sars_config['sdl_percent']))  # SDL
        
        # Calculate medical aid components if employee has medical aid
        if employee.medical_aid_member and employee.medical_aid_dependants is not None:
            payroll_entry.medical_aid_tax_credit = payroll_entry.calculate_medical_tax_credit(
                employee.medical_aid_dependants
            )
            # Fringe benefit still comes from Employee model (employer contribution)
            payroll_entry.fringe_benefit_medical = employee.medical_aid_employer or Decimal('0')
        
        # Calculate net pay
        payroll_entry.net_pay = gross_pay - payroll_entry.total_deductions
        
        # Mark as verified when saved
        payroll_entry.is_verified = True
        payroll_entry.verified_at = datetime.utcnow()
        payroll_entry.verified_by = current_user.id
        
        if not existing_entry:
            db.session.add(payroll_entry)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payroll entry saved and verified successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@payroll_bp.route('/payslip/<int:employee_id>')
@login_required
def generate_payslip(employee_id):
    """Generate BCEA-compliant PDF payslip for employee using actual payroll data"""
    
    if not WEASYPRINT_AVAILABLE:
        flash('PDF generation is not available. WeasyPrint dependencies are missing.', 'error')
        return redirect(url_for('payroll.index'))
    
    from app.models.employee import Employee
    from app.models.payroll_entry import PayrollEntry
    from app.models.company import Company
    
    # Get employee and verify access
    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404)
    
    # Verify user has access to this employee's company
    if not current_user.has_company_access(employee.company_id):
        abort(403)
    
    # Get the most recent payroll entry for this employee
    entry = PayrollEntry.query.filter_by(employee_id=employee_id)\
                             .order_by(PayrollEntry.pay_period_end.desc())\
                             .first()
    
    if not entry:
        flash('No payroll data found for this employee. Please process payroll first.', 'error')
        return redirect(url_for('payroll.index'))
    
    # Get company data
    company = Company.query.get(employee.company_id)
    if not company:
        abort(404)
    
    # Render the payslip template with actual payroll data
    html = render_template("payslip.html", 
                          employee=employee,
                          entry=entry,
                          company=company,
                          current_date=datetime.now())

    # Generate PDF
    try:
        if not WEASYPRINT_AVAILABLE:
            flash('PDF generation is not available. System dependencies are missing.', 'error')
            return redirect(url_for('payroll.index'))
        
        pdf = HTML(string=html).write_pdf()
        
        # Create filename with employee name and pay period
        employee_name_clean = employee.full_name.replace(' ', '_').replace('.', '').replace(',', '')
        pay_period_str = entry.pay_period_end.strftime("%B%Y")
        filename = f'payslip_{employee_name_clean}_{pay_period_str}.pdf'
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        return response
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('payroll.index'))
@payroll_bp.route('/payslips/download')
@login_required
def download_payslips():
    ids = request.args.get('ids', '').split(',')

    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('payroll.index'))

    entries = PayrollEntry.query.filter(
        PayrollEntry.id.in_(ids),
        PayrollEntry.employee.has(company_id=selected_company_id),
        PayrollEntry.is_finalized == True
    ).all()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for entry in entries:
            company = entry.employee.company
            html = render_template('payslip.html',
                                   employee=entry.employee,
                                   entry=entry,
                                   company=company,
                                   current_date=datetime.now())
            pdf = HTML(string=html).write_pdf()
            filename = f"{entry.employee.full_name}_Payslip_{entry.month_year}.pdf".replace(" ", "_")
            zip_file.writestr(filename, pdf)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='payslips.zip'
    )

@payroll_bp.route('/eft/download')
@login_required
def generate_eft_file():
    ids = request.args.get('ids', '').split(',')
    return "EFT file generation coming soon", 501

@payroll_bp.route('/reports', endpoint='reports')
@login_required
def reports_and_exports():
    period = request.args.get('period')

    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('payroll.index'))

    query = PayrollEntry.query.join(Employee).filter(
        Employee.company_id == selected_company_id,
        PayrollEntry.is_verified == True
    )

    if period:
        query = query.filter(PayrollEntry.month_year == period)

    payroll_entries = query.all()
    print(
        f"Loaded {len(payroll_entries)} entries for company {selected_company_id} and period {period}"
    )

    return render_template('payroll/reports.html', payroll_entries=payroll_entries)


@payroll_bp.route('/bulk-actions', methods=['POST'])
@login_required
def bulk_actions():
    entry_ids = request.form.getlist('entry_ids')
    action = request.form.get('action')
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('payroll.reports'))

    entries = PayrollEntry.query.filter(
        PayrollEntry.id.in_(entry_ids),
        PayrollEntry.employee.has(company_id=selected_company_id)
    ).all()

    if action == 'finalize':
        for entry in entries:
            entry.is_finalized = True
        db.session.commit()
        flash(f'{len(entries)} entries finalized.', 'success')

    elif action == 'payslips':
        return redirect(url_for('payroll.download_payslips', ids=",".join(entry_ids)))
    elif action == 'eft':
        return redirect(url_for('payroll.generate_eft_file', ids=",".join(entry_ids)))
    return redirect(url_for('payroll.reports'))
