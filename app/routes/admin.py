from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user
from app.models import GlobalSARSConfig, DocumentTemplate
from app import db
from decimal import Decimal
from werkzeug.utils import secure_filename
import os
from io import BytesIO

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def global_admin_required(func):
    """Decorator to require global admin access"""
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        # Check if user has global admin privileges
        # For now, we'll use a simple check - you can extend this based on your user model
        if not getattr(current_user, 'is_global_admin', False):
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for('dashboard.overview'))
        
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    return login_required(wrapper)

@admin_bp.route('/sars-settings', methods=['GET', 'POST'])
@global_admin_required
def sars_settings():
    """Admin page for editing global SARS configuration"""
    config = GlobalSARSConfig.query.first()
    if not config:
        # Create default configuration if none exists
        config = GlobalSARSConfig()
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        try:
            # Convert percentage inputs to decimal (divide by 100)
            uif_percent_input = request.form.get('uif_percent', '1.0')
            sdl_percent_input = request.form.get('sdl_percent', '1.0')
            
            config.uif_percent = Decimal(str(uif_percent_input)) / 100
            config.sdl_percent = Decimal(str(sdl_percent_input)) / 100
            
            # UIF caps and salary limits
            config.uif_salary_cap = Decimal(str(request.form.get('uif_salary_cap', '17712')))
            config.uif_monthly_cap = Decimal(str(request.form.get('uif_monthly_cap', '177.12')))
            
            # Tax year configuration
            config.tax_year_start_day = int(request.form.get('tax_year_start_day', '1'))
            config.tax_year_start_month = int(request.form.get('tax_year_start_month', '3'))
            
            # Medical aid credits
            config.medical_primary_credit = Decimal(str(request.form.get('medical_primary_credit', '364')))
            config.medical_dependant_credit = Decimal(str(request.form.get('medical_dependant_credit', '246')))
            
            # Authority and currency settings
            config.tax_authority_name = request.form.get('tax_authority_name', 'SARS').strip()
            config.currency_symbol = request.form.get('currency_symbol', 'R').strip()
            
            db.session.commit()
            flash("SARS configuration updated successfully! Changes will apply to all companies using global defaults.", "success")
            
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input format: {str(e)}", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating configuration: {str(e)}", "danger")

    return render_template('admin/sars_settings.html', config=config)

@admin_bp.route('/dashboard')
@global_admin_required
def dashboard():
    """Admin dashboard with system overview"""
    from app.models import Company, User, Employee
    
    # Get system statistics
    total_companies = Company.query.count()
    total_users = User.query.count()
    total_employees = Employee.query.count()
    
    # Get SARS config status
    sars_config = GlobalSARSConfig.query.first()
    
    stats = {
        'total_companies': total_companies,
        'total_users': total_users,
        'total_employees': total_employees,
        'sars_config_exists': sars_config is not None
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/documents')
@global_admin_required
def documents():
    """System Documents management page"""
    # Get all existing document templates
    templates = DocumentTemplate.query.order_by(DocumentTemplate.uploaded_at.desc()).all()
    
    # Define available document types
    document_types = [
        'UI19 Termination Form',
        'IRP5 Certificate', 
        'EMP501 Summary',
        'EMP201 Monthly Return',
        'UIF Declaration',
        'SDL Declaration',
        'Employment Contract Template',
        'Payslip Template'
    ]
    
    return render_template('admin/documents.html', 
                         templates=templates, 
                         document_types=document_types)

@admin_bp.route('/documents/upload', methods=['POST'])
@global_admin_required
def upload_document():
    """Handle document template upload"""
    try:
        document_type = request.form.get('document_type')
        if not document_type:
            flash("Please select a document type.", "danger")
            return redirect(url_for('admin.documents'))
        
        # Check if file was uploaded
        if 'document_file' not in request.files:
            flash("No file selected.", "danger")
            return redirect(url_for('admin.documents'))
        
        file = request.files['document_file']
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(url_for('admin.documents'))
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.docx'):
            flash("Only .docx files are allowed.", "danger")
            return redirect(url_for('admin.documents'))
        
        # Secure the filename
        filename = secure_filename(file.filename) if file.filename else 'unknown.docx'
        
        # Read file data
        file_data = file.read()
        
        # Check if template already exists for this document type
        existing_template = DocumentTemplate.query.filter_by(document_type=document_type).first()
        
        if existing_template:
            # Update existing template
            existing_template.filename = filename
            existing_template.file_data = file_data
            existing_template.uploaded_by = current_user.id
            existing_template.uploaded_at = db.func.now()
            
            flash(f"Document template '{document_type}' has been updated successfully.", "success")
        else:
            # Create new template
            template = DocumentTemplate(
                document_type=document_type,
                filename=filename,
                file_data=file_data,
                uploaded_by=current_user.id
            )
            db.session.add(template)
            
            flash(f"Document template '{document_type}' has been uploaded successfully.", "success")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading document: {str(e)}", "danger")
    
    return redirect(url_for('admin.documents'))

@admin_bp.route('/documents/download/<int:template_id>')
@global_admin_required
def download_document(template_id):
    """Download a document template"""
    template = DocumentTemplate.query.get_or_404(template_id)
    
    return send_file(
        BytesIO(template.file_data),
        as_attachment=True,
        download_name=template.filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@admin_bp.route('/documents/delete/<int:template_id>', methods=['POST'])
@global_admin_required
def delete_document(template_id):
    """Delete a document template"""
    try:
        template = DocumentTemplate.query.get_or_404(template_id)
        document_type = template.document_type
        
        db.session.delete(template)
        db.session.commit()
        
        flash(f"Document template '{document_type}' has been deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting document: {str(e)}", "danger")
    
    return redirect(url_for('admin.documents'))