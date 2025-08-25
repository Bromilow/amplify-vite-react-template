# Payroll Management System

## Overview

This Flask-based web application is designed for comprehensive employee payroll management. It offers functionalities for employee lifecycle management, automated payroll calculations, and detailed reporting through an intuitive web interface. The system aims to streamline payroll processes for businesses, ensuring compliance and providing a user-friendly experience.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap with Replit dark theme for responsive design
- **Icons**: Font Awesome
- **Styling**: Custom CSS for dark theme support

### Backend
- **Framework**: Flask with application factory pattern and Blueprint-based modular structure
- **Database ORM**: SQLAlchemy with declarative base
- **Configuration**: Environment-based system
- **Deployment**: Gunicorn WSGI server

### Database
- **Primary Database**: SQLite (development), PostgreSQL (production)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Connection Pooling**: Configured for efficiency
- **Migration Strategy**: Built-in table creation and data initialization

### Core Components
- **Models**: Employee, Company, User, PayrollEntry, Beneficiary, EmployeeRecurringDeduction, ComplianceReminder, DocumentTemplate, GlobalSARSConfig, SARSConfig, ComplianceReminderRule, CompanyDepartment
- **Services**: EmployeeService, PortfolioService, NotificationService, SARSService, handling business logic, data aggregation, and calculations.
- **Routes (Blueprints)**: Dashboard, Employees, Payroll, Company Management, Authentication, Admin, Reports.
- **Templates**: Modular and reusable Jinja2 templates for various sections like dashboard, employee management, payroll processing, and reports.

### Key Features
- **Multi-tenancy**: Supports multiple companies with isolated data and role-based access control.
- **Employee Management**: Comprehensive CRUD operations, detailed profiles, and lifecycle management (hire, terminate, reinstate).
- **Payroll Processing**: Automated calculations (gross, net, deductions), SARS compliance (PAYE, UIF, SDL, medical aid credits), and dynamic payslip generation (PDF).
- **Recurring Deductions**: Configurable system for automated deductions linked to beneficiaries.
- **Compliance Management**: Dynamic SARS configuration, compliance reminders, and a portfolio dashboard for accountants with aggregated compliance status.
- **Reporting & Exports**: Comprehensive reports for payroll, leave, deductions, and EFT file generation.
- **User Authentication**: Flask-Login integrated with secure registration and session management.
- **Document Generation**: Automated generation of compliance documents (e.g., UI19) from templates.

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: ORM integration
- **Gunicorn**: WSGI server
- **psycopg2-binary**: PostgreSQL adapter
- **email-validator**: Email validation
- **WeasyPrint**: PDF generation from HTML
- **python-docx**: DOCX file manipulation
- **docx2pdf**: DOCX to PDF conversion
- **schedule**: Python job scheduling library

### Frontend Libraries
- **Bootstrap**: UI framework (via CDN)
- **Font Awesome**: Icon library (via CDN)
- **Chart.js**: Data visualization
- **FullCalendar.js**: Interactive calendar
- **Inputmask.js**: Input formatting and validation