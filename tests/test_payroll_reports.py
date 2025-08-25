from app import db
from app.models import User, Company, Employee, PayrollEntry
from datetime import date
from decimal import Decimal


def login(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def create_setup():
    company = Company(name='ReportCo')
    user = User(email='report@example.com', is_accountant=True)
    user.set_password('password')
    user.companies.append(company)
    db.session.add_all([company, user])
    db.session.commit()

    emp = Employee(
        company_id=company.id,
        employee_id='EMP001',
        first_name='John',
        last_name='Doe',
        id_number='9001014800088',
        cell_number='1234567890',
        physical_address='Addr 1',
        department='IT',
        job_title='Dev',
        start_date=date(2023, 1, 1),
        employment_status='Full-Time',
        salary_type='monthly',
        salary=Decimal('10000.00'),
        bank_name='Bank',
        account_number='12345678',
        account_type='Savings',
    )
    db.session.add(emp)
    db.session.commit()
    return user, company, emp


def create_verified_entry(employee_id):
    entry = PayrollEntry(
        employee_id=employee_id,
        pay_period_start=date(2025, 6, 1),
        pay_period_end=date(2025, 6, 30),
        month_year='2025-06',
        ordinary_hours=Decimal('160'),
        overtime_hours=Decimal('0'),
        sunday_hours=Decimal('0'),
        public_holiday_hours=Decimal('0'),
        hourly_rate=Decimal('50'),
        allowances=Decimal('0'),
        bonus_amount=Decimal('0'),
        deductions_other=Decimal('0'),
        union_fee=Decimal('0'),
        paye=Decimal('0'),
        uif=Decimal('0'),
        sdl=Decimal('0'),
        net_pay=Decimal('10000'),
        is_verified=True,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def test_verified_entry_shows_in_reports(client, app):
    with app.app_context():
        user, company, emp = create_setup()
        create_verified_entry(emp.id)

    login(client, 'report@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.get('/payroll/reports?period=2025-06')
    assert resp.status_code == 200
    assert b'John Doe' in resp.data

