from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required
from app.models import Company, Employee, PayrollEntry, Beneficiary, EmployeeRecurringDeduction
from app import db
from sqlalchemy import func, desc
from datetime import date, datetime, timedelta
import calendar
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def reports_dashboard():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('dashboard.overview'))

    company = Company.query.get_or_404(selected_company_id)
    
    # Report and filter selections
    selected_report = request.args.get('report')
    period = request.args.get('period')
    selected_employee = request.args.get('employee')
    
    payroll_entries = []
    if period:
        query = db.session.query(PayrollEntry)\
            .join(Employee)\
            .filter(Employee.company_id == selected_company_id)\
            .filter(PayrollEntry.is_verified == True)

        query = query.filter(PayrollEntry.month_year == period)
        if selected_employee:
            query = query.filter(PayrollEntry.employee_id == int(selected_employee))

        payroll_entries = query.order_by(Employee.first_name, Employee.last_name).all()
    
    # Get all employees for the company
    employees = Employee.query.filter_by(company_id=selected_company_id).all()
    
    # Get all beneficiaries for the company
    beneficiaries = Beneficiary.query.filter_by(company_id=selected_company_id).all()
    
    # Calculate beneficiary payment totals for current period
    beneficiary_totals = {}
    for entry in payroll_entries:
        deductions = EmployeeRecurringDeduction.query.filter_by(
            employee_id=entry.employee_id,
            is_active=True
        ).all()
        
        for deduction in deductions:
            if deduction.beneficiary_id:
                beneficiary_name = deduction.beneficiary.name
                if beneficiary_name not in beneficiary_totals:
                    beneficiary_totals[beneficiary_name] = {
                        'total': 0,
                        'type': deduction.beneficiary.type,
                        'beneficiary_id': deduction.beneficiary_id
                    }
                
                if deduction.amount_type == 'fixed':
                    beneficiary_totals[beneficiary_name]['total'] += deduction.value or 0
                elif deduction.amount_type == 'percent':
                    beneficiary_totals[beneficiary_name]['total'] += (entry.gross_pay * (deduction.value or 0) / 100)
    
    # Get available periods (months with payroll data)
    available_periods = db.session.query(PayrollEntry.month_year)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.is_verified == True)\
        .distinct()\
        .order_by(desc(PayrollEntry.month_year))\
        .all()
    
    periods = [period[0] for period in available_periods if period[0]]
    
    return render_template(
        'reports/index.html',
        company=company,
        current_company_id=selected_company_id,
        payroll_entries=payroll_entries,
        employees=employees,
        beneficiaries=beneficiaries,
        beneficiary_totals=beneficiary_totals,
        current_period=period,
        available_periods=periods,
        selected_report=selected_report,
        selected_employee=selected_employee,
        date=date,
    )

@reports_bp.route('/export/payroll.csv')
@login_required
def export_payroll_csv():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))

    period = request.args.get('period')
    
    query = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.is_verified == True)
    
    if period:
        query = query.filter(PayrollEntry.month_year == period)
    
    entries = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Employee ID', 'Employee Name', 'Gross Pay', 'PAYE', 'UIF', 'SDL', 
                     'Other Deductions', 'Net Pay', 'Period', 'Status'])
    
    # Write data
    for entry in entries:
        writer.writerow([
            entry.employee.employee_id,
            f"{entry.employee.first_name} {entry.employee.last_name}",
            entry.gross_pay,
            entry.paye,
            entry.uif,
            entry.sdl,
            (entry.deductions_other or 0) + (entry.union_fee or 0),
            entry.net_pay,
            entry.month_year or entry.pay_period_start.strftime('%Y-%m'),
            'Finalized' if entry.is_finalized else 'Verified'
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=payroll_summary_{period or "all"}.csv'
    
    return response

@reports_bp.route('/export/leave.csv')
@login_required
def export_leave_csv():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))

    company = Company.query.get_or_404(selected_company_id)
    employees = Employee.query.filter_by(company_id=selected_company_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Employee ID', 'Employee Name', 'Annual Leave Days', 'Sick Leave Days', 
                     'Hire Date', 'Service Period (Years)'])
    
    # Write data
    for employee in employees:
        service_years = 0
        if employee.start_date:
            service_days = (date.today() - employee.start_date).days
            service_years = round(service_days / 365, 1)
        
        writer.writerow([
            employee.employee_id,
            f"{employee.first_name} {employee.last_name}",
            employee.annual_leave_days or company.default_annual_leave_days or 15,
            employee.sick_leave_days or company.default_sick_leave_days or 10,
            employee.start_date.strftime('%Y-%m-%d') if employee.start_date else 'N/A',
            service_years
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=leave_summary.csv'
    
    return response

@reports_bp.route('/export/deductions.csv')
@login_required
def export_deductions_csv():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))

    employees = Employee.query.filter_by(company_id=selected_company_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Employee ID', 'Employee Name', 'Beneficiary', 'Deduction Type', 
                     'Amount Type', 'Amount', 'Status'])
    
    # Write data
    for employee in employees:
        for deduction in employee.recurring_deductions:
            if deduction.is_active:
                amount_display = ''
                if deduction.amount_type == 'fixed':
                    amount_display = f"R{deduction.value or 0:.2f}"
                elif deduction.amount_type == 'percent':
                    amount_display = f"{deduction.value or 0}%"
                else:
                    amount_display = 'Calculated'
                
                writer.writerow([
                    employee.employee_id,
                    f"{employee.first_name} {employee.last_name}",
                    deduction.beneficiary.name if deduction.beneficiary else 'N/A',
                    deduction.beneficiary.type if deduction.beneficiary else 'Other',
                    deduction.amount_type.title(),
                    amount_display,
                    'Active'
                ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=recurring_deductions.csv'
    
    return response

@reports_bp.route('/export/employee_status.csv')
@login_required
def export_employee_status_csv():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))

    employees = Employee.query.filter_by(company_id=selected_company_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Employee ID', 'Employee Name', 'Status', 'UIF Contribution', 
                     'Hire Date', 'Employment Type'])
    
    # Write data
    for employee in employees:
        writer.writerow([
            employee.employee_id,
            f"{employee.first_name} {employee.last_name}",
            'Active' if not employee.end_date else 'Inactive',
            'Contributing' if employee.uif_contributing else 'Exempt',
            employee.start_date.strftime('%Y-%m-%d') if employee.start_date else 'N/A',
            employee.employment_type or 'Full-time'
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=employee_status.csv'
    
    return response

@reports_bp.route('/export/beneficiary.csv')
@login_required
def export_beneficiary_csv():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))

    period = request.args.get('period')
    
    # Get payroll entries for the period
    query = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.is_verified == True)
    
    if period:
        query = query.filter(PayrollEntry.month_year == period)
    
    payroll_entries = query.all()
    
    # Calculate beneficiary totals
    beneficiary_totals = {}
    for entry in payroll_entries:
        deductions = EmployeeRecurringDeduction.query.filter_by(
            employee_id=entry.employee_id,
            is_active=True
        ).all()
        
        for deduction in deductions:
            if deduction.beneficiary_id:
                beneficiary_name = deduction.beneficiary.name
                if beneficiary_name not in beneficiary_totals:
                    beneficiary_totals[beneficiary_name] = {
                        'total': 0,
                        'type': deduction.beneficiary.type,
                        'beneficiary': deduction.beneficiary
                    }
                
                if deduction.amount_type == 'fixed':
                    beneficiary_totals[beneficiary_name]['total'] += deduction.value or 0
                elif deduction.amount_type == 'percent':
                    beneficiary_totals[beneficiary_name]['total'] += (entry.gross_pay * (deduction.value or 0) / 100)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Beneficiary Name', 'Type', 'Total Amount', 'Bank Name', 
                     'Account Number', 'EFT Export Enabled'])
    
    # Write data
    for name, data in beneficiary_totals.items():
        beneficiary = data['beneficiary']
        writer.writerow([
            name,
            data['type'],
            f"R{data['total']:.2f}",
            beneficiary.bank_name or 'N/A',
            beneficiary.account_number or 'N/A',
            'Yes' if beneficiary.include_in_eft_export else 'No'
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=beneficiary_payments_{period or "all"}.csv'
    
    return response

@reports_bp.route('/export/eft_file')
@login_required
def generate_eft_file():
    selected_company_id = session.get('selected_company_id')
    if not selected_company_id:
        flash('Please select a company.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))

    period = request.args.get('period')
    
    query = db.session.query(PayrollEntry)\
        .join(Employee)\
        .filter(Employee.company_id == selected_company_id)\
        .filter(PayrollEntry.is_verified == True)\
        .filter(Employee.bank_name.isnot(None))\
        .filter(Employee.account_number.isnot(None))
    
    if period:
        query = query.filter(PayrollEntry.month_year == period)
    
    entries = query.all()
    
    if not entries:
        flash('No EFT-eligible employees found for the selected period.', 'warning')
        return redirect(url_for('reports.reports_dashboard'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header for EFT file
    writer.writerow(['Employee Name', 'Bank Name', 'Account Number', 'Branch Code', 
                     'Account Type', 'Amount', 'Reference', 'Email'])
    
    # Write employee payment data
    for entry in entries:
        employee = entry.employee
        reference = f"SAL-{employee.employee_id}-{entry.month_year or entry.pay_period_start.strftime('%Y%m')}"
        
        writer.writerow([
            f"{employee.first_name} {employee.last_name}",
            employee.bank_name,
            employee.account_number,
            employee.branch_code or '',
            employee.account_type or 'Savings',
            entry.net_pay,
            reference,
            employee.email or ''
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=eft_file_{period or "all"}_{date.today().strftime("%Y%m%d")}.csv'
    
    return response