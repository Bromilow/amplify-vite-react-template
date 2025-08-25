"""
Portfolio Service - Centralized data management for accountant portfolio dashboard
Optimizes database queries and provides caching for improved performance
"""
from flask import current_app
from app import db, cache
from app.models import Company, Employee, PayrollEntry, ComplianceReminder
from sqlalchemy import func, desc, case, and_, distinct
from datetime import datetime, timedelta
import calendar


class PortfolioService:
    """Service class for portfolio dashboard data management with query optimization"""

    CACHE_TIMEOUT = 900  # 15 minutes cache timeout

    @staticmethod
    def get_overview_data(user):
        """Compatibility wrapper returning dashboard data for a given user"""
        if not user:
            return {
                'company_data': [],
                'chart_data': {'labels': [], 'data': []},
                'upcoming_actions': [],
                'compliance_notifications': [],
                'compliance_metrics': {},
                'portfolio_reminders': [],
                'total_companies': 0,
                'total_employees': 0,
                'no_companies': True,
            }

        return PortfolioService.get_dashboard_data(user.id)

    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_portfolio_table_data(user_id):
        """
        Optimized query for portfolio table view with comprehensive company metrics
        Returns data specifically formatted for responsive table display
        """
        current_app.logger.debug(f"Fetching portfolio table data for user {user_id}")
        
        # Get user's company IDs first
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return []
            
        user_company_ids = [c.id for c in user.companies.all()]
        if not user_company_ids:
            return []
        
        # Enhanced query for table display
        results = db.session.query(
            Company.id,
            Company.name,
            Company.industry,
            func.count(distinct(Employee.id)).label('employee_count'),
            func.max(PayrollEntry.pay_period_end).label('last_payroll'),
            func.sum(case(
                (PayrollEntry.net_pay.isnot(None), PayrollEntry.net_pay),
                else_=0
            )).label('total_payroll'),
            func.count(case(
                (PayrollEntry.is_verified == False, PayrollEntry.id)
            )).label('unverified_entries'),
            func.count(case(
                (PayrollEntry.is_finalized == True, PayrollEntry.id)
            )).label('finalized_entries')
        ).select_from(Company)\
         .outerjoin(Employee, Company.id == Employee.company_id)\
         .outerjoin(PayrollEntry, Employee.id == PayrollEntry.employee_id)\
         .filter(Company.id.in_(user_company_ids))\
         .group_by(Company.id, Company.name, Company.industry)\
         .all()
        
        # Get compliance data
        compliance_data = {}
        if user_company_ids:
            today = datetime.now().date()
            compliance_results = db.session.query(
                ComplianceReminder.company_id,
                func.count(case(
                    (ComplianceReminder.due_date < today, ComplianceReminder.id)
                )).label('overdue_count'),
                func.count(case(
                    (and_(
                        ComplianceReminder.due_date >= today,
                        ComplianceReminder.due_date <= today + timedelta(days=7)
                    ), ComplianceReminder.id)
                )).label('upcoming_count')
            ).filter(
                ComplianceReminder.company_id.in_(user_company_ids),
                ComplianceReminder.is_active == True
            ).group_by(ComplianceReminder.company_id).all()
            
            compliance_data = {
                r.company_id: {
                    'overdue': r.overdue_count,
                    'upcoming': r.upcoming_count
                } for r in compliance_results
            }
        
        # Transform for table display
        table_data = []
        for result in results:
            # Determine payroll status
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            payroll_status = 'none'
            payroll_status_text = 'No Payroll'
            payroll_badge_class = 'bg-secondary'
            
            if result.last_payroll:
                if result.finalized_entries > 0:
                    payroll_status = 'finalized'
                    payroll_status_text = 'Finalized ✅'
                    payroll_badge_class = 'bg-success'
                elif result.unverified_entries > 0:
                    payroll_status = 'pending'
                    payroll_status_text = 'Pending ⏳'
                    payroll_badge_class = 'bg-warning'
                elif not result.last_payroll or result.last_payroll < current_month_start.date():
                    payroll_status = 'overdue'
                    payroll_status_text = 'Overdue ❌'
                    payroll_badge_class = 'bg-danger'
                else:
                    payroll_status = 'current'
                    payroll_status_text = 'Current'
                    payroll_badge_class = 'bg-info'
            
            # Get compliance info
            compliance_info = compliance_data.get(result.id, {'overdue': 0, 'upcoming': 0})
            compliance_status = 'Compliant'
            compliance_class = 'text-success'
            compliance_tooltip = 'All compliance items current'
            
            if compliance_info['overdue'] > 0:
                compliance_status = f"{compliance_info['overdue']} overdue"
                compliance_class = 'text-danger'
                compliance_tooltip = f"{compliance_info['overdue']} overdue compliance tasks"
            elif compliance_info['upcoming'] > 0:
                compliance_status = f"{compliance_info['upcoming']} due soon"
                compliance_class = 'text-warning'
                compliance_tooltip = f"{compliance_info['upcoming']} compliance tasks due within 7 days"
            
            table_data.append({
                'id': result.id,
                'name': result.name,
                'industry': result.industry or 'General',
                'employee_count': result.employee_count or 0,
                'last_payroll_date': result.last_payroll,
                'payroll_status': payroll_status,
                'payroll_status_text': payroll_status_text,
                'payroll_badge_class': payroll_badge_class,
                'compliance_status': compliance_status,
                'compliance_class': compliance_class,
                'compliance_tooltip': compliance_tooltip,
                'overdue_compliance': compliance_info['overdue'],
                'upcoming_compliance': compliance_info['upcoming']
            })
        
        return table_data

    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_portfolio_overview_data(user_id):
        """
        Optimized single query to fetch all company overview data
        Replaces N+1 query pattern with efficient JOINs
        """
        current_app.logger.debug(f"Fetching portfolio overview data for user {user_id}")
        
        # Get user's company IDs first
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return []
            
        user_company_ids = [c.id for c in user.companies.all()]
        if not user_company_ids:
            return []
        
        # Enhanced query with payroll totals and compliance data
        from app.models.employee_medical_aid_info import EmployeeMedicalAidInfo
        
        results = db.session.query(
            Company.id,
            Company.name,
            Company.industry,
            func.count(distinct(Employee.id)).label('employee_count'),
            func.max(PayrollEntry.pay_period_end).label('last_payroll'),
            func.count(case(
                (Employee.tax_number.is_(None), Employee.id)
            )).label('missing_tax_numbers'),
            func.count(case(
                (and_(
                    Employee.medical_aid_member == True,
                    EmployeeMedicalAidInfo.id.is_(None)
                ), Employee.id)
            )).label('missing_medical_aid'),
            func.sum(case(
                (PayrollEntry.net_pay.isnot(None), PayrollEntry.net_pay),
                else_=0
            )).label('total_payroll'),
            func.count(case(
                (PayrollEntry.is_verified == False, PayrollEntry.id)
            )).label('unverified_entries'),
            func.count(case(
                (PayrollEntry.is_finalized == True, PayrollEntry.id)
            )).label('finalized_entries')
        ).select_from(Company)\
         .outerjoin(Employee, Company.id == Employee.company_id)\
         .outerjoin(EmployeeMedicalAidInfo, Employee.id == EmployeeMedicalAidInfo.employee_id)\
         .outerjoin(PayrollEntry, Employee.id == PayrollEntry.employee_id)\
         .filter(Company.id.in_(user_company_ids))\
         .group_by(Company.id, Company.name, Company.industry)\
         .all()
        
        # Get compliance data in separate query for better performance
        compliance_data = {}
        if user_company_ids:
            today = datetime.now().date()
            compliance_results = db.session.query(
                ComplianceReminder.company_id,
                func.count(case(
                    (ComplianceReminder.due_date < today, ComplianceReminder.id)
                )).label('overdue_count')
            ).filter(
                ComplianceReminder.company_id.in_(user_company_ids),
                ComplianceReminder.is_active == True
            ).group_by(ComplianceReminder.company_id).all()
            
            compliance_data = {r.company_id: r.overdue_count for r in compliance_results}
        
        # Transform results to dictionary format with enhanced data
        company_data = []
        total_employees = 0
        
        for result in results:
            # Calculate pending issues from aggregated data
            pending_issues = result.missing_tax_numbers
            if result.missing_medical_aid:
                pending_issues += result.missing_medical_aid
            
            # Check if payroll is missing this month
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            payroll_overdue = False
            if result.employee_count > 0:
                if not result.last_payroll or result.last_payroll < current_month_start.date():
                    pending_issues += 1
                    payroll_overdue = True
            
            # Determine payroll status and badge class
            payroll_status = 'none'
            payroll_status_text = 'No Payroll'
            payroll_badge_class = 'bg-secondary'
            
            if result.last_payroll:
                if result.finalized_entries > 0:
                    payroll_status = 'finalized'
                    payroll_status_text = 'Finalized'
                    payroll_badge_class = 'bg-success'
                elif result.unverified_entries > 0:
                    payroll_status = 'pending'
                    payroll_status_text = 'Pending'
                    payroll_badge_class = 'bg-warning'
                elif payroll_overdue:
                    payroll_status = 'overdue'
                    payroll_status_text = 'Overdue'
                    payroll_badge_class = 'bg-danger'
                else:
                    payroll_status = 'current'
                    payroll_status_text = 'Current'
                    payroll_badge_class = 'bg-info'
            
            # Calculate estimated monthly payroll (average of last 3 months)
            monthly_estimate = 0
            if result.total_payroll:
                # Simple estimate: total payroll divided by number of months with data
                months_with_data = 3  # Assume 3 months of data for estimation
                monthly_estimate = float(result.total_payroll) / months_with_data
            
            # Get compliance status with CSS class and tooltip
            overdue_compliance = compliance_data.get(result.id, 0)
            compliance_status = overdue_compliance == 0
            
            if compliance_status:
                compliance_class = 'text-success'
                compliance_tooltip = 'All compliance requirements up to date'
            elif overdue_compliance > 0:
                compliance_class = 'text-danger'
                compliance_tooltip = f'{overdue_compliance} overdue compliance item(s)'
            else:
                compliance_class = 'text-muted'
                compliance_tooltip = 'No compliance data available'
            
            company_data.append({
                'id': result.id,
                'name': result.name,
                'industry': result.industry,
                'employee_count': result.employee_count or 0,
                'last_payroll_date': result.last_payroll,
                'pending_issues': pending_issues,
                'payroll_status': payroll_status,
                'payroll_status_text': payroll_status_text,
                'payroll_badge_class': payroll_badge_class,
                'monthly_estimate': monthly_estimate,
                'compliance_status': compliance_status,
                'compliance_class': compliance_class,
                'compliance_tooltip': compliance_tooltip,
                'overdue_compliance': overdue_compliance,
                'total_payroll': float(result.total_payroll) if result.total_payroll else 0,
                'finalized_entries': result.finalized_entries or 0,
                'unverified_entries': result.unverified_entries or 0
            })
            
            total_employees += result.employee_count or 0
        
        current_app.logger.debug(f"Portfolio overview: {len(company_data)} companies, {total_employees} total employees")
        return company_data, total_employees

    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_notifications_count(user_id):
        """
        Get count of unresolved notifications for compliance dashboard
        Returns count of active ReminderNotification records for the user
        """
        current_app.logger.debug(f"Fetching notifications count for user {user_id}")
        
        from app.models.reminder_notification import ReminderNotification
        
        # Count unread notifications for the user
        count = db.session.query(ReminderNotification)\
            .filter_by(user_id=user_id, is_read=False)\
            .count()
        
        current_app.logger.debug(f"Found {count} unread notifications for user {user_id}")
        return count

    
    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_compliance_metrics_optimized(user_id):
        """
        Optimized compliance metrics calculation using SQL aggregation
        Replaces multiple Python loops with database-level calculations
        """
        current_app.logger.debug(f"Fetching compliance metrics for user {user_id}")
        
        # Get user's company IDs
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return {
                'overdue_count': 0,
                'this_week_count': 0,
                'compliant_companies': 0,
                'total_active': 0
            }
            
        user_company_ids = [c.id for c in user.companies.all()]
        if not user_company_ids:
            return {
                'overdue_count': 0,
                'this_week_count': 0,
                'compliant_companies': 0,
                'total_active': 0
            }
        
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        
        # Single query to get all compliance metrics
        metrics = db.session.query(
            func.count(case(
                (ComplianceReminder.due_date < today, ComplianceReminder.id)
            )).label('overdue_count'),
            func.count(case(
                (and_(
                    ComplianceReminder.due_date >= today,
                    ComplianceReminder.due_date <= week_from_now
                ), ComplianceReminder.id)
            )).label('this_week_count'),
            func.count(ComplianceReminder.id).label('total_active'),
            func.count(distinct(ComplianceReminder.company_id)).label('companies_with_reminders')
        ).filter(
            ComplianceReminder.company_id.in_(user_company_ids),
            ComplianceReminder.is_active == True
        ).first()
        
        # Calculate compliant companies (companies with no overdue reminders)
        companies_with_overdue = db.session.query(
            func.count(distinct(ComplianceReminder.company_id))
        ).filter(
            ComplianceReminder.company_id.in_(user_company_ids),
            ComplianceReminder.is_active == True,
            ComplianceReminder.due_date < today
        ).scalar()
        
        total_companies = len(user_company_ids)
        compliant_companies = total_companies - (companies_with_overdue or 0)
        
        result = {
            'overdue_count': metrics.overdue_count or 0,
            'this_week_count': metrics.this_week_count or 0,
            'compliant_companies': compliant_companies,
            'total_active': metrics.total_active or 0
        }
        
        current_app.logger.debug(f"Compliance metrics: {result}")
        return result
    
    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_upcoming_payroll_actions_optimized(user_id):
        """
        Optimized payroll actions calculation with bulk company processing
        """
        current_app.logger.debug(f"Fetching payroll actions for user {user_id}")
        
        # Get user's companies with employee counts in single query
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return []
            
        user_company_ids = [c.id for c in user.companies.all()]
        if not user_company_ids:
            return []
        
        # Get companies with payroll status in single query
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        company_payroll_status = db.session.query(
            Company.id,
            Company.name,
            func.count(distinct(Employee.id)).label('employee_count'),
            func.count(distinct(case(
                (PayrollEntry.pay_period_end >= current_month_start.date(), PayrollEntry.id)
            ))).label('payroll_entries_this_month')
        ).select_from(Company)\
         .outerjoin(Employee, Company.id == Employee.company_id)\
         .outerjoin(PayrollEntry, Employee.id == PayrollEntry.employee_id)\
         .filter(Company.id.in_(user_company_ids))\
         .group_by(Company.id, Company.name)\
         .all()
        
        actions = []
        today = datetime.now().date()
        
        for company_status in company_payroll_status:
            # Only process companies with employees that haven't run payroll
            if (company_status.employee_count > 0 and 
                company_status.payroll_entries_this_month == 0):
                
                # Calculate month-end due date
                last_day = calendar.monthrange(today.year, today.month)[1]
                month_end = today.replace(day=last_day)
                days_until_due = (month_end - today).days
                
                actions.append({
                    'company_name': company_status.name,
                    'company_id': company_status.id,
                    'action': 'Monthly Payroll Processing',
                    'due_date': month_end,
                    'days_until': days_until_due,
                    'priority': 'high' if days_until_due <= 3 else 'medium' if days_until_due <= 7 else 'low'
                })
        
        # Sort by due date
        actions.sort(key=lambda x: x['due_date'])
        current_app.logger.debug(f"Upcoming payroll actions: {len(actions)} companies need processing")
        return actions
    
    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_compliance_notifications_optimized(user_id):
        """
        Optimized compliance notifications with bulk data processing
        """
        current_app.logger.debug(f"Fetching compliance notifications for user {user_id}")
        
        # Get user's companies
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return []
            
        user_company_ids = [c.id for c in user.companies.all()]
        if not user_company_ids:
            return []
        
        # Single query to get all notification-relevant data
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        from app.models.employee_medical_aid_info import EmployeeMedicalAidInfo
        
        notification_data = db.session.query(
            Company.id,
            Company.name,
            func.count(distinct(Employee.id)).label('total_employees'),
            func.count(distinct(case(
                (Employee.tax_number.is_(None), Employee.id)
            ))).label('missing_tax_numbers'),
            func.count(distinct(case(
                (and_(
                    Employee.medical_aid_member == True,
                    EmployeeMedicalAidInfo.id.is_(None)
                ), Employee.id)
            ))).label('missing_medical_aid'),
            func.count(distinct(case(
                (PayrollEntry.pay_period_end >= current_month_start.date(), PayrollEntry.id)
            ))).label('payroll_entries_this_month')
        ).select_from(Company)\
         .outerjoin(Employee, Company.id == Employee.company_id)\
         .outerjoin(EmployeeMedicalAidInfo, Employee.id == EmployeeMedicalAidInfo.employee_id)\
         .outerjoin(PayrollEntry, Employee.id == PayrollEntry.employee_id)\
         .filter(Company.id.in_(user_company_ids))\
         .group_by(Company.id, Company.name)\
         .all()
        
        notifications = []
        
        for data in notification_data:
            # Missing tax numbers notification
            if data.missing_tax_numbers > 0:
                notifications.append({
                    'type': 'warning',
                    'company_name': data.name,
                    'company_id': data.id,
                    'title': 'Missing Tax Numbers',
                    'message': f'{data.missing_tax_numbers} employee(s) missing tax numbers',
                    'action': 'Update Employee Records'
                })
            
            # Overdue payroll notification (after 25th of month)
            if (data.total_employees > 0 and 
                data.payroll_entries_this_month == 0 and 
                datetime.now().day > 25):
                notifications.append({
                    'type': 'danger',
                    'company_name': data.name,
                    'company_id': data.id,
                    'title': 'Payroll Overdue',
                    'message': 'Monthly payroll not processed',
                    'action': 'Process payroll immediately'
                })
            
            # Missing medical aid details notification
            if data.missing_medical_aid > 0:
                notifications.append({
                    'type': 'info',
                    'company_name': data.name,
                    'company_id': data.id,
                    'title': 'Medical Aid Details',
                    'message': f'{data.missing_medical_aid} employee(s) with medical aid contributions need scheme names',
                    'action': 'Update medical aid details'
                })
        
        current_app.logger.debug(f"Compliance notifications: {len(notifications)} issues found")
        return notifications
    
    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUT)
    def get_portfolio_reminders_optimized(user_id):
        """
        Optimized portfolio reminders with company name JOIN
        """
        current_app.logger.debug(f"Fetching portfolio reminders for user {user_id}")
        
        # Get user's companies
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return []
            
        user_company_ids = [c.id for c in user.companies.all()]
        if not user_company_ids:
            return []
        
        # Single query with company name JOIN
        reminders_data = db.session.query(
            ComplianceReminder.id,
            ComplianceReminder.title,
            ComplianceReminder.due_date,
            ComplianceReminder.category,
            ComplianceReminder.description,
            Company.name.label('company_name')
        ).join(Company, ComplianceReminder.company_id == Company.id)\
         .filter(
             ComplianceReminder.company_id.in_(user_company_ids),
             ComplianceReminder.is_active == True
         ).all()
        
        events = []
        today = datetime.now().date()
        
        for reminder in reminders_data:
            # Determine status and styling
            if reminder.due_date < today:
                status = 'overdue'
                color = '#dc3545'  # Bootstrap danger red
                text_color = '#ffffff'
                class_name = 'fc-event-overdue'
            elif reminder.due_date <= today + timedelta(days=7):
                status = 'due_soon'
                color = '#fd7e14'  # Bootstrap warning orange
                text_color = '#ffffff'
                class_name = 'fc-event-due-soon'
            else:
                status = 'upcoming'
                color = '#28a745'  # Bootstrap success green
                text_color = '#ffffff'
                class_name = 'fc-event-upcoming'
            
            # Category-specific styling
            category_colors = {
                'tax': '#dc3545',      # Red
                'payroll': '#fd7e14',  # Orange
                'employment': '#ffc107', # Yellow
                'custom': '#6f42c1'    # Purple
            }
            
            if reminder.category in category_colors:
                color = category_colors[reminder.category]
            
            events.append({
                'id': f'reminder_{reminder.id}',
                'title': reminder.title,
                'start': reminder.due_date.isoformat(),
                'color': color,
                'textColor': text_color,
                'className': class_name,
                'extendedProps': {
                    'category': reminder.category,
                    'description': reminder.description or '',
                    'company_name': reminder.company_name,
                    'status': status,
                    'reminder_id': reminder.id
                }
            })
        
        current_app.logger.debug(f"Portfolio reminders: {len(events)} events generated")
        return events
    
    @staticmethod
    def get_dashboard_data(user_id):
        """
        Main method to fetch all dashboard data efficiently
        Uses optimized service methods with caching
        """
        current_app.logger.info(f"Fetching complete dashboard data for user {user_id}")
        
        # Fetch all data using optimized methods
        company_data, total_employees = PortfolioService.get_portfolio_overview_data(user_id)
        compliance_metrics = PortfolioService.get_compliance_metrics_optimized(user_id)
        upcoming_actions = PortfolioService.get_upcoming_payroll_actions_optimized(user_id)
        compliance_notifications = PortfolioService.get_compliance_notifications_optimized(user_id)
        portfolio_reminders = PortfolioService.get_portfolio_reminders_optimized(user_id)
        
        # Generate chart data
        chart_data = {
            'labels': [company['name'] for company in company_data],
            'data': [company['employee_count'] for company in company_data]
        }
        
        result = {
            'company_data': company_data,
            'chart_data': chart_data,
            'upcoming_actions': upcoming_actions,
            'compliance_notifications': compliance_notifications,
            'compliance_metrics': compliance_metrics,
            'portfolio_reminders': portfolio_reminders,
            'total_companies': len(company_data),
            'total_employees': total_employees,
            'no_companies': len(company_data) == 0
        }
        
        current_app.logger.info(f"Dashboard data compiled: {len(company_data)} companies, {total_employees} employees, {len(upcoming_actions)} actions, {len(compliance_notifications)} notifications")
        return result
    
    @staticmethod
    def clear_user_cache(user_id):
        """Clear cached data for a specific user"""
        cache_keys = [
            f"portfolio_overview_data_{user_id}",
            f"compliance_metrics_optimized_{user_id}",
            f"upcoming_payroll_actions_optimized_{user_id}",
            f"compliance_notifications_optimized_{user_id}",
            f"portfolio_reminders_optimized_{user_id}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        current_app.logger.info(f"Cleared cache for user {user_id}")
    
    @staticmethod
    def clear_all_cache():
        """Clear all portfolio dashboard cache"""
        cache.clear()
        current_app.logger.info("Cleared all portfolio dashboard cache")