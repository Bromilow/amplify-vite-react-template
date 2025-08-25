from datetime import date
from decimal import Decimal

from app import db
from app.models import (
    User,
    Company,
    Employee,
    Beneficiary,
    EmployeeRecurringDeduction,
    CompanyDeductionDefault,
)


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


def create_employee(company_id):
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
    return emp


def test_delete_beneficiary_in_use(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        beneficiary = Beneficiary(company_id=company.id, type='Other', name='Test Beneficiary')
        db.session.add(beneficiary)
        db.session.commit()

        # Reference in company defaults and employee deductions
        db.session.add(
            CompanyDeductionDefault(
                company_id=company.id,
                beneficiary_id=beneficiary.id,
                amount=Decimal('10.00'),
            )
        )
        db.session.commit()

        employee = create_employee(company.id)
        ded = EmployeeRecurringDeduction(
            employee_id=employee.id,
            beneficiary_id=beneficiary.id,
            amount_type='Fixed',
            value=Decimal('1.00'),
        )
        db.session.add(ded)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    response = client.post(
        f'/company/{company.id}/beneficiaries/{beneficiary.id}/delete', follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Cannot delete beneficiary' in response.data

    with app.app_context():
        assert Beneficiary.query.get(beneficiary.id) is not None
