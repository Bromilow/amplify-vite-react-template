# SQLAlchemy Model Schema Report

Generated on: January 3, 2025

## Overview

This report documents all SQLAlchemy models in the South African Payroll Management System, including field definitions, relationships, and constraints. The system uses a multi-tenant architecture with comprehensive employee lifecycle management, SARS compliance, and automated payroll processing.

## Model Summary

| Model | Table | Columns | Description |
|-------|-------|---------|-------------|
| User | `users` | 14 | Authentication and user management |
| Company | `companies` | 44 | **⚠️ OVERSIZED** - Company info + employee defaults |
| Employee | `employees` | 57 | **⚠️ OVERSIZED** - Employee data with duplicated fields |
| PayrollEntry | `payroll_entries` | 25 | Payroll calculations and processing |
| Beneficiary | `beneficiaries` | 11 | Third-party payment recipients |
| EmployeeRecurringDeduction | `employee_recurring_deductions` | 11 | Recurring deductions management |
| CompanyDeductionDefault | `company_deduction_defaults` | 8 | Company-wide deduction defaults |
| EmployeeMedicalAidInfo | `employee_medical_aid_info` | 15 | **⚠️ DUPLICATE** - Medical aid details |
| ComplianceReminder | `compliance_reminders` | 14 | Company compliance tracking |
| ComplianceReminderRule | `compliance_reminder_rules` | 12 | System-wide compliance rules |
| ReminderNotification | `reminder_notifications` | 10 | Notification system |
| SARSConfig | `sars_config` | 14 | Company SARS configuration |
| GlobalSARSConfig | `global_sars_config` | 14 | System-wide SARS defaults |
| DocumentTemplate | `document_templates` | 6 | Document template storage |
| UI19Record | `ui19_records` | 9 | Employee termination records |

---

## 1. User Model (`users`)

**Purpose**: Authentication and user management with multi-tenant company access

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `email` | String(120) | No | - | Unique email address |
| `password_hash` | String(256) | No | - | Hashed password |
| `first_name` | String(50) | Yes | - | User's first name |
| `last_name` | String(50) | Yes | - | User's last name |
| `cell_number` | String(20) | Yes | - | Contact number |
| `is_accountant` | Boolean | No | True | Accountant role flag |
| `is_admin` | Boolean | No | False | Admin role flag |
| `is_global_admin` | Boolean | No | False | Global admin flag |
| `is_power_user` | Boolean | No | False | Power user flag |
| `is_active` | Boolean | No | True | Account active status |
| `last_login` | DateTime | Yes | - | Last login timestamp |
| `current_company_id` | Integer | Yes | - | FK to companies |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |
| `updated_at` | DateTime | Yes | UTC now | Update timestamp |

### Relationships

- **companies**: Many-to-many via `user_company` table
- **current_company**: One-to-many with Company model

### Association Tables

#### user_company
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | Integer | FK to users.id |
| `company_id` | Integer | FK to companies.id |
| `created_at` | DateTime | Association timestamp |

---

## 2. Company Model (`companies`) ⚠️ OVERSIZED TABLE

**Purpose**: Multi-tenant company management with employee defaults

### Fields

#### Core Company Information (11 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `name` | String(150) | No | - | Company name |
| `registration_number` | String(50) | Yes | - | Company registration |
| `industry` | String(100) | Yes | - | Industry sector |
| `address` | Text | Yes | - | Company address |
| `phone` | String(20) | Yes | - | Contact phone |
| `email` | String(100) | Yes | - | Contact email |
| `tax_year_end` | String(10) | Yes | 'February' | Tax year end |
| `is_active` | Boolean | No | True | Company active status |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |
| `updated_at` | DateTime | Yes | UTC now | Update timestamp |

#### SARS Declaration Fields (5 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `uif_reference_number` | String(10) | Yes | - | UIF reference (1234567/8) |
| `paye_reference_number` | String(10) | Yes | - | PAYE reference (7xxxxxxxxx) |
| `employer_first_name` | String(50) | Yes | - | Employer first name |
| `employer_last_name` | String(50) | Yes | - | Employer last name |
| `employer_id_number` | String(13) | Yes | - | South African ID |

#### Payroll Configuration (7 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `default_hourly_rate` | Numeric(8,2) | Yes | - | Default hourly rate |
| `default_daily_rate` | Numeric(8,2) | Yes | - | Default daily rate |
| `overtime_multiplier` | Numeric(4,2) | Yes | 1.50 | Overtime multiplier |
| `sunday_multiplier` | Numeric(4,2) | Yes | 2.00 | Sunday multiplier |
| `public_holiday_multiplier` | Numeric(4,2) | Yes | 2.50 | Holiday multiplier |
| `uif_monthly_ceiling` | Numeric(10,2) | Yes | 17712.00 | UIF salary cap |
| `uif_percent` | Numeric(5,2) | Yes | 1.00 | UIF percentage |
| `sdl_percent` | Numeric(5,2) | Yes | 1.00 | SDL percentage |
| `default_pay_date` | String(20) | Yes | - | Default pay date |
| `default_ordinary_hours_per_day` | Numeric(4,2) | Yes | 8.0 | Default hours/day |
| `default_work_days_per_month` | Integer | Yes | 22 | Default work days |

#### Employee Defaults (21 fields) 🔴 **NORMALIZATION CANDIDATE**
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `default_salary_type` | String(10) | Yes | 'monthly' | Default salary type |
| `default_salary` | Numeric(10,2) | Yes | - | Default monthly salary |
| `default_bonus_type` | String(50) | Yes | - | Default bonus type |
| `default_annual_leave_days` | Integer | Yes | 15 | Default leave days |
| `default_sick_leave_days` | Integer | Yes | 10 | Default sick leave |
| `default_uif` | Boolean | Yes | True | Default UIF flag |
| `default_sdl` | Boolean | Yes | True | Default SDL flag |
| `default_paye_exempt` | Boolean | Yes | False | Default PAYE exempt |

### Relationships

- **employees**: One-to-many with Employee model
- **sars_config**: One-to-one with SARSConfig model

---

## 3. Employee Model (`employees`) ⚠️ OVERSIZED TABLE

**Purpose**: Employee management with personal, employment, and payroll data

### Fields

#### Core Information (16 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `company_id` | Integer | No | - | FK to companies |
| `employee_id` | String(20) | No | - | Unique employee ID |
| `first_name` | String(50) | No | - | First name |
| `last_name` | String(50) | No | - | Last name |
| `id_number` | String(13) | No | - | South African ID |
| `date_of_birth` | Date | Yes | - | Date of birth |
| `gender` | String(10) | Yes | - | Gender |
| `marital_status` | String(20) | Yes | - | Marital status |
| `tax_number` | String(50) | Yes | - | Tax number |
| `cell_number` | String(20) | No | - | Cell phone |
| `email` | String(100) | Yes | - | Email address |
| `physical_address` | Text | Yes | - | Physical address |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |
| `updated_at` | DateTime | Yes | UTC now | Update timestamp |

#### Employment Information (8 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `department` | String(50) | No | - | Department |
| `job_title` | String(100) | No | - | Job title |
| `start_date` | Date | No | - | Start date |
| `end_date` | Date | Yes | - | End date |
| `employment_type` | String(50) | No | 'Full-Time' | Employment type |
| `employment_status` | String(20) | No | 'Active' | Employment status |
| `termination_reason` | String(100) | Yes | - | Termination reason |
| `reporting_manager` | String(100) | Yes | - | Reporting manager |

#### Compensation (14 fields) 🔴 **POTENTIAL DUPLICATION**
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `salary_type` | String(20) | No | 'monthly' | Salary type |
| `salary` | Numeric(10,2) | No | - | Salary amount |
| `overtime_eligible` | Boolean | No | True | Overtime eligible |
| `allowances` | Numeric(10,2) | Yes | 0 | Allowances |
| `bonus_type` | String(20) | Yes | - | Bonus type |
| `ordinary_hours_per_day` | Numeric(4,2) | No | 8.0 | Hours per day |
| `work_days_per_month` | Integer | No | 22 | Work days per month |
| `overtime_calc_method` | String(20) | No | 'per_hour' | Overtime calculation |
| `overtime_multiplier` | Numeric(4,2) | No | 1.5 | Overtime multiplier |
| `sunday_multiplier` | Numeric(4,2) | No | 2.0 | Sunday multiplier |
| `holiday_multiplier` | Numeric(4,2) | No | 2.5 | Holiday multiplier |

#### Medical Aid (10 fields) 🔴 **DUPLICATE WITH employee_medical_aid_info**
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `medical_aid_scheme` | String(100) | Yes | - | Medical aid scheme |
| `medical_aid_number` | String(50) | Yes | - | Membership number |
| `medical_aid_principal_member` | Boolean | No | True | Principal member |
| `medical_aid_employee` | Numeric(10,2) | Yes | - | Employee contribution |
| `medical_aid_employer` | Numeric(10,2) | Yes | - | Employer contribution |
| `medical_aid_dependants` | Integer | Yes | 0 | Number of dependants |
| `medical_aid_fringe_benefit` | Numeric(10,2) | Yes | 0 | Fringe benefit |
| `linked_medical_beneficiary_id` | Integer | Yes | - | FK to beneficiaries |

#### Union (4 fields) 🔴 **LEGACY - REPLACED BY RECURRING DEDUCTIONS**
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `union_member` | Boolean | No | False | Union member flag |
| `union_name` | String(100) | Yes | - | Union name |
| `union_fee_type` | String(10) | Yes | - | **LEGACY** Fee type |
| `union_fee_amount` | Numeric(8,2) | Yes | 0 | **LEGACY** Fee amount |

#### Statutory Deductions (3 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `uif_contributing` | Boolean | No | True | UIF contributing |
| `sdl_contributing` | Boolean | No | True | SDL contributing |
| `paye_exempt` | Boolean | No | False | PAYE exempt |

#### Banking & Leave (4 fields)
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `bank_name` | String(100) | No | - | Bank name |
| `account_number` | String(30) | No | - | Account number |
| `account_type` | String(20) | No | 'Savings' | Account type |
| `annual_leave_days` | Integer | No | 15 | Annual leave days |

### Relationships

- **company**: Many-to-one with Company model
- **payroll_entries**: One-to-many with PayrollEntry model
- **linked_medical_beneficiary**: Many-to-one with Beneficiary model

### Constraints

- **Unique constraint**: `company_id` + `id_number` (company-scoped ID uniqueness)

---

## 4. PayrollEntry Model (`payroll_entries`)

**Purpose**: Payroll calculations and processing with verification workflow

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `employee_id` | Integer | No | - | FK to employees |
| `pay_period_start` | Date | No | - | Pay period start |
| `pay_period_end` | Date | No | - | Pay period end |
| `month_year` | String(7) | Yes | - | YYYY-MM format |
| `ordinary_hours` | Numeric(6,2) | No | 0 | Ordinary hours |
| `overtime_hours` | Numeric(6,2) | No | 0 | Overtime hours |
| `sunday_hours` | Numeric(6,2) | No | 0 | Sunday hours |
| `public_holiday_hours` | Numeric(6,2) | No | 0 | Holiday hours |
| `hourly_rate` | Numeric(8,2) | No | - | Hourly rate |
| `allowances` | Numeric(10,2) | No | 0 | Allowances |
| `bonus_amount` | Numeric(10,2) | Yes | 0 | Bonus amount |
| `deductions_other` | Numeric(10,2) | No | 0 | Other deductions |
| `union_fee` | Numeric(8,2) | No | 0 | Union fee |
| `paye` | Numeric(10,2) | No | 0 | PAYE tax |
| `uif` | Numeric(8,2) | No | 0 | UIF deduction |
| `sdl` | Numeric(8,2) | No | 0 | SDL deduction |
| `medical_aid_tax_credit` | Numeric(10,2) | Yes | 0 | Medical aid credit |
| `fringe_benefit_medical` | Numeric(10,2) | Yes | 0 | Medical fringe benefit |
| `net_pay` | Numeric(10,2) | No | 0 | Net pay |
| `is_verified` | Boolean | No | False | Verification status |
| `verified_at` | DateTime | Yes | - | Verification timestamp |
| `verified_by` | Integer | Yes | - | FK to users |
| `is_finalized` | Boolean | No | False | Finalization status |
| `finalized_at` | DateTime | Yes | - | Finalization timestamp |
| `finalized_by` | Integer | Yes | - | FK to users |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |

### Relationships

- **employee**: Many-to-one with Employee model

---

## 5. Beneficiary Model (`beneficiaries`)

**Purpose**: Third-party payment recipients for recurring deductions

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `company_id` | Integer | No | - | FK to companies |
| `type` | String(50) | No | - | Beneficiary type |
| `name` | String(255) | No | - | Beneficiary name |
| `bank_name` | String(100) | Yes | - | Bank name |
| `account_number` | String(50) | Yes | - | Account number |
| `branch_code` | String(20) | Yes | - | Branch code |
| `account_type` | String(20) | Yes | - | Account type |
| `include_in_eft_export` | Boolean | No | - | EFT export flag |
| `created_at` | DateTime | Yes | - | Creation timestamp |
| `updated_at` | DateTime | Yes | - | Update timestamp |

### Relationships

- **company**: Many-to-one with Company model

---

## 6. EmployeeRecurringDeduction Model (`employee_recurring_deductions`)

**Purpose**: Employee-specific recurring deductions

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `employee_id` | Integer | No | - | FK to employees |
| `beneficiary_id` | Integer | No | - | FK to beneficiaries |
| `amount_type` | String(10) | No | - | 'Fixed' or 'Percentage' |
| `value` | Numeric(10,2) | Yes | - | Deduction amount |
| `notes` | String(255) | Yes | - | Notes |
| `is_active` | Boolean | No | - | Active status |
| `effective_date` | Date | Yes | - | Effective date |
| `end_date` | Date | Yes | - | End date |
| `created_at` | DateTime | Yes | - | Creation timestamp |
| `updated_at` | DateTime | Yes | - | Update timestamp |

### Relationships

- **employee**: Many-to-one with Employee model
- **beneficiary**: Many-to-one with Beneficiary model

---

## 7. CompanyDeductionDefault Model (`company_deduction_defaults`)

**Purpose**: Company-wide recurring deduction defaults

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `company_id` | Integer | No | - | FK to companies |
| `beneficiary_id` | Integer | No | - | FK to beneficiaries |
| `amount` | Numeric(10,2) | Yes | - | Default amount |
| `amount_type` | String(10) | No | - | 'Fixed' or 'Percentage' |
| `include_in_eft_export` | Boolean | No | - | EFT export flag |
| `created_at` | DateTime | Yes | - | Creation timestamp |
| `updated_at` | DateTime | Yes | - | Update timestamp |

### Relationships

- **company**: Many-to-one with Company model
- **beneficiary**: Many-to-one with Beneficiary model

---

## 8. EmployeeMedicalAidInfo Model (`employee_medical_aid_info`) ⚠️ DUPLICATE

**Purpose**: Extended medical aid information (duplicates Employee fields)

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `employee_id` | Integer | No | - | FK to employees |
| `scheme_name` | String(100) | Yes | - | **DUPLICATE** Medical scheme |
| `membership_number` | String(50) | Yes | - | **DUPLICATE** Membership number |
| `number_of_dependants` | Integer | Yes | - | **DUPLICATE** Dependants |
| `main_member` | Boolean | No | - | **DUPLICATE** Main member |
| `linked_beneficiary_id` | Integer | Yes | - | FK to beneficiaries |
| `notes` | Text | Yes | - | Notes |
| `additional_dependants` | Integer | Yes | - | Additional dependants |
| `employer_contribution_override` | Numeric(10,2) | Yes | - | Employer override |
| `employee_contribution_override` | Numeric(10,2) | Yes | - | Employee override |
| `use_sars_calculation` | Boolean | Yes | True | Use SARS calc |
| `effective_from` | Date | Yes | - | Effective date |
| `created_at` | DateTime | Yes | - | Creation timestamp |
| `updated_at` | DateTime | Yes | - | Update timestamp |

### Relationships

- **employee**: Many-to-one with Employee model
- **linked_beneficiary**: Many-to-one with Beneficiary model

---

## 9. ComplianceReminder Model (`compliance_reminders`)

**Purpose**: Company-specific compliance reminders

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `company_id` | Integer | No | - | FK to companies |
| `title` | String(255) | No | - | Reminder title |
| `description` | Text | Yes | - | Description |
| `due_date` | Date | No | - | Due date |
| `category` | String(50) | No | 'custom' | Category |
| `is_recurring` | Boolean | No | False | Recurring flag |
| `recurrence_pattern` | String(50) | Yes | - | Recurrence pattern |
| `reminder_days` | String(100) | No | '7,3,1' | Reminder days |
| `is_active` | Boolean | No | True | Active status |
| `created_by` | Integer | No | - | FK to users |
| `created_at` | DateTime | Yes | now() | Creation timestamp |
| `updated_at` | DateTime | Yes | now() | Update timestamp |

### Relationships

- **company**: Many-to-one with Company model
- **created_by_user**: Many-to-one with User model

---

## 10. ComplianceReminderRule Model (`compliance_reminder_rules`)

**Purpose**: System-wide compliance rules

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `title` | String(255) | No | - | Rule title |
| `description` | Text | Yes | - | Description |
| `category` | String(50) | No | 'tax' | Category |
| `frequency` | String(20) | No | - | Frequency |
| `due_day` | Integer | No | - | Due day |
| `due_month` | Integer | Yes | - | Due month |
| `applies_to` | String(20) | No | - | Applies to |
| `reminder_days` | String(100) | Yes | - | Reminder days |
| `is_active` | Boolean | No | True | Active status |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |
| `updated_at` | DateTime | Yes | UTC now | Update timestamp |

---

## 11. ReminderNotification Model (`reminder_notifications`)

**Purpose**: Notification system for compliance reminders

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `reminder_id` | Integer | No | - | FK to compliance_reminders |
| `company_id` | Integer | No | - | FK to companies |
| `user_id` | Integer | No | - | FK to users |
| `notification_type` | String(20) | No | 'reminder' | Notification type |
| `message` | Text | No | - | Message |
| `is_read` | Boolean | No | False | Read status |
| `read_at` | DateTime | Yes | - | Read timestamp |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |

### Relationships

- **reminder**: Many-to-one with ComplianceReminder model
- **company**: Many-to-one with Company model
- **user**: Many-to-one with User model

---

## 12. SARSConfig Model (`sars_config`)

**Purpose**: Company-specific SARS configuration

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `company_id` | Integer | No | - | FK to companies |
| `uif_percent` | Numeric(5,3) | Yes | - | UIF percentage |
| `sdl_percent` | Numeric(5,3) | Yes | - | SDL percentage |
| `uif_salary_cap` | Numeric(10,2) | Yes | - | UIF salary cap |
| `uif_monthly_cap` | Numeric(10,2) | Yes | - | UIF monthly cap |
| `tax_year_start_month` | Integer | Yes | - | Tax year start month |
| `tax_year_start_day` | Integer | Yes | - | Tax year start day |
| `medical_primary_credit` | Numeric(10,2) | Yes | - | Medical primary credit |
| `medical_dependant_credit` | Numeric(10,2) | Yes | - | Medical dependant credit |
| `tax_authority_name` | String(64) | Yes | - | Tax authority name |
| `currency_symbol` | String(5) | Yes | - | Currency symbol |
| `tax_year_display` | String(20) | Yes | - | Tax year display |
| `created_at` | DateTime | Yes | - | Creation timestamp |

### Relationships

- **company**: One-to-one with Company model

---

## 13. GlobalSARSConfig Model (`global_sars_config`)

**Purpose**: System-wide SARS configuration defaults

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `uif_percent` | Numeric(5,3) | No | - | UIF percentage |
| `sdl_percent` | Numeric(5,3) | No | - | SDL percentage |
| `uif_salary_cap` | Numeric(10,2) | No | - | UIF salary cap |
| `uif_monthly_cap` | Numeric(10,2) | No | - | UIF monthly cap |
| `tax_year_start_month` | Integer | No | - | Tax year start month |
| `tax_year_start_day` | Integer | No | - | Tax year start day |
| `medical_primary_credit` | Numeric(10,2) | No | - | Medical primary credit |
| `medical_dependant_credit` | Numeric(10,2) | No | - | Medical dependant credit |
| `tax_authority_name` | String(64) | No | - | Tax authority name |
| `currency_symbol` | String(5) | No | - | Currency symbol |
| `tax_year_display` | String(20) | No | - | Tax year display |
| `is_active` | Boolean | No | - | Active status |
| `created_at` | DateTime | Yes | - | Creation timestamp |

---

## 14. DocumentTemplate Model (`document_templates`)

**Purpose**: Document template storage for compliance reports

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `document_type` | String(50) | No | - | Document type |
| `filename` | String(255) | No | - | Filename |
| `file_data` | Bytea | No | - | Binary file data |
| `uploaded_at` | DateTime | Yes | - | Upload timestamp |
| `uploaded_by` | Integer | No | - | FK to users |

### Relationships

- **uploaded_by_user**: Many-to-one with User model

---

## 15. UI19Record Model (`ui19_records`)

**Purpose**: Employee termination records for UI19 compliance

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | Integer | No | Auto-increment | Primary key |
| `employee_id` | Integer | No | - | FK to employees |
| `start_date` | Date | No | - | Employment start |
| `end_date` | Date | No | - | Employment end |
| `termination_reason` | String(255) | Yes | - | Termination reason |
| `notes` | Text | Yes | - | Notes |
| `status` | String(20) | No | 'Active' | Record status |
| `created_by` | Integer | No | - | FK to users |
| `created_at` | DateTime | Yes | UTC now | Creation timestamp |

### Relationships

- **employee**: Many-to-one with Employee model
- **created_by_user**: Many-to-one with User model

---

## 🔴 CRITICAL SCHEMA ISSUES IDENTIFIED

### 1. **Oversized Tables**
- **`companies`**: 44 columns (should be normalized)
- **`employees`**: 57 columns (should be split into multiple tables)

### 2. **Duplicate Medical Aid Functionality**
- **`employees`** table: 8 medical aid fields
- **`employee_medical_aid_info`** table: 15 fields (duplicates functionality)

### 3. **Legacy Fields (Superseded by Recurring Deductions)**
- **`employees.union_fee_type`** ⚠️ LEGACY
- **`employees.union_fee_amount`** ⚠️ LEGACY
- **`companies.default_union_fee_type`** ⚠️ LEGACY
- **`companies.default_union_fee_value`** ⚠️ LEGACY

### 4. **Normalization Opportunities**
- **Employee defaults** could be moved to separate table
- **Payroll configuration** could be extracted from companies table
- **Medical aid information** should be consolidated

### 5. **Missing Constraints**
- Several foreign key relationships lack proper indexes
- Some `amount_type` fields lack default values
- Inconsistent `created_at` default values

---

## Recommendations

### High Priority
1. **Normalize oversized tables** (companies, employees)
2. **Remove duplicate medical aid fields** (consolidate into single table)
3. **Remove legacy union fee fields** (replaced by recurring deductions)
4. **Add missing indexes** for foreign key relationships

### Medium Priority
1. **Standardize timestamp defaults** across all models
2. **Add validation constraints** for amount_type fields
3. **Create employee defaults table** (extract from companies)

### Low Priority
1. **Add audit trail fields** to critical tables
2. **Implement soft delete** for important records
3. **Add computed columns** for frequently calculated values

---

*Report generated by automated schema analysis tool*
*Last updated: January 3, 2025*