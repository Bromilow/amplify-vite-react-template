from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import ComplianceReminder, Company
from app import db
from datetime import datetime, date
import json

# Create reminders blueprint
reminders_bp = Blueprint('reminders', __name__, url_prefix='/reminders')

@reminders_bp.route('/')
@login_required
def index():
    """Compliance Reminders management page"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id:
        flash('Please select a company to manage reminders.', 'warning')
        return redirect(url_for('dashboard.overview'))
    
    # Verify user has access to this company
    if not current_user.has_company_access(selected_company_id):
        flash('Access denied to this company.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    company = Company.query.get(selected_company_id)
    if not company:
        flash('Company not found.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    # Get filter parameters
    category_filter = request.args.get('category', 'all')
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = ComplianceReminder.query.filter_by(company_id=selected_company_id)
    
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'overdue':
        query = query.filter(
            ComplianceReminder.is_active == True,
            ComplianceReminder.due_date < date.today()
        )
    elif status_filter == 'upcoming':
        from datetime import timedelta
        next_week = date.today() + timedelta(days=7)
        query = query.filter(
            ComplianceReminder.is_active == True,
            ComplianceReminder.due_date >= date.today(),
            ComplianceReminder.due_date <= next_week
        )
    
    reminders = query.order_by(ComplianceReminder.due_date.asc()).all()
    
    # Get category counts for filter badges
    category_counts = {
        'all': ComplianceReminder.query.filter_by(company_id=selected_company_id, is_active=True).count(),
        'tax': ComplianceReminder.query.filter_by(company_id=selected_company_id, category='tax', is_active=True).count(),
        'payroll': ComplianceReminder.query.filter_by(company_id=selected_company_id, category='payroll', is_active=True).count(),
        'employment': ComplianceReminder.query.filter_by(company_id=selected_company_id, category='employment', is_active=True).count(),
        'custom': ComplianceReminder.query.filter_by(company_id=selected_company_id, category='custom', is_active=True).count(),
    }
    
    # Get status counts
    status_counts = {
        'active': ComplianceReminder.query.filter_by(company_id=selected_company_id, is_active=True).count(),
        'overdue': len(ComplianceReminder.get_overdue_for_company(selected_company_id)),
        'upcoming': len(ComplianceReminder.get_upcoming_for_company(selected_company_id, 7))
    }
    
    return render_template('reminders/index.html',
                         company=company,
                         reminders=reminders,
                         category_filter=category_filter,
                         status_filter=status_filter,
                         category_counts=category_counts,
                         status_counts=status_counts)

@reminders_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Create a new compliance reminder"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id or not current_user.has_company_access(selected_company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Parse form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        category = request.form.get('category', 'custom')
        reminder_days_str = request.form.get('reminder_days', '7,3,1')
        is_recurring = request.form.get('is_recurring') == 'on'
        recurrence_pattern = request.form.get('recurrence_pattern') if is_recurring else None
        
        # Validation
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if not due_date_str:
            return jsonify({'error': 'Due date is required'}), 400
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid due date format'}), 400
        
        # Parse reminder days
        try:
            reminder_days = [int(x.strip()) for x in reminder_days_str.split(',') if x.strip()]
            if not reminder_days:
                reminder_days = [7, 3, 1]
        except ValueError:
            reminder_days = [7, 3, 1]
        
        # Create reminder
        reminder = ComplianceReminder(
            company_id=selected_company_id,
            title=title,
            description=description or None,
            due_date=due_date,
            category=category,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern,
            created_by=current_user.id
        )
        
        # Set reminder days using helper method
        reminder.set_reminder_days(reminder_days)
        
        db.session.add(reminder)
        db.session.commit()
        
        flash(f'Reminder "{title}" created successfully.', 'success')
        return jsonify({'success': True, 'id': reminder.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create reminder: {str(e)}'}), 500

@reminders_bp.route('/<int:reminder_id>/edit', methods=['POST'])
@login_required
def edit(reminder_id):
    """Edit an existing compliance reminder"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id or not current_user.has_company_access(selected_company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    reminder = ComplianceReminder.query.filter_by(
        id=reminder_id,
        company_id=selected_company_id
    ).first()
    
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404
    
    try:
        # Parse form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        category = request.form.get('category', 'custom')
        reminder_days_str = request.form.get('reminder_days', '7,3,1')
        is_recurring = request.form.get('is_recurring') == 'on'
        recurrence_pattern = request.form.get('recurrence_pattern') if is_recurring else None
        is_active = request.form.get('is_active') == 'on'
        
        # Validation
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if not due_date_str:
            return jsonify({'error': 'Due date is required'}), 400
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid due date format'}), 400
        
        # Parse reminder days
        try:
            reminder_days = [int(x.strip()) for x in reminder_days_str.split(',') if x.strip()]
            if not reminder_days:
                reminder_days = [7, 3, 1]
        except ValueError:
            reminder_days = [7, 3, 1]
        
        # Update reminder
        reminder.title = title
        reminder.description = description or None
        reminder.due_date = due_date
        reminder.category = category
        reminder.set_reminder_days(reminder_days)  # Use helper method
        reminder.is_recurring = is_recurring
        reminder.recurrence_pattern = recurrence_pattern
        reminder.is_active = is_active
        reminder.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Reminder "{title}" updated successfully.', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update reminder: {str(e)}'}), 500

@reminders_bp.route('/<int:reminder_id>/delete', methods=['POST'])
@login_required
def delete(reminder_id):
    """Delete a compliance reminder"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id or not current_user.has_company_access(selected_company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    reminder = ComplianceReminder.query.filter_by(
        id=reminder_id,
        company_id=selected_company_id
    ).first()
    
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404
    
    try:
        title = reminder.title
        db.session.delete(reminder)
        db.session.commit()
        
        flash(f'Reminder "{title}" deleted successfully.', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete reminder: {str(e)}'}), 500

@reminders_bp.route('/<int:reminder_id>/toggle', methods=['POST'])
@login_required
def toggle_active(reminder_id):
    """Toggle reminder active status"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id or not current_user.has_company_access(selected_company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    reminder = ComplianceReminder.query.filter_by(
        id=reminder_id,
        company_id=selected_company_id
    ).first()
    
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404
    
    try:
        reminder.is_active = not reminder.is_active
        reminder.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'activated' if reminder.is_active else 'deactivated'
        flash(f'Reminder "{reminder.title}" {status}.', 'success')
        return jsonify({'success': True, 'is_active': reminder.is_active})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to toggle reminder: {str(e)}'}), 500

@reminders_bp.route('/api/events')
@login_required
def api_events():
    """API endpoint to get reminder events for FullCalendar"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id or not current_user.has_company_access(selected_company_id):
        return jsonify([])
    
    # Get all active reminders for the company
    reminders = ComplianceReminder.query.filter_by(
        company_id=selected_company_id,
        is_active=True
    ).all()
    
    # Convert to FullCalendar events
    raw_events = [reminder.get_calendar_event() for reminder in reminders]

    # Deduplicate by (id, start) in case of accidental duplicates
    unique = {}
    for event in raw_events:
        key = (event.get('id'), event.get('start'))
        if key not in unique:
            unique[key] = event
    events = list(unique.values())

    current_app.logger.debug(
        f"/reminders/api/events returned {len(events)} events (from {len(raw_events)} records)"
    )

    return jsonify(events)

@reminders_bp.route('/<int:reminder_id>/api')
@login_required
def api_reminder(reminder_id):
    """API endpoint to get reminder data for editing"""
    selected_company_id = session.get('selected_company_id')
    
    if not selected_company_id or not current_user.has_company_access(selected_company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    reminder = ComplianceReminder.query.filter_by(
        id=reminder_id,
        company_id=selected_company_id
    ).first()
    
    if not reminder:
        return jsonify({'error': 'Reminder not found'}), 404
    
    return jsonify(reminder.to_dict())