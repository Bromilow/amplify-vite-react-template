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


def test_create_calculated_non_medical_aid_rejected(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        ben = Beneficiary(company_id=company.id, type='Pension Fund', name='Fund')
        db.session.add(ben)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.post(
        f'/company/{company.id}/deduction-defaults',
        data={'beneficiary_id': ben.id, 'amount_type': 'calculated'},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b'only allowed for Medical Aid beneficiaries' in resp.data
    with app.app_context():
        assert CompanyDeductionDefault.query.count() == 0


def test_update_to_calculated_non_medical_aid_rejected(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        ben = Beneficiary(company_id=company.id, type='Other', name='Benef')
        db.session.add(ben)
        db.session.commit()
        default = CompanyDeductionDefault(
            company_id=company.id,
            beneficiary_id=ben.id,
            amount=Decimal('10.00'),
            amount_type='fixed',
        )
        db.session.add(default)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.post(
        f'/company/{company.id}/deduction-defaults/{default.id}',
        data={'amount_type': 'calculated'},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b'only allowed for Medical Aid beneficiaries' in resp.data
    with app.app_context():
        updated = CompanyDeductionDefault.query.get(default.id)
        assert updated.amount_type == 'fixed'
        assert updated.amount == Decimal('10.00')


def test_create_calculated_medical_aid_success(client, app):
    """Medical Aid beneficiaries can use calculated amount type"""
    with app.app_context():
        user, company = create_user_and_company()
        ben = Beneficiary(company_id=company.id, type='Medical Aid', name='Med')
        db.session.add(ben)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.post(
        f'/company/{company.id}/deduction-defaults',
        data={'beneficiary_id': ben.id, 'amount_type': 'calculated'},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        default = CompanyDeductionDefault.query.first()
        assert default.amount_type == 'calculated'
        assert default.amount is None


def test_update_calculated_medical_aid_success(client, app):
    with app.app_context():
        user, company = create_user_and_company()
        ben = Beneficiary(company_id=company.id, type='Medical Aid', name='Med')
        db.session.add(ben)
        db.session.commit()
        default = CompanyDeductionDefault(
            company_id=company.id,
            beneficiary_id=ben.id,
            amount=Decimal('10.00'),
            amount_type='fixed',
        )
        db.session.add(default)
        db.session.commit()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.post(
        f'/company/{company.id}/deduction-defaults/{default.id}',
        data={'amount_type': 'calculated'},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        updated = CompanyDeductionDefault.query.get(default.id)
        assert updated.amount_type == 'calculated'
        assert updated.amount is None
