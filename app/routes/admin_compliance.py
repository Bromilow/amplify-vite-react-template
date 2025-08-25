from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import ComplianceReminderRule
from app import db
from datetime import datetime
from functools import wraps

# Create admin compliance blueprint
admin_compliance_bp = Blueprint('admin_compliance', __name__, url_prefix='/admin')

def power_user_required(f):
    """Decorator to require power user access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not getattr(current_user, 'is_power_user', False):
            flash('Access denied. Power user privileges required.', 'error')
            return redirect(url_for('dashboard.overview'))
        return f(*args, **kwargs)
    return decorated_function

@admin_compliance_bp.route('/compliance-rules')
@login_required
@power_user_required
def compliance_rules():
    """Admin interface for managing compliance reminder rules"""
    
    # Get all compliance rules ordered by category and title
    rules = ComplianceReminderRule.query.order_by(
        ComplianceReminderRule.category,
        ComplianceReminderRule.title
    ).all()
    
    current_app.logger.info(f"Power user {current_user.id} accessing compliance rules admin")
    
    return render_template('admin/compliance_rules.html', rules=rules)

@admin_compliance_bp.route('/compliance-rules/new', methods=['GET', 'POST'])
@login_required
@power_user_required
def new_compliance_rule():
    """Create new compliance reminder rule"""
    
    if request.method == 'POST':
        try:
            # Extract form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            frequency = request.form.get('frequency', '').strip()
            due_day = request.form.get('due_day', type=int)
            due_month = request.form.get('due_month', type=int)
            applies_to = request.form.get('applies_to', '').strip()
            reminder_days_str = request.form.get('reminder_days', '').strip()
            is_active = request.form.get('is_active') == 'on'
            
            # Validation
            errors = []
            if not title:
                errors.append('Title is required')
            if not category:
                errors.append('Category is required')
            if frequency not in ['monthly', 'annual', 'biannual']:
                errors.append('Invalid frequency')
            if not due_day or due_day < 1 or due_day > 31:
                errors.append('Due day must be between 1 and 31')
            if frequency in ['annual', 'biannual'] and (not due_month or due_month < 1 or due_month > 12):
                errors.append('Due month is required for annual/biannual rules')
            if not applies_to:
                errors.append('Applies to is required')
            
            # Parse reminder days
            reminder_days = []
            if reminder_days_str:
                try:
                    reminder_days = [int(x.strip()) for x in reminder_days_str.split(',') if x.strip()]
                    if any(d < 0 or d > 365 for d in reminder_days):
                        errors.append('Reminder days must be between 0 and 365')
                except ValueError:
                    errors.append('Invalid reminder days format (use comma-separated numbers)')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('admin/compliance_rule_form.html', 
                                     rule=None, 
                                     form_data=request.form)
            
            # Create new rule
            rule = ComplianceReminderRule(
                title=title,
                description=description,
                category=category,
                frequency=frequency,
                due_day=due_day,
                due_month=due_month if frequency in ['annual', 'biannual'] else None,
                applies_to=applies_to,
                is_active=is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Set reminder days
            rule.set_reminder_days(reminder_days)
            
            db.session.add(rule)
            db.session.commit()
            
            current_app.logger.info(f"Power user {current_user.id} created compliance rule: {title}")
            flash(f'Compliance rule "{title}" created successfully', 'success')
            return redirect(url_for('admin_compliance.compliance_rules'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating compliance rule: {str(e)}")
            flash('Error creating compliance rule. Please try again.', 'error')
            return render_template('admin/compliance_rule_form.html', 
                                 rule=None, 
                                 form_data=request.form)
    
    # GET request - show form
    return render_template('admin/compliance_rule_form.html', rule=None, form_data={})

@admin_compliance_bp.route('/compliance-rules/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
@power_user_required
def edit_compliance_rule(rule_id):
    """Edit existing compliance reminder rule"""
    
    rule = ComplianceReminderRule.query.get_or_404(rule_id)
    
    if request.method == 'POST':
        try:
            # Extract form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            frequency = request.form.get('frequency', '').strip()
            due_day = request.form.get('due_day', type=int)
            due_month = request.form.get('due_month', type=int)
            applies_to = request.form.get('applies_to', '').strip()
            reminder_days_str = request.form.get('reminder_days', '').strip()
            is_active = request.form.get('is_active') == 'on'
            
            # Validation
            errors = []
            if not title:
                errors.append('Title is required')
            if not category:
                errors.append('Category is required')
            if frequency not in ['monthly', 'annual', 'biannual']:
                errors.append('Invalid frequency')
            if not due_day or due_day < 1 or due_day > 31:
                errors.append('Due day must be between 1 and 31')
            if frequency in ['annual', 'biannual'] and (not due_month or due_month < 1 or due_month > 12):
                errors.append('Due month is required for annual/biannual rules')
            if not applies_to:
                errors.append('Applies to is required')
            
            # Parse reminder days
            reminder_days = []
            if reminder_days_str:
                try:
                    reminder_days = [int(x.strip()) for x in reminder_days_str.split(',') if x.strip()]
                    if any(d < 0 or d > 365 for d in reminder_days):
                        errors.append('Reminder days must be between 0 and 365')
                except ValueError:
                    errors.append('Invalid reminder days format (use comma-separated numbers)')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('admin/compliance_rule_form.html', 
                                     rule=rule, 
                                     form_data=request.form)
            
            # Update rule
            rule.title = title
            rule.description = description
            rule.category = category
            rule.frequency = frequency
            rule.due_day = due_day
            rule.due_month = due_month if frequency in ['annual', 'biannual'] else None
            rule.applies_to = applies_to
            rule.is_active = is_active
            rule.updated_at = datetime.utcnow()
            
            # Set reminder days
            rule.set_reminder_days(reminder_days)
            
            db.session.commit()
            
            current_app.logger.info(f"Power user {current_user.id} updated compliance rule: {title}")
            flash(f'Compliance rule "{title}" updated successfully', 'success')
            return redirect(url_for('admin_compliance.compliance_rules'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating compliance rule: {str(e)}")
            flash('Error updating compliance rule. Please try again.', 'error')
            return render_template('admin/compliance_rule_form.html', 
                                 rule=rule, 
                                 form_data=request.form)
    
    # GET request - show form with existing data
    form_data = {
        'title': rule.title,
        'description': rule.description or '',
        'category': rule.category,
        'frequency': rule.frequency,
        'due_day': rule.due_day,
        'due_month': rule.due_month or '',
        'applies_to': rule.applies_to,
        'reminder_days': ','.join(map(str, rule.get_reminder_days())),
        'is_active': rule.is_active
    }
    
    return render_template('admin/compliance_rule_form.html', rule=rule, form_data=form_data)

@admin_compliance_bp.route('/compliance-rules/<int:rule_id>/toggle', methods=['POST'])
@login_required
@power_user_required
def toggle_compliance_rule(rule_id):
    """Toggle active status of compliance reminder rule"""
    
    try:
        rule = ComplianceReminderRule.query.get_or_404(rule_id)
        rule.is_active = not rule.is_active
        rule.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'activated' if rule.is_active else 'deactivated'
        current_app.logger.info(f"Power user {current_user.id} {status} compliance rule: {rule.title}")
        flash(f'Compliance rule "{rule.title}" {status}', 'success')
        
        return jsonify({'success': True, 'is_active': rule.is_active})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling compliance rule: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_compliance_bp.route('/compliance-rules/<int:rule_id>/delete', methods=['POST'])
@login_required
@power_user_required
def delete_compliance_rule(rule_id):
    """Delete compliance reminder rule"""
    
    try:
        rule = ComplianceReminderRule.query.get_or_404(rule_id)
        rule_title = rule.title
        
        db.session.delete(rule)
        db.session.commit()
        
        current_app.logger.info(f"Power user {current_user.id} deleted compliance rule: {rule_title}")
        flash(f'Compliance rule "{rule_title}" deleted successfully', 'success')
        
        return redirect(url_for('admin_compliance.compliance_rules'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting compliance rule: {str(e)}")
        flash('Error deleting compliance rule. Please try again.', 'error')
        return redirect(url_for('admin_compliance.compliance_rules'))