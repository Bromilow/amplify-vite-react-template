from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Company
from app.services.company_service import CompanyService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with automatic company selection for single-company users"""
    if request.method == 'POST':
        current_app.logger.debug("POST request received")
        email = request.form.get('email', '').strip().lower()  # Normalize email to lowercase
        password = request.form.get('password', '')
        current_app.logger.debug("Email (normalized): %s, Password length: %d", email, len(password) if password else 0)
        
        if not email or not password:
            current_app.logger.debug("Email or password missing")
            flash('Email and password are required.', 'error')
            return render_template('auth/login.html')
        
        # Find user by email (case-insensitive lookup)
        user = User.query.filter_by(email=email).first()
        current_app.logger.debug("User found: %s", user is not None)
        
        if user:
            current_app.logger.debug("User active: %s", user.is_active)
            password_check = user.check_password(password)
            current_app.logger.debug("Password check result: %s", password_check)
        
        if not user or not user.check_password(password):
            current_app.logger.debug("Authentication failed - invalid user or password")
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            current_app.logger.debug("User account inactive")
            flash('Your account has been deactivated. Please contact support.', 'error')
            return render_template('auth/login.html')
        
        # Log the user in
        current_app.logger.debug("Attempting to log user in")
        login_user(user, remember=True)
        session.permanent = True
        current_app.logger.debug("User logged in, is_authenticated: %s", user.is_authenticated)
        current_app.logger.debug("Session permanent: %s", session.permanent)
        
        # Update last login timestamp
        user.last_login = db.func.current_timestamp()
        
        # Handle company selection logic based on new requirements
        user_companies = user.companies.all()
        current_app.logger.debug("User companies count: %d", len(user_companies))
        
        if len(user_companies) == 0:
            current_app.logger.debug("No companies assigned to user")
            flash('You don\'t have any companies yet. Please create one to continue.', 'info')
            redirect_url = url_for('dashboard.new_company')
        elif user.is_accountant:
            # Accountants always go to portfolio dashboard regardless of company count
            session.pop('selected_company_id', None)  # Don't auto-select for accountants
            if len(user_companies) == 0:
                flash('Welcome! You haven\'t added any companies yet.', 'info')
            elif len(user_companies) == 1:
                flash(f'Welcome! You manage {user_companies[0].name}.', 'success')
            else:
                flash(f'Welcome! You manage {len(user_companies)} companies.', 'success')
            redirect_url = url_for('accountant_dashboard.dashboard')
        elif len(user_companies) == 1:
            # Single company business owner - auto-select and redirect to company dashboard
            company = user_companies[0]
            session['selected_company_id'] = company.id
            user.current_company_id = company.id
            current_app.logger.debug("Single company user, auto-selected: %s", company.name)
            flash(f'Welcome to {company.name}!', 'success')
            redirect_url = url_for('dashboard.overview')
        else:
            # Multi-company business owner - redirect to company selection
            session.pop('selected_company_id', None)
            current_app.logger.debug("Multi-company business owner, companies: %s", [c.name for c in user_companies])
            flash('Welcome! Please select a company to continue.', 'info')
            redirect_url = url_for('dashboard.overview')
        
        current_app.logger.debug("Committing session")
        db.session.commit()
        
        # Verify user session state before redirect
        current_app.logger.debug("Before redirect - user.get_id(): %s", user.get_id())
        current_app.logger.debug("Before redirect - session data: %s", dict(session))
        
        # Handle next page parameter for specific redirects
        next_page = request.args.get('next')
        if next_page:
            redirect_url = next_page
        
        current_app.logger.debug("Redirecting to: %s", redirect_url)
        return redirect(redirect_url)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout with session cleanup"""
    # Clear all company session data
    session.pop('current_company_id', None)
    session.pop('selected_company_id', None)
    
    # Log out the user
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/set-company', methods=['POST'])
@login_required
def set_company():
    """Handle company selection for multi-company users"""
    try:
        selected_id = int(request.form.get('company_id', 0))
    except (ValueError, TypeError):
        flash('Invalid company selection.', 'error')
        return redirect(request.referrer or url_for('dashboard.index'))
    
    # Verify user has access to this company
    if not current_user.has_company_access(selected_id):
        flash('You do not have access to this company.', 'error')
        return redirect(request.referrer or url_for('dashboard.index'))
    
    # Set the current company
    if CompanyService.set_current_company(current_user.id, selected_id):
        company = Company.query.get(selected_id)
        if company:
            flash(f'Switched to {company.name}', 'success')
        else:
            flash('Company switched successfully', 'success')
    else:
        flash('Failed to switch company.', 'error')
    
    return redirect(request.referrer or url_for('dashboard.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with company creation for business owners"""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_type = request.form.get('user_type', '')
        
        # Validate basic fields
        if not all([first_name, last_name, email, password, confirm_password, user_type]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[1]:
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/register.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email address already registered. Please use a different email.', 'error')
            return render_template('auth/register.html')
        
        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        # Validate password strength
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User()
            user.first_name = first_name
            user.last_name = last_name
            user.email = email.strip().lower()  # Normalize email to lowercase
            user.set_password(password)
            
            # Set user type flags
            if user_type == 'business_owner':
                user.is_accountant = False
                user.is_admin = False
            elif user_type == 'accountant':
                user.is_accountant = True
                user.is_admin = False
            else:
                flash('Invalid user type selected.', 'error')
                return render_template('auth/register.html')
            
            db.session.add(user)
            db.session.flush()  # Get user ID before creating company
            
            # If business owner, create company
            company = None
            if user_type == 'business_owner':
                # Get company fields
                company_name = request.form.get('company_name', '').strip()
                industry = request.form.get('industry', '').strip()
                registration_number = request.form.get('registration_number', '').strip()
                company_email = request.form.get('company_email', '').strip()
                company_phone = request.form.get('company_phone', '').strip()
                company_address = request.form.get('company_address', '').strip()
                tax_year_end = request.form.get('tax_year_end', 'February')
                
                # Validate company fields
                if not company_name:
                    flash('Company name is required for business owners.', 'error')
                    return render_template('auth/register.html')
                
                # Create company
                company = Company()
                company.name = company_name
                company.industry = industry if industry else None
                company.registration_number = registration_number if registration_number else None
                company.email = company_email if company_email else None
                company.phone = company_phone if company_phone else None
                company.address = company_address if company_address else None
                company.tax_year_end = tax_year_end
                company.is_active = True
                
                db.session.add(company)
                db.session.flush()  # Get company ID
                
                # Associate user with company
                user.companies.append(company)
                user.current_company_id = company.id
            
            db.session.commit()
            
            # Log the user in
            login_user(user, remember=True)
            session.permanent = True
            
            # Flash success message
            flash('Registration successful! Welcome to the Payroll Management System.', 'success')
            
            # Redirect based on user type
            if user_type == 'business_owner' and company:
                # Business owner with company should go to dashboard
                session['selected_company_id'] = company.id
                session['current_company_id'] = company.id
                return redirect(url_for('dashboard.overview'))
            else:  # accountant
                # Accountant should create their first company
                flash('Please add your first company to begin using the platform.', 'info')
                return redirect(url_for('dashboard.new_company'))
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error("Registration error: %s", e)
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')
    
    # GET request - show registration form
    return render_template('auth/register.html')

@auth_bp.route('/debug-users')
def debug_users():
    """Debug endpoint to check user database state"""
    from app.models.user import User
    users = User.query.order_by(User.id.desc()).limit(5).all()
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name} {user.last_name}",
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
        })
    return {'users': user_data, 'total_count': User.query.count()}

@auth_bp.route('/normalize-emails', methods=['POST'])
def normalize_emails():
    """One-time migration to normalize all user emails to lowercase"""
    from app.models.user import User
    from app import db
    
    try:
        users = User.query.all()
        updated_count = 0
        
        for user in users:
            original_email = user.email
            normalized_email = user.email.strip().lower()
            
            if user.email != normalized_email:
                current_app.logger.debug("Normalizing email: %s -> %s", original_email, normalized_email)
                user.email = normalized_email
                updated_count += 1
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Email normalization completed. Updated {updated_count} users.',
            'updated_count': updated_count,
            'total_users': len(users)
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("ERROR in email normalization: %s", str(e))
        return {
            'success': False,
            'message': f'Email normalization failed: {str(e)}',
            'updated_count': 0
        }, 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Admin utility to reset user password"""
    from app.models.user import User
    from app import db
    
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            data = {
                'email': request.form.get('email'),
                'new_password': request.form.get('new_password')
            }
        
        email = (data.get('email') or '').strip().lower()
        new_password = data.get('new_password') or ''
        
        if not email or not new_password:
            return {
                'success': False,
                'message': 'Email and new password are required'
            }, 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return {
                'success': False,
                'message': f'User with email {email} not found'
            }, 404
        
        # Reset password
        user.set_password(new_password)
        db.session.commit()
        
        current_app.logger.info("Password reset successful for user: %s", email)
        
        return {
            'success': True,
            'message': f'Password reset successful for {email}',
            'user_id': user.id
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("ERROR in password reset: %s", str(e))
        return {
            'success': False,
            'message': f'Password reset failed: {str(e)}'
        }, 500

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page allowing updates"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        cell_number = request.form.get('cell_number', '').strip()

        try:
            current_user.first_name = first_name or None
            current_user.last_name = last_name or None
            current_user.cell_number = cell_number or None
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        except Exception:
            db.session.rollback()
            flash('Failed to update profile.', 'error')

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/remove-company/<int:company_id>', methods=['POST'])
@login_required
def remove_company(company_id):
    """Remove user access to a company and delete if last user"""
    company = Company.query.get_or_404(company_id)

    if company not in current_user.companies:
        flash('Access not found.', 'error')
        return redirect(url_for('auth.profile'))

    # ``company.users`` returns an ``InstrumentedList`` because the backref is
    # not configured with ``lazy='dynamic'``. Attempting to call ``filter`` on
    # it raises ``AttributeError``.  Instead, count other users using a simple
    # list comprehension.
    other_users = len([u for u in company.users if u.id != current_user.id])

    try:
        current_user.companies.remove(company)

        if other_users == 0:
            # Import all models that have foreign key relationships to Company
            from app.models import (
                Employee, PayrollEntry, Beneficiary, EmployeeRecurringDeduction, 
                CompanyDeductionDefault, ComplianceReminder, ReminderNotification,
                UI19Record, EmployeeMedicalAidInfo
            )
            from app.models.sars_config import SARSConfig
            from app.models.company_department import CompanyDepartment

            # Get all employee IDs for this company first
            emp_ids = [e.id for e in Employee.query.filter_by(company_id=company.id).all()]
            
            # Delete in proper order to avoid foreign key constraint violations
            if emp_ids:
                # Delete employee-related records first
                PayrollEntry.query.filter(PayrollEntry.employee_id.in_(emp_ids)).delete(synchronize_session=False)
                EmployeeRecurringDeduction.query.filter(EmployeeRecurringDeduction.employee_id.in_(emp_ids)).delete(synchronize_session=False)
                EmployeeMedicalAidInfo.query.filter(EmployeeMedicalAidInfo.employee_id.in_(emp_ids)).delete(synchronize_session=False)
                UI19Record.query.filter(UI19Record.employee_id.in_(emp_ids)).delete(synchronize_session=False)
            
            # Delete employees
            Employee.query.filter_by(company_id=company.id).delete(synchronize_session=False)
            
            # Delete company-specific records
            Beneficiary.query.filter_by(company_id=company.id).delete(synchronize_session=False)
            CompanyDeductionDefault.query.filter_by(company_id=company.id).delete(synchronize_session=False)
            CompanyDepartment.query.filter_by(company_id=company.id).delete(synchronize_session=False)
            
            # Delete reminder notifications first (they reference compliance_reminders)
            reminder_ids = [r.id for r in ComplianceReminder.query.filter_by(company_id=company.id).all()]
            if reminder_ids:
                ReminderNotification.query.filter(ReminderNotification.reminder_id.in_(reminder_ids)).delete(synchronize_session=False)
            
            # Then delete compliance reminders
            ComplianceReminder.query.filter_by(company_id=company.id).delete(synchronize_session=False)
            SARSConfig.query.filter_by(company_id=company.id).delete(synchronize_session=False)
            
            # Update any users who have this company as their current company
            from app.models.user import User
            User.query.filter_by(current_company_id=company.id).update({'current_company_id': None})
            
            # Finally delete the company itself
            db.session.delete(company)

        db.session.commit()
        flash('Company access removed.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing company access: {str(e)}")
        flash('Failed to remove company access.', 'error')

    return redirect(url_for('auth.profile'))
