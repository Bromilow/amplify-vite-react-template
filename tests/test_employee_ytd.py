from app import db
from app.models import User, Company, Employee, PayrollEntry
from datetime import date
from decimal import Decimal


def login(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def setup_env():
    company = Company(name='YTDCo')
    user = User(email='ytd@example.com', is_accountant=True)
    user.set_password('password')
    user.companies.append(company)
    db.session.add_all([company, user])
    db.session.commit()

    emp = Employee(
        company_id=company.id,
        employee_id='EMP001',
        first_name='Test',
        last_name='User',
        id_number='9001014800088',
        cell_number='1234567890',
        physical_address='Addr',
        department='IT',
        job_title='Dev',
        start_date=date(2025, 3, 1),
        employment_status='Full-Time',
        salary_type='monthly',
        salary=Decimal('10000.00'),
        bank_name='Bank',
        account_number='12345678',
        account_type='Savings',
    )
    db.session.add(emp)
    db.session.commit()

    e1 = PayrollEntry(
        employee_id=emp.id,
        pay_period_start=date(2025, 3, 1),
        pay_period_end=date(2025, 3, 31),
        month_year='2025-03',
        ordinary_hours=Decimal('160'),
        overtime_hours=Decimal('0'),
        sunday_hours=Decimal('0'),
        public_holiday_hours=Decimal('0'),
        hourly_rate=Decimal('50'),
        allowances=Decimal('0'),
        bonus_amount=Decimal('0'),
        deductions_other=Decimal('0'),
        union_fee=Decimal('0'),
        paye=Decimal('100'),
        uif=Decimal('10'),
        sdl=Decimal('10'),
        net_pay=Decimal('9800'),
        is_finalized=True,
    )
    e2 = PayrollEntry(
        employee_id=emp.id,
        pay_period_start=date(2025, 4, 1),
        pay_period_end=date(2025, 4, 30),
        month_year='2025-04',
        ordinary_hours=Decimal('160'),
        overtime_hours=Decimal('0'),
        sunday_hours=Decimal('0'),
        public_holiday_hours=Decimal('0'),
        hourly_rate=Decimal('50'),
        allowances=Decimal('0'),
        bonus_amount=Decimal('0'),
        deductions_other=Decimal('0'),
        union_fee=Decimal('0'),
        paye=Decimal('150'),
        uif=Decimal('10'),
        sdl=Decimal('10'),
        net_pay=Decimal('9750'),
        is_finalized=True,
    )
    db.session.add_all([e1, e2])
    db.session.commit()
    return user, company, emp


def test_ytd_endpoint(client, app):
    with app.app_context():
        user, company, emp = setup_env()

    login(client, 'ytd@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.get(f'/employees/api/employees/{emp.id}/payroll-ytd')
    assert resp.status_code == 200
    data = resp.get_json()
    assert round(data['gross_pay_ytd'], 2) == 20000.0
    assert round(data['paye_ytd'], 2) == 250.0
    assert round(data['uif_ytd'], 2) == 20.0
    assert round(data['sdl_ytd'], 2) == 20.0
    assert round(data['net_pay_ytd'], 2) == 19550.0
