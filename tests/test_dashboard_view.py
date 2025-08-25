import pytest
from app import db
from app.models import User, Company


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


def test_dashboard_overview_renders(client, app):
    with app.app_context():
        user, company = create_user_and_company()

    login(client, 'user@example.com', 'password')
    with client.session_transaction() as sess:
        sess['selected_company_id'] = company.id

    resp = client.get('/dashboard/overview')
    assert resp.status_code == 200

    # Check for card IDs and titles
    html = resp.get_data(as_text=True)
    assert 'id="dashboard-company-snapshot"' in html
    assert 'Company Snapshot' in html
    assert 'id="dashboard-payroll-progress"' in html
    assert 'Payroll Progress Tracker' in html
    assert 'id="dashboard-upcoming-events"' in html
    assert 'Upcoming Events' in html
    assert 'id="dashboard-calendar"' in html
    assert 'Company Calendar' in html
    assert 'Next Pay Day' in html
    assert 'id="dashboard-leave-summary"' in html
    assert 'Leave Summary' in html
    assert 'id="dashboard-deduction-overview"' in html
    assert 'Deduction Overview' in html
    assert 'Total Active Deductions' in html
    assert 'id="dashboard-department-breakdown"' in html
    assert 'Department Breakdown' in html
    assert 'id="dashboard-gpt-assistant"' in html
    assert 'Ask the Assistant' in html
    assert 'id="dashboard-activity-feed"' in html
    assert 'Recent Activity Feed' in html
