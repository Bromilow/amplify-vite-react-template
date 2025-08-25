from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, BooleanField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length, Regexp

class EmployeeForm(FlaskForm):
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    id_number = StringField('ID Number', validators=[DataRequired(), Length(min=13, max=13)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=100)])
    cell_number = StringField('Cell Number', validators=[Optional(), Length(max=20)])
    physical_address = TextAreaField('Physical Address', validators=[Optional()])
    
    # Employment Information
    department = StringField('Department', validators=[DataRequired(), Length(max=50)])
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    employment_type = SelectField(
        'Employment Type',
        choices=[
            ('Full-Time', 'Full-Time'),
            ('Part-Time', 'Part-Time'),
            ('Contract', 'Contract'),
            ('Temporary', 'Temporary'),
            ('Seasonal', 'Seasonal')
        ],
        validators=[DataRequired()]
    )
    employment_status = SelectField(
        'Employment Status',
        choices=[
            ('Active', 'Active'),
            ('Suspended', 'Suspended'),
            ('Terminated', 'Terminated')
        ],
        default='Active',
        validators=[DataRequired()]
    )
    reporting_manager = StringField('Reporting Manager', validators=[Optional(), Length(max=100)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    
    # Compensation
    salary_type = SelectField(
        'Salary Type',
        choices=[
            ('monthly', 'Monthly'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('piece', 'Piece Work')
        ],
        validators=[DataRequired()]
    )
    salary = DecimalField('Salary Amount', validators=[DataRequired(), NumberRange(min=0)])
    allowances = DecimalField('Allowances', validators=[Optional(), NumberRange(min=0)])
    bonus_type = SelectField(
        'Bonus Type',
        choices=[
            ('', 'None'),
            ('Fixed', 'Fixed Amount'),
            ('Discretionary', 'Discretionary'),
            ('Performance', 'Performance Based')
        ],
        validators=[Optional()]
    )
    
    # Banking Information
    bank_name = SelectField(
        'Bank Name',
        choices=[
            ('', 'Select Bank'),
            ('ABSA Bank', 'ABSA Bank'),
            ('Standard Bank', 'Standard Bank'),
            ('First National Bank', 'First National Bank'),
            ('Nedbank', 'Nedbank'),
            ('Capitec Bank', 'Capitec Bank'),
            ('African Bank', 'African Bank'),
            ('Investec', 'Investec')
        ],
        validators=[Optional()]
    )
    account_number = StringField('Account Number', validators=[Optional(), Length(max=20)])
    account_type = SelectField(
        'Account Type',
        choices=[
            ('Savings', 'Savings'),
            ('Cheque', 'Cheque')
        ],
        validators=[Optional()]
    )
    
    # Statutory Deductions
    uif_contributing = BooleanField('UIF Contributing', default=True)
    sdl_contributing = BooleanField('SDL Contributing', default=True)
    paye_exempt = BooleanField('PAYE Exempt', default=False)
    
    # Union Information
    union_member = BooleanField('Union Member', default=False)
    union_name = StringField('Union Name', validators=[Optional(), Length(max=100)])
    
    # Medical Aid Information
    medical_aid_member = BooleanField('Medical Aid Member', default=False)
    medical_aid_scheme = StringField('Medical Aid Scheme', validators=[Optional(), Length(max=100)])
    medical_aid_number = StringField('Medical Aid Number', validators=[Optional(), Length(max=50)])
    medical_aid_dependants = DecimalField('Number of Dependants', validators=[Optional(), NumberRange(min=0)])
    medical_aid_employer = DecimalField('Employer Contribution', validators=[Optional(), NumberRange(min=0)])

class EmployeeDefaultsForm:
    def __init__(self, obj=None):
        self.obj = obj


class CompanyForm(FlaskForm):
    """Company information form with SARS validation"""
    # Basic Company Information
    company_name = StringField(
        'Company Name',
        validators=[DataRequired(), Length(max=255)]
    )
    industry = StringField(
        'Industry',
        validators=[Optional(), Length(max=100)]
    )
    registration_number = StringField(
        'Company Registration Number',
        validators=[
            Optional(),
            Regexp(r'^\d{4}/\d{6}/\d{2}$', message="Format must be YYYY/NNNNNN/YY (e.g., 2023/123456/07)")
        ]
    )
    company_email = StringField(
        'Email',
        validators=[Optional(), Email()]
    )
    company_phone = StringField(
        'Phone',
        validators=[Optional(), Length(max=20)]
    )
    company_address = TextAreaField(
        'Address',
        validators=[Optional()]
    )
    tax_year_end = SelectField(
        'Tax Year End',
        choices=[
            ('February', 'February'),
            ('March', 'March'),
            ('December', 'December')
        ],
        default='February',
        validators=[DataRequired()]
    )
    
    # SARS Declaration Information
    uif_reference_number = StringField(
        'UIF Employer Reference Number',
        validators=[
            Optional(),
            Regexp(r'^\d{7}/\d$', message="Format must be 1234567/8")
        ]
    )
    paye_reference_number = StringField(
        'PAYE Reference Number',
        validators=[
            Optional(),
            Regexp(r'^7\d{9}$', message="Must be 10 digits starting with 7")
        ]
    )
    employer_first_name = StringField(
        'Employer First Name',
        validators=[Optional(), Length(max=50)]
    )
    employer_last_name = StringField(
        'Employer Last Name', 
        validators=[Optional(), Length(max=50)]
    )
    employer_id_number = StringField(
        'Employer ID Number',
        validators=[
            Optional(),
            Regexp(r'^\d{13}$', message="Must be exactly 13 digits")
        ]
    )
