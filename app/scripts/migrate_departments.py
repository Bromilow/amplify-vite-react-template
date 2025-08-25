#!/usr/bin/env python3
"""
Migration script to populate CompanyDepartment table for existing companies
and migrate existing employee department values.
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app, db
from app.models.company import Company
from app.models.employee import Employee
from app.models.company_department import CompanyDepartment

def migrate_departments():
    """Migrate departments for all existing companies"""
    app = create_app()
    
    with app.app_context():
        print("Starting department migration...")
        
        # Get all companies
        companies = Company.query.all()
        print(f"Found {len(companies)} companies to migrate")
        
        for company in companies:
            print(f"\nMigrating company: {company.name} (ID: {company.id})")
            
            # Check if this company already has departments
            existing_depts = CompanyDepartment.query.filter_by(company_id=company.id).count()
            if existing_depts > 0:
                print(f"  Company already has {existing_depts} departments, skipping default seeding")
            else:
                # Seed default departments
                print("  Seeding default departments...")
                CompanyDepartment.seed_default_departments(company.id)
                print("  ✓ Default departments seeded")
            
            # Get unique departments from existing employees
            employee_departments = db.session.query(Employee.department)\
                .filter(Employee.company_id == company.id)\
                .filter(Employee.department.isnot(None))\
                .filter(Employee.department != '')\
                .distinct().all()
            
            employee_dept_names = [dept[0] for dept in employee_departments if dept[0]]
            print(f"  Found {len(employee_dept_names)} unique departments in employee records: {employee_dept_names}")
            
            # Create departments that don't exist yet
            for dept_name in employee_dept_names:
                existing = CompanyDepartment.query.filter_by(
                    company_id=company.id,
                    name=dept_name
                ).first()
                
                if not existing:
                    print(f"    Creating department: {dept_name}")
                    new_dept = CompanyDepartment(
                        company_id=company.id,
                        name=dept_name,
                        is_default=False  # These are custom departments from existing data
                    )
                    db.session.add(new_dept)
                else:
                    print(f"    Department already exists: {dept_name}")
            
            try:
                db.session.commit()
                print(f"  ✓ Company {company.name} migration completed")
            except Exception as e:
                db.session.rollback()
                print(f"  ✗ Error migrating company {company.name}: {str(e)}")
        
        # Final summary
        print(f"\n=== Migration Summary ===")
        total_companies = Company.query.count()
        total_departments = CompanyDepartment.query.count()
        print(f"Total companies: {total_companies}")
        print(f"Total departments created: {total_departments}")
        
        # Show department counts per company
        for company in Company.query.all():
            dept_count = CompanyDepartment.query.filter_by(company_id=company.id).count()
            print(f"  {company.name}: {dept_count} departments")

if __name__ == '__main__':
    migrate_departments()