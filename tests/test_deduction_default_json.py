import pytest
from decimal import Decimal
from app import db
from app.models import User, Company, Beneficiary, CompanyDeductionDefault


def login(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def create_user_and_company():
    company = Company(name='TestCo')
    user = User(email='user@example.com', is_accountant=True)
    user.set_password('password')
    user.companies.append(company)
    db.session.add_all([company, user])
    db.session.commit()
    return user, company


def test_deduction_default_json_endpoint(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        beneficiary = Beneficiary(company_id=company.id, type='Other', name='Test Beneficiary')
        db.session.add(beneficiary)
        db.session.commit()
        default = CompanyDeductionDefault(company_id=company.id, beneficiary_id=beneficiary.id, amount=Decimal('50.00'), amount_type='fixed')
        db.session.add(default)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.get(f'/company/recurring-deductions/{default.id}/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['id'] == default.id
    assert data['beneficiary_id'] == beneficiary.id
    assert data['amount'] == float(default.amount)


def test_deduction_default_json_calculated(client, app):
    """Ensure endpoint returns fields for calculated deductions"""
    with app.app_context():
        user, company = create_user_and_company()
        beneficiary = Beneficiary(company_id=company.id, type='Medical Aid', name='MedAid')
        db.session.add(beneficiary)
        db.session.commit()
        default = CompanyDeductionDefault(
            company_id=company.id,
            beneficiary_id=beneficiary.id,
            amount=None,
            amount_type='calculated',
        )
        db.session.add(default)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.get(f'/company/recurring-deductions/{default.id}/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['id'] == default.id
    assert data['beneficiary_id'] == beneficiary.id
    assert data['amount'] is None
    assert data['amount_type'] == 'calculated'
