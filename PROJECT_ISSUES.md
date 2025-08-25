# Project Issues & Development Tracking
**Flask Payroll Management System**

Last Updated: January 2025  
Current Status: 95% Production Ready

---

## 🔴 High Priority Issues (Production Blockers)

### Company Access Removal Bug (Resolved)
- [x] **🏢 Failed to Remove Company Access Error** - Missing foreign key relationships in deletion logic ✅ Fixed: 2025-08-06T13:45:00+00:00
- [x] **🔗 ReminderNotification Indirect Relationship** - Fixed indirect company_id relationship through ComplianceReminder ✅ Fixed: 2025-08-06T13:46:00+00:00

### LSP Diagnostics (45 issues across 9 files)
- [ ] **app/routes/employees.py** (13 issues) - Medical aid field references after model migration
- [ ] **app/models/payroll_entry.py** (11 issues) - Relationship access patterns and type annotations
- [ ] **app/services/portfolio_service.py** (5 issues) - SQLAlchemy boolean expression warnings
- [ ] **app/routes/dashboard.py** (5 issues) - Type warnings in dashboard logic
- [ ] **app/routes/payroll.py** (6 issues) - Payroll calculation type annotations
- [ ] **app/models/employee.py** (1 issue) - Constructor validation
- [ ] **app/models/user.py** (2 issues) - Type annotation improvements
- [ ] **app/routes/admin.py** (1 issue) - Minor type warning
- [ ] **app/services/employee_service.py** (1 issue) - Service layer type checking

### Missing Core Routes (Identified via verification)
- [ ] **Employee Export** - `/employees/export` endpoint missing (import exists)
- [ ] **Payroll Verification** - `/payroll/verify` route not found (internal references exist)
- [ ] **Payroll Finalization** - `/payroll/finalize` route not found (internal references exist)
- [ ] **Company Selection Route** - `/dashboard/company-selection` route missing

### Employee Form UX Issues (High Impact)
- [x] **🧍 SA ID vs Passport Toggle** - Add toggle between South African ID and Passport number entry ✅ Fixed: 2025-08-06T08:14:00+00:00
- [x] **📱 Cell Number Validation** - Accept 06x/07x/08x formats, convert to +27 xxx xxx xxxx on save ✅ Fixed: 2025-08-06T07:55:00+00:00
- [x] **🏢 Company-scoped Department Management** - Implemented CompanyDepartment model with full CRUD system ✅ Fixed: 2025-08-06T10:14:00+00:00
- [x] **🏢 Default Department Initialization** - New companies automatically get 9 default departments seeded ✅ Fixed: 2025-08-06T10:35:00+00:00
- [x] **🏢 Company-specific Department Filtering** - Employee forms now show only company-specific departments ✅ Fixed: 2025-08-06T10:35:00+00:00  
- [x] **🏢 Department Management UI Redesign** - Improved table-style layout with statistics row ✅ Fixed: 2025-08-06T10:35:00+00:00
- [x] **🔁 Form State Preservation** - Add Employee form now retains user input on validation errors ✅ Fixed: 2025-08-06T14:02:00+00:00
- [ ] **🏢 Custom Department Field Placement** - Fix "Other" department input appearing at bottom instead of below dropdown
- [ ] **💸 Overtime Logic Bug** - Form validates workdays when "Overtime Eligible" unchecked, blocks submission
- [ ] **🔁 Decimal Precision Handling** - Work Days Per Month field must accept decimals (e.g., 22.00)
- [x] **🚨 Edit Employee Modal Bug** - 500 error when opening edit modal due to missing medical aid fields ✅ Fixed: August 2025
- [x] **🔁 Recurring Deduction Default Override Bug** - Defaults re-applied even when user removes them from form ✅ Fixed: August 2025

### Calendar Integration Gap
- [ ] **Complete Calendar Implementation** - Currently only placeholder route exists
- [ ] **Compliance Calendar Integration** - Link with existing compliance reminder system
- [ ] **FullCalendar.js Integration** - Frontend calendar functionality incomplete

---

## 🟡 Medium Priority Enhancements

### Infrastructure & Configuration
- [ ] **SMTP Email Configuration** - Service exists but requires setup for notifications
- [ ] **Database Production Config** - Currently defaults to SQLite, needs PostgreSQL setup guide
- [ ] **Environment Secrets Management** - Document required environment variables

### Route Consistency & API Design
- [ ] **Reports Endpoint Standardization** - Currently uses CSV exports, consider REST endpoints
- [ ] **API Response Consistency** - Standardize JSON response formats across blueprints
- [ ] **Error Handling Enhancement** - Improve user-facing error messages and logging

### Employee Form Logic & Validation
- [ ] **🧍 Auto-fill Logic Enhancement** - Date of Birth auto-fill only for valid SA ID, lock field when SA ID used
- [ ] **🧍 Gender Field Behavior** - Make auto-filled but editable, or lockable based on policy
- [ ] **📱 Cell Number Format Validation** - Reject invalid formats (non-numeric, too short)
- [ ] **🏢 Department/Job Title Dropdowns** - Confirm all employment dropdowns working correctly
- [ ] **💸 Salary Type Logic Verification** - Ensure Monthly/Hourly/Daily/Piecework calculations work
- [ ] **🔁 Form Sync Issues** - Sync validation rules between Add Employee and Employee Defaults forms
- [ ] **🔁 Backend Validation** - Add server-side validation to mirror front-end rules

### Testing & Quality Assurance
- [ ] **Fix Test Failure** - `tests/test_employee_edit.py::test_add_employee_calculated_deduction`
- [ ] **Expand Test Coverage** - Add integration tests for payroll calculations
- [ ] **Performance Testing** - Load testing for multi-tenant scenarios

### Security Enhancements
- [ ] **Input Validation Review** - Comprehensive form validation audit
- [ ] **Session Security Hardening** - Review session configuration for production
- [ ] **CSRF Token Verification** - Ensure all forms properly protected

---

## 🟢 Low Priority Polish & Features

### User Experience Improvements
- [ ] **Mobile Responsiveness Review** - Test all modals and forms on mobile devices
- [ ] **Loading States** - Add loading spinners for long-running operations
- [ ] **Success/Error Feedback** - Enhance user feedback for form submissions

### Form UX Polish & Consistency
- [ ] **🧍 Passport Number Manual Entry** - Allow manual passport number entry when toggle selected
- [ ] **🧍 Auto-fill Disable Logic** - Disable DOB/gender auto-fill when "Passport" selected
- [ ] **💸 Decimal Input Consistency** - Ensure Employee Defaults and Add Employee forms handle decimals identically
- [ ] **🔁 Default Population Logic** - Verify defaults sync correctly between forms and config

### Documentation & Maintenance
- [ ] **User Documentation** - Create end-user guides for payroll processing
- [ ] **Admin Documentation** - System administration and maintenance guides
- [ ] **API Documentation** - Document internal API endpoints for future development

### Advanced Features (Future Enhancements)
- [ ] **Advanced Reporting Dashboard** - Beyond current CSV exports
- [ ] **Audit Trail Enhancement** - Detailed logging for compliance tracking
- [ ] **Bulk Operations** - Employee bulk updates, mass payroll processing
- [ ] **Integration APIs** - External accounting software integration points

---

## 📋 Technical Debt

### Code Quality
- [ ] **Type Annotation Completion** - Add comprehensive type hints across all modules
- [ ] **Docstring Standardization** - Ensure all functions have proper documentation
- [ ] **Code Duplication Review** - Identify and refactor repeated code patterns

### Performance Optimization
- [ ] **Query Optimization Review** - Analyze slow queries in portfolio dashboard
- [ ] **Caching Strategy Enhancement** - Expand beyond current 15-minute portfolio cache
- [ ] **Database Indexing Review** - Ensure optimal indexing for all query patterns

### Architecture Improvements
- [ ] **Service Layer Expansion** - Move more business logic from routes to services
- [ ] **Model Validation Enhancement** - Add comprehensive model-level validation
- [ ] **Error Handling Centralization** - Implement consistent error handling patterns

---

## 🚀 Deployment Preparation

### Pre-Production Checklist
- [ ] **Resolve all High Priority issues**
- [ ] **Complete LSP diagnostic fixes**
- [ ] **Implement missing core routes**
- [ ] **Configure production database**
- [ ] **Set up email service**
- [ ] **Performance testing in production-like environment**

### Production Deployment
- [ ] **Environment Variable Documentation** - Complete list for production setup
- [ ] **Database Migration Scripts** - Ensure smooth production database setup
- [ ] **Monitoring Setup** - Application performance monitoring
- [ ] **Backup Strategy** - Database backup and recovery procedures
- [ ] **SSL Certificate Configuration** - HTTPS setup for production

---

## 📊 Progress Tracking

### Completed Recently ✅
- ✅ Multi-tenant architecture implementation
- ✅ SARS compliance calculations (2025/26)
- ✅ Employee lifecycle management
- ✅ Recurring deductions system
- ✅ PDF payslip generation
- ✅ Portfolio dashboard with caching
- ✅ Role-based access control
- ✅ Medical aid integration
- ✅ Compliance reminder system

### In Progress 🔄
- 🔄 LSP diagnostic resolution
- 🔄 Calendar integration planning
- 🔄 Missing route implementation

### Blocked 🚫
- None currently identified

---

## 📝 Notes & Decisions

### Recent Technical Decisions
- **Database**: Confirmed SQLite default with PostgreSQL production option
- **Caching**: Redis-backed caching with SimpleCache fallback verified working
- **Architecture**: Blueprint-based modular design confirmed effective
- **Testing**: Basic test suite exists, needs expansion

### User Experience Issues Identified
- **Employee Forms**: Multiple UX issues found in Add Employee form affecting user workflow
- **ID vs Passport**: Need toggle system for South African ID vs international passport entry
- **Contact Validation**: Cell number format validation needs South African standards (06x/07x/08x)
- **Form Logic**: Overtime eligibility validation blocking submission incorrectly
- **Field Placement**: Custom department input field appearing in wrong location

### Known Limitations
- Calendar integration is placeholder only
- Some reported routes don't exist but core functionality complete
- Email notifications ready but need SMTP configuration
- Export functionality exists for import but not standalone export
- Employee form has several UX issues affecting user experience
- Form validation inconsistencies between Add Employee and Employee Defaults
- SA ID vs Passport handling needs improvement for international employees

### Development Environment
- **Python Version**: 3.11+
- **Flask Version**: 3.x
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Caching**: Redis with fallback
- **Frontend**: Bootstrap + custom CSS
- **Testing**: pytest framework

---

## 🔧 Quick Reference

### Common Commands
```bash
# Run application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Database operations
flask db upgrade

# Testing
pytest

# LSP diagnostics check
# Use Replit LSP diagnostics tool
```

### Important Files
- `config.py` - Environment configuration
- `app/__init__.py` - Application factory
- `app/models/` - Database models
- `app/services/` - Business logic layer
- `app/routes/` - Route blueprints
- `replit.md` - Project documentation

---

*Issue tracking started: January 2025*  
*Next Review: Weekly*