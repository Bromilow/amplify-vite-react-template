# Complete UI19 Document Generation Code
**Flask Payroll Management System - UI19 PDF Generation Implementation**
*Extracted: June 26, 2025*

## Overview

This document contains the complete Python code for generating UI19 UIF Declaration documents. The system loads a DOCX template from the database, fills placeholders with employee and company data, and converts to PDF for download.

---

## Import Dependencies

```python
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, session, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app.models.employee import Employee
from app.models.payroll_entry import PayrollEntry
from app.models.company import Company
from app.models.ui19_record import UI19Record
from app.models.document_template import DocumentTemplate
from app import db
from datetime import datetime, date, timedelta
from decimal import Decimal
import tempfile
import os
from docx import Document
from docx2pdf import convert
```

---

## Main Route Handler

**Location:** `app/routes/employees.py` lines 2388-2643

```python
@employees_bp.route('/<int:employee_id>/generate-uif-doc')
@login_required
def generate_uif_doc(employee_id):
    """Generate UIF Declaration PDF document for terminated employee"""
    # Get current company
    current_company_id = session.get('current_company_id')
    if not current_company_id:
        flash('Please select a company first.', 'error')
        return redirect(url_for('dashboard.overview'))
    
    # Get employee with company access control
    employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id).first_or_404()
    company = employee.company
    
    # Check if employee has termination records
    ui19_records = UI19Record.query.filter_by(employee_id=employee_id, company_id=current_company_id).all()
    if not ui19_records:
        flash('No UI19 termination records found for this employee.', 'error')
        return redirect(url_for('employees.view', employee_id=employee_id))
    
    try:
        # Get the UI19 template from database
        ui19_template = DocumentTemplate.query.filter(
            DocumentTemplate.document_type.ilike('%UI19%')
        ).first()
        if not ui19_template:
            flash('UI19 document template not found. Please contact system administrator.', 'error')
            return redirect(url_for('employees.view', employee_id=employee_id))
        
        # Create temporary file for template
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_template:
            temp_template.write(ui19_template.file_data)
            template_path = temp_template.name
        
        # Load the template document
        doc = Document(template_path)
        
        # [HELPER FUNCTION DEFINED INLINE - See below]
        
        # Get latest termination record
        latest_record = ui19_records[-1]  # Most recent record
        
        # [DATA PREPARATION - See sections below]
        
        # [FIELD MAPPING - See comprehensive mapping below]
        
        # Replace all placeholders in the document
        for placeholder, value in field_map.items():
            fill_field(doc, placeholder, value)
        
        # Create temporary files for output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
            temp_docx_path = temp_docx.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        # Save the filled document
        doc.save(temp_docx_path)
        
        # Convert DOCX to PDF
        try:
            convert(temp_docx_path, temp_pdf_path)
        except Exception as conv_error:
            current_app.logger.error(f'Error converting DOCX to PDF: {str(conv_error)}')
            # If PDF conversion fails, return the DOCX file
            filename = f'UI19_Declaration_{employee.last_name}_{employee.first_name}.docx'
            response = send_file(temp_docx_path, as_attachment=True, download_name=filename)
            
            # Clean up temporary files
            try:
                os.unlink(template_path)
                os.unlink(temp_docx_path)
            except OSError:
                pass
            
            return response
        
        # Generate filename
        filename = f'UI19_Declaration_{employee.last_name}_{employee.first_name}.pdf'
        
        # Send the PDF file
        response = send_file(temp_pdf_path, as_attachment=True, download_name=filename)
        
        # Clean up temporary files
        try:
            os.unlink(template_path)
            os.unlink(temp_docx_path)
            os.unlink(temp_pdf_path)
        except OSError:
            pass
        
        return response
        
    except Exception as e:
        current_app.logger.error(f'Error generating UIF declaration for employee {employee_id}: {str(e)}')
        flash('Failed to generate UIF declaration document. Please try again.', 'error')
        return redirect(url_for('employees.view', employee_id=employee_id))
```

---

## Helper Function: fill_field()

**Location:** `app/routes/employees.py` lines 2426-2446

```python
def fill_field(doc, placeholder, value):
    """Replace placeholder text in document paragraphs and tables"""
    value = str(value) if value is not None else ''
    
    # Replace in paragraphs
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            for run in paragraph.runs:
                if placeholder in run.text:
                    run.text = run.text.replace(placeholder, value)
    
    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if placeholder in cell.text:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, value)
```

---

## Data Preparation Logic

**Location:** `app/routes/employees.py` lines 2448-2489

```python
# Get latest termination record
latest_record = ui19_records[-1]  # Most recent record

# Prepare company data
uif_ref = company.uif_reference_number or ''
paye_ref = company.paye_reference_number or ''
reg_number = company.registration_number or ''
contact_email = company.email or ''
phone_number = company.phone or ''
emp_fname = company.employer_first_name or ''
emp_lname = company.employer_last_name or ''
emp_id = company.employer_id_number or ''

# Prepare employee data
emp_last = employee.last_name or ''
emp_initials = employee.first_name[0] if employee.first_name else ''
emp_id_no = employee.id_number or ''

# Get latest payroll entry for salary information
latest_payroll = PayrollEntry.query.filter_by(employee_id=employee_id).order_by(PayrollEntry.pay_period_start.desc()).first()
if latest_payroll:
    emp_salary = str(int(float(latest_payroll.gross_pay or 0)))
    emp_salary_cents = "00"
else:
    emp_salary = str(int(float(employee.salary or 0)))
    emp_salary_cents = "00"

# Calculate average monthly hours (default to 160)
emp_hours = "160"  # Standard full-time hours per month

# Format dates
start_date = employee.start_date.strftime('%d%m%y') if employee.start_date else ''
end_date = latest_record.end_date.strftime('%d%m%y') if latest_record.end_date else ''

# Termination details
term_reason = "1"  # Default termination code - can be enhanced based on termination_reason
uif_status = "Y"   # Assume UIF eligible unless specified
uif_reason = "1"   # Default UIF reason code

# Current date info
today = datetime.today().strftime('%d/%m/%Y')
month_str = datetime.today().strftime('%B').upper()
```

---

## Complete Field Mapping Dictionary

**Location:** `app/routes/employees.py` lines 2491-2590

```python
# Field mapping for UI19 form
field_map = {
    # UIF Reference Number (split into individual characters)
    'E_1': uif_ref[0:1] if len(uif_ref) > 0 else '',
    'E_2': uif_ref[1:2] if len(uif_ref) > 1 else '',
    'E_3': uif_ref[2:3] if len(uif_ref) > 2 else '',
    'E_4': uif_ref[3:4] if len(uif_ref) > 3 else '',
    'E_5': uif_ref[4:5] if len(uif_ref) > 4 else '',
    'E_6': uif_ref[5:6] if len(uif_ref) > 5 else '',
    'E_7': uif_ref[6:7] if len(uif_ref) > 6 else '',
    'E_8': uif_ref[7:8] if len(uif_ref) > 7 else '',
    'E_9': uif_ref[9:10] if len(uif_ref) > 9 else '',
    
    # Period information
    'ED_MONTH': month_str,
    
    # PAYE Reference Number (split into individual characters)
    'P_1': paye_ref[0:1] if len(paye_ref) > 0 else '',
    'P_2': paye_ref[1:2] if len(paye_ref) > 1 else '',
    'P_3': paye_ref[2:3] if len(paye_ref) > 2 else '',
    'P_4': paye_ref[3:4] if len(paye_ref) > 3 else '',
    'P_5': paye_ref[4:5] if len(paye_ref) > 4 else '',
    'P_6': paye_ref[5:6] if len(paye_ref) > 5 else '',
    'P_7': paye_ref[6:7] if len(paye_ref) > 6 else '',
    'P_8': paye_ref[7:8] if len(paye_ref) > 7 else '',
    'P_9': paye_ref[8:9] if len(paye_ref) > 8 else '',
    'P_10': paye_ref[9:10] if len(paye_ref) > 9 else '',
    
    # Company Registration (split into individual characters)
    'C_1': reg_number[0:1] if len(reg_number) > 0 else '',
    'C_2': reg_number[1:2] if len(reg_number) > 1 else '',
    'C_3': reg_number[2:3] if len(reg_number) > 2 else '',
    'C_4': reg_number[3:4] if len(reg_number) > 3 else '',
    'C_5': reg_number[4:5] if len(reg_number) > 4 else '',
    'C_6': reg_number[5:6] if len(reg_number) > 5 else '',
    'C_7': reg_number[6:7] if len(reg_number) > 6 else '',
    'C_8': reg_number[7:8] if len(reg_number) > 7 else '',
    'C_9': reg_number[8:9] if len(reg_number) > 8 else '',
    'C_10': reg_number[9:10] if len(reg_number) > 9 else '',
    'C_11': reg_number[10:11] if len(reg_number) > 10 else '',
    'C_12': reg_number[11:12] if len(reg_number) > 11 else '',
    'C_13': reg_number[12:13] if len(reg_number) > 12 else '',
    'C_14': reg_number[13:14] if len(reg_number) > 13 else '',
    'C_15': reg_number[14:15] if len(reg_number) > 14 else '',
    
    # Company contact information
    'COMPANY_EMAIL': contact_email,
    'COMPANY_PHONE': phone_number,
    
    # Employer information
    'First_Last_Name': f"{emp_fname} {emp_lname}".strip(),
    
    # Employee information
    'EMP_L_NAME': emp_last,
    'EMP_I': emp_initials,
    
    # Employee ID Number (split into individual characters)
    'I_1': emp_id_no[0:1] if len(emp_id_no) > 0 else '',
    'I_2': emp_id_no[1:2] if len(emp_id_no) > 1 else '',
    'I_3': emp_id_no[2:3] if len(emp_id_no) > 2 else '',
    'I_4': emp_id_no[3:4] if len(emp_id_no) > 3 else '',
    'I_5': emp_id_no[4:5] if len(emp_id_no) > 4 else '',
    'I_6': emp_id_no[5:6] if len(emp_id_no) > 5 else '',
    'I_7': emp_id_no[6:7] if len(emp_id_no) > 6 else '',
    'I_8': emp_id_no[7:8] if len(emp_id_no) > 7 else '',
    'I_9': emp_id_no[8:9] if len(emp_id_no) > 8 else '',
    'I_10': emp_id_no[9:10] if len(emp_id_no) > 9 else '',
    'I_11': emp_id_no[10:11] if len(emp_id_no) > 10 else '',
    'I_12': emp_id_no[11:12] if len(emp_id_no) > 11 else '',
    'I_13': emp_id_no[12:13] if len(emp_id_no) > 12 else '',
    
    # Employee salary and hours
    'EMP_R': emp_salary,
    'EMP_C': emp_salary_cents,
    'EMP_H': emp_hours,
    
    # Employment dates (split into individual characters)
    'J_1': start_date[0:1] if len(start_date) > 0 else '',
    'J_2': start_date[1:2] if len(start_date) > 1 else '',
    'J_3': start_date[2:3] if len(start_date) > 2 else '',
    'J_4': start_date[3:4] if len(start_date) > 3 else '',
    'J_5': start_date[4:5] if len(start_date) > 4 else '',
    'J_6': start_date[5:6] if len(start_date) > 5 else '',
    
    'J_7': end_date[0:1] if len(end_date) > 0 else '',
    'J_8': end_date[1:2] if len(end_date) > 1 else '',
    'J_9': end_date[2:3] if len(end_date) > 2 else '',
    'J_10': end_date[3:4] if len(end_date) > 3 else '',
    'J_11': end_date[4:5] if len(end_date) > 4 else '',
    'J_12': end_date[5:6] if len(end_date) > 5 else '',
    
    # Termination codes
    'J_CODE': term_reason,
    'J_YN': uif_status,
    'J_R': uif_reason,
    
    # Signature information
    'EMP_ID': emp_id,
    'E_SIG': f"{emp_fname} {emp_lname}".strip(),
    'E_DATE': today
}
```

---

## Template Loading and Processing

```python
# Get the UI19 template from database
ui19_template = DocumentTemplate.query.filter(
    DocumentTemplate.document_type.ilike('%UI19%')  # Case-insensitive pattern matching
).first()

if not ui19_template:
    flash('UI19 document template not found. Please contact system administrator.', 'error')
    return redirect(url_for('employees.view', employee_id=employee_id))

# Create temporary file for template
with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_template:
    temp_template.write(ui19_template.file_data)  # file_data is stored as BLOB in database
    template_path = temp_template.name

# Load the template document using python-docx
doc = Document(template_path)
```

---

## Document Filling Process

```python
# Replace all placeholders in the document
for placeholder, value in field_map.items():
    fill_field(doc, placeholder, value)

# The fill_field function processes:
# 1. All paragraphs in the document
# 2. All tables and their cells
# 3. All runs within paragraphs and cells
# 4. Character-by-character replacement for form fields
```

---

## Font Styling Logic

**Note:** Currently, no specific font styling is applied. The system preserves the original formatting from the template. To add font styling, the following could be implemented:

```python
# Example font styling (not currently implemented)
def apply_font_styling(run):
    """Apply consistent font styling to filled fields"""
    from docx.shared import Pt
    run.font.size = Pt(10)  # Set font size to 10pt
    run.font.name = 'Arial'  # Set font family
    run.bold = False  # Remove bold formatting
```

---

## File Saving and PDF Conversion

```python
# Create temporary files for output
with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
    temp_docx_path = temp_docx.name

with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
    temp_pdf_path = temp_pdf.name

# Save the filled document
doc.save(temp_docx_path)

# Convert DOCX to PDF using docx2pdf
try:
    convert(temp_docx_path, temp_pdf_path)
    
    # Generate filename
    filename = f'UI19_Declaration_{employee.last_name}_{employee.first_name}.pdf'
    
    # Send the PDF file
    response = send_file(temp_pdf_path, as_attachment=True, download_name=filename)
    
except Exception as conv_error:
    current_app.logger.error(f'Error converting DOCX to PDF: {str(conv_error)}')
    
    # Fallback: Return DOCX file if PDF conversion fails
    filename = f'UI19_Declaration_{employee.last_name}_{employee.first_name}.docx'
    response = send_file(temp_docx_path, as_attachment=True, download_name=filename)

# Clean up temporary files
try:
    os.unlink(template_path)
    os.unlink(temp_docx_path)
    os.unlink(temp_pdf_path)
except OSError:
    pass

return response
```

---

## Error Handling and Logging

```python
try:
    # Main document generation logic
    
except Exception as e:
    current_app.logger.error(f'Error generating UIF declaration for employee {employee_id}: {str(e)}')
    flash('Failed to generate UIF declaration document. Please try again.', 'error')
    return redirect(url_for('employees.view', employee_id=employee_id))
```

---

## Data Sources and Validation

### **Required Data Models:**
- `Employee` - Personal and employment information
- `Company` - UIF/PAYE reference numbers, employer details
- `UI19Record` - Termination records and dates
- `PayrollEntry` - Latest salary information
- `DocumentTemplate` - UI19 DOCX template file

### **Data Validation:**
- Employee must belong to current company
- UI19 termination records must exist
- UI19 template must be uploaded to system
- All database lookups include error handling

### **Field Processing:**
- Character-by-character splitting for form fields
- Date formatting (DDMMYY format)
- Salary conversion to integer (removes decimals)
- String concatenation with null value handling

---

## Known Issues and Limitations

### **PDF Conversion Issue:**
```
ERROR:app:Error converting DOCX to PDF: docx2pdf is not implemented for linux as it requires Microsoft Word to be installed
```
**Impact:** System falls back to DOCX file download when PDF conversion fails

### **Template Dependency:**
- Requires UI19 template to be uploaded via Admin → System Documents
- Template placeholders must match field_map keys exactly
- No validation of template placeholder completeness

### **Character Splitting Logic:**
- UIF reference number assumes specific format
- Missing index 8 in UIF reference (E_8 maps to index 7, E_9 maps to index 9)
- Could cause IndexError with malformed reference numbers

### **Hardcoded Values:**
- Default termination codes (term_reason = "1")
- Standard work hours (emp_hours = "160")
- UIF eligibility assumptions (uif_status = "Y")

---

## Enhancement Opportunities

### **Immediate Fixes:**
1. Fix UIF reference number character mapping
2. Add template placeholder validation
3. Implement proper termination code mapping
4. Add font styling preservation/application

### **Advanced Features:**
1. Template preview functionality
2. Batch UI19 generation for multiple employees
3. Custom termination reason code mapping
4. Integration with SARS submission system

---

*This comprehensive code extraction provides the complete implementation for debugging and enhancement of the UI19 document generation system.*