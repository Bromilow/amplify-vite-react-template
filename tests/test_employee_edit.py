from datetime import date
from decimal import Decimal

from app import db
from app.models import User, Company, Employee, Beneficiary, EmployeeRecurringDeduction


def login(client, email, password):
    return client.post(
        '/auth/login',
        data={'email': email, 'password': password},
        follow_redirects=True,
    )


def create_user_and_company():
    company = Company(name='TestCo')
    user = User(email='user@example.com', is_accountant=True)
    user.set_password('password')
    user.companies.append(company)
    db.session.add_all([company, user])
    db.session.commit()
    return user, company


def create_employee_with_deduction(company_id, beneficiary):
    emp = Employee(
        company_id=company_id,
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

    ded = EmployeeRecurringDeduction(
        employee_id=emp.id,
        beneficiary_id=beneficiary.id,
        amount_type='Fixed',
        value=Decimal('100.00'),
        notes='Initial',
    )
    db.session.add(ded)
    db.session.commit()
    return emp


def test_edit_employee_updates_deduction(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        beneficiary = Beneficiary(company_id=company.id, type='Other', name='Test Beneficiary')
        db.session.add(beneficiary)
        db.session.commit()
        employee = create_employee_with_deduction(company.id, beneficiary)

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    response = client.post(
        f'/employees/{employee.id}/edit',
        data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'id_number': '9001014800088',
            'cell_number': '0987654321',
            'physical_address': 'Addr 2',
            'department': 'IT',
            'job_title': 'DevOps',
            'start_date': '2023-01-01',
            'employment_status': 'Full-Time',
            'salary_type': 'monthly',
            'salary': '12000',
            'bank_name': 'Bank',
            'account_number': '87654321',
            'account_type': 'Savings',
            'customize_deductions': 'on',
            'deduction_beneficiary_id[]': str(beneficiary.id),
            'deduction_amount_type[]': 'Fixed',
            'deduction_value[]': '200',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        updated_emp = Employee.query.get(employee.id)
        assert updated_emp.first_name == 'Jane'
        assert updated_emp.cell_number == '0987654321'
        deduction = EmployeeRecurringDeduction.query.filter_by(
            employee_id=employee.id,
            beneficiary_id=beneficiary.id,
            is_active=True,
        ).first()
        assert deduction is not None
        assert deduction.value == Decimal('200')


def test_add_employee_calculated_deduction(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        beneficiary = Beneficiary(company_id=company.id, type='Medical Aid', name='MedAid')
        db.session.add(beneficiary)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    response = client.post(
        '/employees/new',
        data={
            'first_name': 'John',
            'last_name': 'Doe',
            'id_number': '9001014800088',
            'cell_number': '1234567890',
            'physical_address': 'Addr 1',
            'department': 'IT',
            'job_title': 'Dev',
            'start_date': '2023-01-01',
            'employment_status': 'Full-Time',
            'salary_type': 'monthly',
            'salary': '10000',
            'bank_name': 'Bank',
            'account_number': '12345678',
            'account_type': 'Savings',
            'annual_leave_days': '15',
            'customize_deductions': 'on',
            'deduction_beneficiary_id[]': str(beneficiary.id),
            'deduction_amount_type[]': 'Calculated',
            'deduction_value[]': '',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        emp = Employee.query.filter_by(first_name='John', last_name='Doe').first()
        assert emp is not None
        deduction = EmployeeRecurringDeduction.query.filter_by(
            employee_id=emp.id,
            beneficiary_id=beneficiary.id,
            is_active=True,
        ).first()
        assert deduction is not None
        assert deduction.amount_type == 'Calculated'
        assert deduction.value is None
