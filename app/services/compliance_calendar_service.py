from app.models.compliance import ComplianceReminderRule
from app.models.company import Company
from datetime import date, datetime, timedelta
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)


class ComplianceCalendarService:
    """Service for generating dynamic compliance calendar events from system rules"""
    
    @staticmethod
    def generate_company_compliance_events(company_id, start_date=None, end_date=None):
        """
        Generate compliance events for a specific company based on system rules
        
        Args:
            company_id: Company ID to generate events for
            start_date: Start date for event generation (default: current month)
            end_date: End date for event generation (default: 12 months ahead)
        
        Returns:
            List of calendar event dictionaries
        """
        if start_date is None:
            start_date = date.today().replace(day=1)  # First day of current month
        
        if end_date is None:
            end_date = start_date.replace(year=start_date.year + 1)  # 12 months ahead
        
        company = Company.query.get(company_id)
        if not company:
            logger.warning(f"Company {company_id} not found")
            return []
        
        events = []
        
        # Get applicable rules for companies
        company_rules = ComplianceReminderRule.get_rules_by_scope('company')
        
        # Generate events for each rule
        for rule in company_rules:
            rule_events = ComplianceCalendarService._generate_rule_events(
                rule, company, start_date, end_date
            )
            events.extend(rule_events)
        
        logger.info(f"Generated {len(events)} compliance events for company {company_id}")
        return events
    
    @staticmethod
    def generate_portfolio_compliance_events(company_ids, start_date=None, end_date=None):
        """
        Generate compliance events for multiple companies (portfolio view)
        
        Args:
            company_ids: List of company IDs
            start_date: Start date for event generation
            end_date: End date for event generation
        
        Returns:
            List of calendar event dictionaries with company context
        """
        all_events = []
        
        for company_id in company_ids:
            company_events = ComplianceCalendarService.generate_company_compliance_events(
                company_id, start_date, end_date
            )
            all_events.extend(company_events)
        
        # Sort events by date
        all_events.sort(key=lambda x: x['start'])
        
        logger.info(f"Generated {len(all_events)} total compliance events for {len(company_ids)} companies")
        return all_events

    @staticmethod
    def generate_due_dates(rule, year):
        """Return list of due dates for the given rule in the specified year."""
        dates = []
        if rule.frequency == 'monthly':
            for month in range(1, 13):
                last_day = monthrange(year, month)[1]
                day = min(rule.due_day, last_day)
                dates.append(date(year, month, day))
        elif rule.frequency == 'annual':
            if rule.due_month:
                months = [rule.due_month]
            else:
                months = [1]
            for m in months:
                last_day = monthrange(year, m)[1]
                day = min(rule.due_day, last_day)
                dates.append(date(year, m, day))
        elif rule.frequency == 'biannual':
            first = rule.due_month or 1
            months = [first, (first + 5) % 12 + 1]
            for m in months:
                last_day = monthrange(year, m)[1]
                day = min(rule.due_day, last_day)
                dates.append(date(year, m, day))
        return dates
    
    @staticmethod
    def _generate_rule_events(rule, company, start_date, end_date):
        """
        Generate events for a specific compliance rule within date range
        
        Args:
            rule: ComplianceReminderRule instance
            company: Company instance
            start_date: Start date for generation
            end_date: End date for generation
        
        Returns:
            List of event dictionaries
        """
        events = []
        for year in range(start_date.year, end_date.year + 1):
            for due_date in ComplianceCalendarService.generate_due_dates(rule, year):
                if start_date <= due_date <= end_date:
                    events.append(
                        ComplianceCalendarService._create_event_dict(rule, company, due_date)
                    )

        return events
    
    @staticmethod
    def _create_event_dict(rule, company, event_date):
        """
        Create calendar event dictionary from rule and date
        
        Args:
            rule: ComplianceReminderRule instance
            company: Company instance
            event_date: Date for the event
        
        Returns:
            Dictionary with FullCalendar-compatible event structure
        """
        # Determine event color based on category/type
        color_map = {
            'monthly': '#17a2b8',    # Info blue
            'annual': '#dc3545',     # Danger red
            'biannual': '#fd7e14',   # Warning orange
            'event': '#6f42c1'       # Purple
        }
        
        # Check if event is overdue
        is_overdue = event_date < date.today()
        
        # Determine status and styling
        if is_overdue:
            background_color = '#dc3545'  # Red for overdue
            border_color = '#dc3545'
            text_color = '#ffffff'
            class_names = ['compliance-event', 'overdue']
        else:
            days_until = (event_date - date.today()).days
            if days_until <= 7:
                background_color = '#fd7e14'  # Orange for due soon
                border_color = '#fd7e14'
                text_color = '#ffffff'
                class_names = ['compliance-event', 'due-soon']
            else:
                background_color = color_map.get(rule.frequency, '#6c757d')
                border_color = background_color
                text_color = '#ffffff'
                class_names = ['compliance-event', 'upcoming']
        
        return {
            'id': f"rule_{rule.id}_{company.id}_{event_date.isoformat()}",
            'title': rule.title,
            'start': event_date.isoformat(),
            'allDay': True,
            'backgroundColor': background_color,
            'borderColor': border_color,
            'textColor': text_color,
            'classNames': class_names,
            'extendedProps': {
                'rule_id': rule.id,
                'company_id': company.id,
                'company_name': company.name,
                'description': rule.description,
                'frequency': rule.frequency,
                'applies_to': rule.applies_to,
                'is_overdue': is_overdue,
                'days_until': (event_date - date.today()).days,
                'type': 'compliance_rule'
            }
        }
    
    @staticmethod
    def get_calendar_events(user_id, start_date=None, end_date=None):
        """
        Get all calendar events for a user's portfolio
        
        Args:
            user_id: User ID to get companies for
            start_date: Start date for event generation (default: today)
            end_date: End date for event generation (default: 3 months ahead)
        
        Returns:
            List of calendar event dictionaries
        """
        from app.models.user import User
        
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return []
        
        # Get user's companies
        company_ids = [company.id for company in user.companies.all()]
        
        if not company_ids:
            logger.info(f"No companies found for user {user_id}")
            return []
        
        # Set default date range
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date + timedelta(days=90)
        
        # Generate compliance events
        events = ComplianceCalendarService.generate_portfolio_compliance_events(
            company_ids, start_date, end_date
        )
        
        # De-duplicate events by (rule_id, due_date) and combine companies
        deduplicated_events = ComplianceCalendarService._deduplicate_calendar_events(events)
        
        logger.info(f"Generated {len(events)} calendar events, de-duplicated to {len(deduplicated_events)} for user {user_id}")
        return deduplicated_events
    
    @staticmethod
    def _deduplicate_calendar_events(events):
        """
        De-duplicate calendar events by (rule_id, due_date) and combine companies
        
        Args:
            events: List of calendar event dictionaries
            
        Returns:
            List of de-duplicated events with companies combined
        """
        event_groups = {}
        
        for event in events:
            # Create unique key from rule_id and start date
            rule_id = event['extendedProps']['rule_id']
            start_date = event['start']
            key = f"{rule_id}_{start_date}"
            
            if key not in event_groups:
                # First event for this rule+date combination
                event_groups[key] = event.copy()
                # Convert company data to list format
                event_groups[key]['extendedProps']['companies'] = [{
                    'id': event['extendedProps']['company_id'],
                    'name': event['extendedProps']['company_name']
                }]
                # Remove individual company fields
                del event_groups[key]['extendedProps']['company_id']
                del event_groups[key]['extendedProps']['company_name']
            else:
                # Add company to existing event
                event_groups[key]['extendedProps']['companies'].append({
                    'id': event['extendedProps']['company_id'],
                    'name': event['extendedProps']['company_name']
                })
        
        # Convert back to list and update event IDs
        deduplicated_events = []
        for key, event in event_groups.items():
            # Update event ID to reflect multiple companies
            company_count = len(event['extendedProps']['companies'])
            event['id'] = f"{key}_companies_{company_count}"
            deduplicated_events.append(event)
        
        return deduplicated_events

    @staticmethod
    def get_company_calendar_events(company_id, start_date=None, end_date=None):
        """
        Get compliance calendar events for a specific company
        
        Args:
            company_id: Company ID to get events for
            start_date: Start date for event generation (default: today)
            end_date: End date for event generation (default: 3 months ahead)
        
        Returns:
            List of calendar event dictionaries for the company
        """
        # Set default date range
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date + timedelta(days=90)
        
        # Generate compliance events for single company
        events = ComplianceCalendarService.generate_portfolio_compliance_events(
            [company_id], start_date, end_date
        )
        
        logger.info(f"Generated {len(events)} compliance events for company {company_id}")
        return events

    @staticmethod
    def get_upcoming_deadlines(company_ids, days_ahead=30):
        """
        Get upcoming compliance deadlines for dashboard widgets
        
        Args:
            company_ids: List of company IDs
            days_ahead: Number of days to look ahead (default: 30)
        
        Returns:
            List of upcoming deadline dictionaries
        """
        end_date = date.today() + timedelta(days=days_ahead)
        
        events = ComplianceCalendarService.generate_portfolio_compliance_events(
            company_ids, date.today(), end_date
        )
        
        # Filter and format for dashboard display
        upcoming = []
        for event in events:
            event_date = datetime.fromisoformat(event['start']).date()
            days_until = (event_date - date.today()).days
            
            upcoming.append({
                'title': event['title'],
                'company_name': event['extendedProps']['company_name'],
                'due_date': event_date,
                'days_until': days_until,
                'is_overdue': days_until < 0,
                'is_due_soon': 0 <= days_until <= 7,
                'frequency': event['extendedProps']['frequency'],
                'description': event['extendedProps']['description']
            })
        
        # Sort by days until due
        upcoming.sort(key=lambda x: x['days_until'])
        
        return upcoming
    
    @staticmethod
    def get_compliance_summary(company_ids):
        """
        Get compliance summary statistics for dashboard metrics
        
        Args:
            company_ids: List of company IDs
        
        Returns:
            Dictionary with compliance metrics
        """
        # Get next 30 days of events
        events = ComplianceCalendarService.generate_portfolio_compliance_events(
            company_ids, date.today(), date.today() + timedelta(days=30)
        )
        
        overdue_count = 0
        due_this_week = 0
        due_this_month = 0
        
        today = date.today()
        week_end = today + timedelta(days=7)
        month_end = today + timedelta(days=30)
        
        for event in events:
            event_date = datetime.fromisoformat(event['start']).date()
            days_until = (event_date - today).days
            
            if days_until < 0:
                overdue_count += 1
            elif days_until <= 7:
                due_this_week += 1
            elif days_until <= 30:
                due_this_month += 1
        
        return {
            'overdue_count': overdue_count,
            'due_this_week': due_this_week,
            'due_this_month': due_this_month,
            'total_upcoming': len(events)
        }