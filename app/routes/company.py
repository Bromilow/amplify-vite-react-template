from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Company, Beneficiary, Employee, EmployeeRecurringDeduction, CompanyDeductionDefault, CompanyDepartment
from app.forms import EmployeeDefaultsForm
from app.services.sars_service import SARSService

bp = Blueprint("company", __name__, url_prefix="/company")


@bp.route("/<int:company_id>")
@login_required
def company_detail(company_id):
    """Display dashboard overview for the specified company."""
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    # Persist company context
    session["selected_company_id"] = company_id
    session["current_company_id"] = company_id

    from app.routes.dashboard import overview as dashboard_overview
    return dashboard_overview()


@bp.route("/<int:company_id>/employees")
@login_required
def company_employees(company_id):
    """Show employees page filtered to the specified company."""
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    # Persist company context
    session["selected_company_id"] = company_id
    session["current_company_id"] = company_id

    from app.routes.employees import index as employees_index
    return employees_index()


@bp.route("/<int:company_id>/beneficiaries")
@login_required
def beneficiaries(company_id):
    """Display company beneficiaries"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    # Persist company context for AJAX calls on this page
    session["selected_company_id"] = company_id
    session["current_company_id"] = company_id

    company = Company.query.get_or_404(company_id)
    beneficiaries = company.beneficiaries.order_by(Beneficiary.name.asc()).all()

    return render_template(
        "company/beneficiaries.html", company=company, beneficiaries=beneficiaries, current_company_id=company_id
    )


@bp.route("/<int:company_id>/beneficiaries/add", methods=["POST"])
@login_required
def add_beneficiary(company_id):
    """Create new beneficiary"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    try:
        beneficiary = Beneficiary()
        beneficiary.company_id = company_id

        # Handle custom type
        beneficiary_type = request.form.get("type")
        if beneficiary_type == "Other":
            custom_type = request.form.get("custom_type", "").strip()
            beneficiary.type = custom_type if custom_type else "Other"
        else:
            beneficiary.type = beneficiary_type

        beneficiary.name = request.form.get("name")

        # Handle custom bank name
        bank_name = request.form.get("bank_name")
        if bank_name == "Other":
            custom_bank_name = request.form.get("custom_bank_name", "").strip()
            beneficiary.bank_name = custom_bank_name if custom_bank_name else "Other"
        else:
            beneficiary.bank_name = bank_name

        beneficiary.account_number = request.form.get("account_number")
        beneficiary.branch_code = request.form.get("branch_code")
        beneficiary.account_type = request.form.get("account_type", "Savings")
        beneficiary.include_in_eft_export = request.form.get("include_in_eft_export") == "1"

        db.session.add(beneficiary)
        db.session.commit()

        flash(f'Beneficiary "{beneficiary.name}" created successfully!', "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating beneficiary: {str(e)}", "error")

    # Determine redirect company ID from session, fallback to URL parameter
    selected_company_id = session.get("selected_company_id", company_id)
    return redirect(url_for("company.beneficiaries", company_id=selected_company_id))


@bp.route("/update_beneficiary/<int:beneficiary_id>", methods=["POST"])
@login_required
def update_beneficiary(beneficiary_id):
    """Edit existing beneficiary"""
    selected_company_id = session.get("selected_company_id")

    if not selected_company_id:
        flash("No company selected.", "error")
        return redirect(url_for("dashboard.overview"))

    # Verify user has access to this company
    if not current_user.has_company_access(selected_company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    beneficiary = Beneficiary.query.filter_by(id=beneficiary_id, company_id=selected_company_id).first_or_404()

    try:
        # Handle custom type
        beneficiary_type = request.form.get("type")
        if beneficiary_type == "Other":
            custom_type = request.form.get("custom_type", "").strip()
            beneficiary.type = custom_type if custom_type else "Other"
        else:
            beneficiary.type = beneficiary_type

        beneficiary.name = request.form.get("name")

        # Handle custom bank name
        bank_name = request.form.get("bank_name")
        if bank_name == "Other":
            custom_bank_name = request.form.get("custom_bank_name", "").strip()
            beneficiary.bank_name = custom_bank_name if custom_bank_name else "Other"
        else:
            beneficiary.bank_name = bank_name

        beneficiary.account_number = request.form.get("account_number")
        beneficiary.branch_code = request.form.get("branch_code")
        beneficiary.account_type = request.form.get("account_type", "Savings")
        beneficiary.include_in_eft_export = request.form.get("include_in_eft_export") == "1"

        db.session.commit()
        flash(f'Beneficiary "{beneficiary.name}" updated successfully!', "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating beneficiary: {str(e)}", "error")

    return redirect(url_for("company.beneficiaries", company_id=selected_company_id))


@bp.route("/beneficiaries/<int:beneficiary_id>/json")
@login_required
def beneficiary_json(beneficiary_id):
    """Return beneficiary data as JSON for AJAX editing"""
    selected_company_id = session.get("selected_company_id")

    if not selected_company_id:
        return jsonify({"error": "No company selected"}), 400

    if not current_user.has_company_access(selected_company_id):
        return jsonify({"error": "Access denied"}), 403

    beneficiary = Beneficiary.query.filter_by(id=beneficiary_id, company_id=selected_company_id).first()

    if not beneficiary:
        return jsonify({"error": "Beneficiary not found"}), 404

    try:
        return jsonify(beneficiary.to_dict())
    except Exception as e:
        return jsonify({"error": f"Failed to fetch beneficiary: {str(e)}"}), 500


@bp.route("/<int:company_id>/beneficiaries/<int:beneficiary_id>/delete", methods=["POST"])
@login_required
def delete_beneficiary(company_id, beneficiary_id):
    """Delete beneficiary"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    beneficiary = Beneficiary.query.filter_by(id=beneficiary_id, company_id=company_id).first_or_404()


    # Check if beneficiary is referenced elsewhere
    default_count = CompanyDeductionDefault.query.filter_by(beneficiary_id=beneficiary.id).count()
    deduction_count = EmployeeRecurringDeduction.query.filter_by(beneficiary_id=beneficiary.id).count()

    if default_count or deduction_count:
        flash(
            f"Cannot delete beneficiary because it's currently used in {default_count} company default(s) and {deduction_count} employee deduction(s). Please remove or update those entries first.",
            "warning",
        )
        return redirect(url_for('company.beneficiaries', company_id=company_id))

    try:
        beneficiary_name = beneficiary.name
        db.session.delete(beneficiary)
        db.session.commit()

        flash(f'Beneficiary "{beneficiary_name}" deleted successfully!', 'success')
        flash(f'Beneficiary "{beneficiary_name}" deleted successfully!', "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting beneficiary: {str(e)}", "error")

    return redirect(url_for("company.beneficiaries", company_id=company_id))


# API Endpoints for AJAX calls
@bp.route("/api/departments")
@login_required
def api_departments():
    """API endpoint to get unique departments for the current company"""
    try:
        # Get the selected company from session
        selected_company_id = session.get('selected_company_id')
        
        if not selected_company_id:
            return jsonify({"error": "No company selected"}), 400
        
        # Verify user has access to this company
        if not current_user.has_company_access(selected_company_id):
            return jsonify({"error": "Access denied"}), 403
        
        # Get departments from CompanyDepartment table
        departments = CompanyDepartment.get_company_departments(selected_company_id)
        department_list = [dept.name for dept in departments]
        
        return jsonify({"departments": department_list})
        
    except Exception as e:
        print(f"Error fetching departments: {e}")
        return jsonify({"error": "Failed to fetch departments"}), 500


@bp.route("/<int:company_id>/employee/<int:employee_id>/deductions")
@login_required
def employee_deductions(company_id, employee_id):
    """Display employee recurring deductions"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    company = Company.query.get_or_404(company_id)
    employee = Employee.query.filter_by(id=employee_id, company_id=company_id).first_or_404()

    # Get all deductions for this employee
    deductions = EmployeeRecurringDeduction.query.filter_by(employee_id=employee_id).all()

    # Get available beneficiaries for this company
    beneficiaries = company.beneficiaries.order_by(Beneficiary.name.asc()).all()

    # Calculate deduction totals
    active_deductions = [d for d in deductions if d.is_active]
    fixed_total = sum(float(d.value) for d in active_deductions if d.amount_type == "Fixed")
    percentage_total = sum(float(d.value) for d in active_deductions if d.amount_type == "Percentage")

    monthly_salary = float(employee.monthly_salary or 0)
    est_total_deductions = fixed_total + (monthly_salary * percentage_total / 100)

    return render_template(
        "company/employee_deductions.html",
        company=company,
        employee=employee,
        deductions=deductions,
        beneficiaries=beneficiaries,
        current_company_id=company_id,
        fixed_total=fixed_total,
        percentage_total=percentage_total,
        est_total_deductions=est_total_deductions,
    )


@bp.route("/<int:company_id>/employee/<int:employee_id>/deductions/add", methods=["POST"])
@login_required
def add_employee_deduction(company_id, employee_id):
    """Add recurring deduction for employee"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    try:
        deduction = EmployeeRecurringDeduction()
        deduction.employee_id = employee_id
        deduction.beneficiary_id = request.form.get("beneficiary_id")
        amount_type_raw = request.form.get("amount_type", "Fixed")
        amount_type_lower = str(amount_type_raw).lower()
        if amount_type_lower.startswith("percent"):
            deduction.amount_type = "Percentage"
        elif amount_type_lower.startswith("calc"):
            deduction.amount_type = "Calculated"
        else:
            deduction.amount_type = "Fixed"
        deduction.value = request.form.get("value")
        deduction.notes = request.form.get("notes")
        deduction.is_active = request.form.get("is_active") == "1"

        db.session.add(deduction)
        db.session.commit()

        flash("Recurring deduction added successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding deduction: {str(e)}", "error")

    return redirect(url_for("company.employee_deductions", company_id=company_id, employee_id=employee_id))


@bp.route("/<int:company_id>/employee/<int:employee_id>/deductions/<int:deduction_id>/edit", methods=["POST"])
@login_required
def edit_employee_deduction(company_id, employee_id, deduction_id):
    """Edit employee recurring deduction"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    deduction = EmployeeRecurringDeduction.query.filter_by(id=deduction_id, employee_id=employee_id).first_or_404()

    try:
        deduction.beneficiary_id = request.form.get("beneficiary_id")
        amount_type_raw = request.form.get("amount_type", "Fixed")
        amount_type_lower = str(amount_type_raw).lower()
        if amount_type_lower.startswith("percent"):
            deduction.amount_type = "Percentage"
        elif amount_type_lower.startswith("calc"):
            deduction.amount_type = "Calculated"
        else:
            deduction.amount_type = "Fixed"
        deduction.value = request.form.get("value")
        deduction.notes = request.form.get("notes")
        deduction.is_active = request.form.get("is_active") == "1"

        db.session.commit()
        flash("Recurring deduction updated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating deduction: {str(e)}", "error")

    return redirect(url_for("company.employee_deductions", company_id=company_id, employee_id=employee_id))


@bp.route("/<int:company_id>/employee/<int:employee_id>/deductions/<int:deduction_id>/delete", methods=["POST"])
@login_required
def delete_employee_deduction(company_id, employee_id, deduction_id):
    """Delete employee recurring deduction"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    deduction = EmployeeRecurringDeduction.query.filter_by(id=deduction_id, employee_id=employee_id).first_or_404()

    try:
        db.session.delete(deduction)
        db.session.commit()
        flash("Recurring deduction deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting deduction: {str(e)}", "error")

    return redirect(url_for("company.employee_deductions", company_id=company_id, employee_id=employee_id))


# =====================================================
# Company Deduction Defaults Management
# =====================================================


@bp.route("/<int:company_id>/deduction-defaults")
@login_required
def deduction_defaults(company_id):
    """Display company deduction defaults"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    company = Company.query.get_or_404(company_id)
    defaults = CompanyDeductionDefault.get_company_defaults(company_id)

    return render_template(
        "company/deduction_defaults.html", company=company, defaults=defaults, current_company_id=company_id
    )


@bp.route("/<int:company_id>/deduction-defaults", methods=["POST"])
@login_required
def create_deduction_default(company_id):
    """Create new deduction default"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    try:
        # Validate input
        beneficiary_id = request.form.get("beneficiary_id")
        amount = request.form.get("amount")
        amount_type = str(request.form.get("amount_type", "fixed")).lower()

        if not beneficiary_id:
            flash("Beneficiary is required.", "error")
            return redirect(url_for("dashboard.overview"))

        # Check if beneficiary belongs to this company
        beneficiary = Beneficiary.query.filter_by(id=beneficiary_id, company_id=company_id).first()
        if not beneficiary:
            flash("Invalid beneficiary selected.", "error")
            return redirect(url_for("dashboard.overview"))

        # Check if default already exists for this beneficiary
        existing = CompanyDeductionDefault.get_default_for_beneficiary(company_id, beneficiary_id)
        if existing:
            flash(f"Default already exists for {beneficiary.name}. Please edit the existing default.", "warning")
            return redirect(url_for("dashboard.overview"))

        # Create new default
        default = CompanyDeductionDefault()
        default.company_id = company_id
        default.beneficiary_id = beneficiary_id
        default.amount_type = amount_type
        # Inherit include_in_eft_export from beneficiary for consistency
        default.include_in_eft_export = beneficiary.include_in_eft_export
        if amount_type == "calculated":
            if beneficiary.type != "Medical Aid":
                flash("Calculated amount type is only allowed for Medical Aid beneficiaries.", "error")
                return redirect(url_for("dashboard.overview"))
            default.amount = None
        else:
            if not amount:
                flash("Amount is required unless deduction is calculated.", "error")
                return redirect(url_for("dashboard.overview"))
            default.amount = float(amount)

        db.session.add(default)
        db.session.commit()

        flash(f'Default deduction for "{beneficiary.name}" created successfully!', "success")

    except ValueError:
        db.session.rollback()
        flash("Invalid amount provided.", "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating default: {str(e)}", "error")

    return redirect(url_for("dashboard.overview"))


@bp.route("/<int:company_id>/deduction-defaults/<int:default_id>", methods=["POST"])
@login_required
def update_deduction_default(company_id, default_id):
    """Update existing deduction default"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    default = CompanyDeductionDefault.query.filter_by(id=default_id, company_id=company_id).first_or_404()

    try:
        # Update fields
        amount = request.form.get("amount")
        amount_type = str(request.form.get("amount_type", "fixed")).lower()

        # Always inherit include_in_eft_export from beneficiary for consistency
        default.include_in_eft_export = default.beneficiary.include_in_eft_export

        if amount_type == "calculated":
            if default.beneficiary.type != "Medical Aid":
                flash("Calculated amount type is only allowed for Medical Aid beneficiaries.", "error")
                return redirect(url_for("dashboard.overview"))
            default.amount = None
        else:
            if not amount:
                flash("Amount is required unless deduction is calculated.", "error")
                return redirect(url_for("dashboard.overview"))
            default.amount = float(amount)
        default.amount_type = amount_type

        db.session.commit()

        flash(f'Default for "{default.beneficiary.name}" updated successfully!', "success")

    except ValueError:
        db.session.rollback()
        flash("Invalid amount provided.", "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating default: {str(e)}", "error")

    return redirect(url_for("dashboard.overview"))


@bp.route("/<int:company_id>/deduction-defaults/<int:default_id>/delete", methods=["POST"])
@login_required
def delete_deduction_default(company_id, default_id):
    """Delete deduction default"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    default = CompanyDeductionDefault.query.filter_by(id=default_id, company_id=company_id).first_or_404()

    try:
        beneficiary_name = default.beneficiary.name
        db.session.delete(default)
        db.session.commit()
        flash(f'Default for "{beneficiary_name}" deleted successfully!', "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting default: {str(e)}", "error")

    return redirect(url_for("dashboard.overview"))


# API Endpoints for AJAX requests


@bp.route("/api/deduction-defaults")
@login_required
def api_deduction_defaults():
    """API endpoint to fetch company deduction defaults for current session company"""
    selected_company_id = session.get("selected_company_id")

    if not selected_company_id:
        return jsonify({"error": "No company selected"}), 400

    # Verify user has access to this company
    if not current_user.has_company_access(selected_company_id):
        return jsonify({"error": "Access denied"}), 403

    try:
        # Get company deduction defaults with beneficiary information
        defaults = (
            db.session.query(CompanyDeductionDefault, Beneficiary)
            .join(Beneficiary, CompanyDeductionDefault.beneficiary_id == Beneficiary.id)
            .filter(CompanyDeductionDefault.company_id == selected_company_id)
            .order_by(Beneficiary.name.asc())
            .all()
        )

        result = []
        for default, beneficiary in defaults:
            result.append(
                {
                    "id": default.id,
                    "beneficiary_id": beneficiary.id,
                    "beneficiary_name": beneficiary.name,
                    "beneficiary_type": beneficiary.type,
                    "amount": float(default.amount) if default.amount is not None else None,
                    "amount_type": default.amount_type,
                    "include_in_eft_export": beneficiary.include_in_eft_export,
                }
            )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to fetch deduction defaults: {str(e)}"}), 500


# Company Departments Management
@bp.route("/<int:company_id>/departments")
@login_required
def company_departments(company_id):
    """Display company departments management page"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    # Persist company context
    session["selected_company_id"] = company_id
    session["current_company_id"] = company_id

    company = Company.query.get_or_404(company_id)
    departments = CompanyDepartment.get_company_departments(company_id)

    return render_template(
        "company/departments.html", 
        company=company, 
        departments=departments, 
        current_company_id=company_id
    )


@bp.route("/<int:company_id>/departments/add", methods=["POST"])
@login_required
def add_department(company_id):
    """Add new department to company"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    try:
        department_name = request.form.get('department_name', '').strip()
        
        if not department_name:
            flash("Department name is required.", "error")
            return redirect(url_for("company.company_departments", company_id=company_id))

        # Check if department already exists for this company
        existing = CompanyDepartment.query.filter_by(
            company_id=company_id,
            name=department_name
        ).first()
        
        if existing:
            flash(f"Department '{department_name}' already exists.", "warning")
            return redirect(url_for("company.company_departments", company_id=company_id))

        # Create new department
        department = CompanyDepartment(
            company_id=company_id,
            name=department_name,
            is_default=False
        )
        
        db.session.add(department)
        db.session.commit()
        
        flash(f"Department '{department_name}' created successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating department: {str(e)}", "error")

    return redirect(url_for("company.company_departments", company_id=company_id))


@bp.route("/<int:company_id>/departments/<int:department_id>/edit", methods=["POST"])
@login_required
def edit_department(company_id, department_id):
    """Edit department name"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    try:
        department = CompanyDepartment.query.filter_by(
            id=department_id,
            company_id=company_id
        ).first_or_404()
        
        new_name = request.form.get('department_name', '').strip()
        old_name = department.name
        
        if not new_name:
            flash("Department name is required.", "error")
            return redirect(url_for("company.company_departments", company_id=company_id))

        # Check if new name already exists for this company (excluding current department)
        existing = CompanyDepartment.query.filter(
            CompanyDepartment.company_id == company_id,
            CompanyDepartment.name == new_name,
            CompanyDepartment.id != department_id
        ).first()
        
        if existing:
            flash(f"Department '{new_name}' already exists.", "warning")
            return redirect(url_for("company.company_departments", company_id=company_id))

        # Update department name
        department.name = new_name
        
        # Also update any employees that have this department
        employees_updated = Employee.query.filter_by(
            company_id=company_id,
            department=old_name
        ).update({'department': new_name})
        
        db.session.commit()
        
        flash(f"Department renamed from '{old_name}' to '{new_name}' successfully! Updated {employees_updated} employee(s).", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating department: {str(e)}", "error")

    return redirect(url_for("company.company_departments", company_id=company_id))


@bp.route("/<int:company_id>/departments/<int:department_id>/delete", methods=["POST"])
@login_required
def delete_department(company_id, department_id):
    """Delete department (with checks for employees using it)"""
    # Verify user has access to this company
    if not current_user.has_company_access(company_id):
        flash("You do not have access to this company.", "error")
        return redirect(url_for("dashboard.overview"))

    try:
        department = CompanyDepartment.query.filter_by(
            id=department_id,
            company_id=company_id
        ).first_or_404()
        
        department_name = department.name
        
        # Check if department is in use by employees
        employees_using = Employee.query.filter_by(
            company_id=company_id,
            department=department_name
        ).count()
        
        if employees_using > 0:
            flash(
                f"Cannot delete department '{department_name}' because it's currently used by {employees_using} employee(s). "
                f"Please reassign those employees to other departments first.",
                "warning"
            )
            return redirect(url_for("company.company_departments", company_id=company_id))

        # Delete department
        db.session.delete(department)
        db.session.commit()
        
        flash(f"Department '{department_name}' deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting department: {str(e)}", "error")

    return redirect(url_for("company.company_departments", company_id=company_id))


@bp.route("/recurring-deductions/<int:default_id>/json")
@login_required
def deduction_default_json(default_id):
    """Return a single company deduction default as JSON"""
    selected_company_id = session.get("selected_company_id")

    if not selected_company_id:
        return jsonify({"error": "No company selected"}), 400

    if not current_user.has_company_access(selected_company_id):
        return jsonify({"error": "Access denied"}), 403

    result = (
        db.session.query(CompanyDeductionDefault, Beneficiary)
        .join(Beneficiary, CompanyDeductionDefault.beneficiary_id == Beneficiary.id)
        .filter(
            CompanyDeductionDefault.company_id == selected_company_id,
            CompanyDeductionDefault.id == default_id,
        )
        .first()
    )

    if not result:
        return jsonify({"error": "Deduction default not found"}), 404

    default, beneficiary = result

    try:
        data = {
            "id": default.id,
            "beneficiary_id": beneficiary.id,
            "beneficiary_name": beneficiary.name,
            "beneficiary_type": beneficiary.type,
            "amount": float(default.amount) if default.amount is not None else None,
            "amount_type": default.amount_type,
            "include_in_eft_export": beneficiary.include_in_eft_export,
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch deduction default: {str(e)}"}), 500

@bp.route('/<int:company_id>/reports')
@login_required
def company_reports(company_id):
    """Display company-level reports and export tools"""
    if not current_user.has_company_access(company_id):
        flash('You do not have access to this company.', 'error')
        return redirect(url_for('dashboard.overview'))

    # Persist company context
    session['selected_company_id'] = company_id
    session['current_company_id'] = company_id

    company = Company.query.get_or_404(company_id)
    return render_template(
        'reports/index.html',
        company=company,
        current_company_id=company_id,
        date=date,
    )


@bp.route('/settings')
@login_required
def settings():
    """Display company settings page"""
    company_id = session.get('current_company_id')
    if not company_id:
        flash('No company selected', 'danger')
        return redirect(url_for('main.dashboard'))

    company = Company.query.get(company_id)
    employee_defaults_form = EmployeeDefaultsForm(obj=company)
    deduction_defaults = CompanyDeductionDefault.query.filter_by(company_id=company.id).all()
    beneficiaries = Beneficiary.query.filter_by(company_id=company.id).order_by(Beneficiary.name.asc()).all()
    
    # Get SARS configuration for this company
    sars_config = SARSService.get_company_sars_config(company_id)

    return render_template(
        'company/settings.html',
        company=company,
        employee_defaults_form=employee_defaults_form,
        deduction_defaults=deduction_defaults,
        beneficiaries=beneficiaries,
        sars_config=sars_config,
        show_edit_button=True,
    )


@bp.route('/<int:company_id>/edit', methods=['POST'])
@login_required
def edit_company(company_id):
    """Edit company details with comprehensive SARS validation"""
    from app.forms import CompanyForm
    
    company = Company.query.filter_by(id=company_id).first()
    if not company or not current_user.has_company_access(company_id):
        flash('Company not found or access denied.', 'error')
        return redirect(url_for('dashboard.overview'))

    form = CompanyForm()
    
    if form.validate_on_submit():
        try:
            # Update basic company information
            company.name = form.company_name.data.strip()
            company.industry = form.industry.data.strip() if form.industry.data else None
            company.registration_number = form.registration_number.data.strip() if form.registration_number.data else None
            company.email = form.company_email.data.strip() if form.company_email.data else None
            company.phone = form.company_phone.data.strip() if form.company_phone.data else None
            company.address = form.company_address.data.strip() if form.company_address.data else None
            company.tax_year_end = form.tax_year_end.data
            
            # Update SARS Declaration fields with validation
            company.uif_reference_number = form.uif_reference_number.data.strip() if form.uif_reference_number.data else None
            company.paye_reference_number = form.paye_reference_number.data.strip() if form.paye_reference_number.data else None
            company.employer_first_name = form.employer_first_name.data.strip() if form.employer_first_name.data else None
            company.employer_last_name = form.employer_last_name.data.strip() if form.employer_last_name.data else None
            company.employer_id_number = form.employer_id_number.data.strip() if form.employer_id_number.data else None

            db.session.commit()
            flash(f'Company "{company.name}" updated successfully with SARS-compliant reference numbers!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update company. Please try again.', 'error')
            
    else:
        # Form validation failed - display specific field errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.replace("_", " ").title()}: {error}', 'error')

    return redirect(url_for('company.settings'))
