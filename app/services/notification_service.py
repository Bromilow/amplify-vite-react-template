from app.models import ComplianceReminder, ReminderNotification, User, Company
from app import db
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing compliance reminder notifications"""
    
    @staticmethod
    def scan_and_dispatch_reminders():
        """
        Scan all active compliance reminders and dispatch notifications
        for those due within reminder_days
        """
        today = date.today()
        notifications_sent = 0
        
        try:
            # Get all active reminders
            active_reminders = ComplianceReminder.query.filter_by(is_active=True).all()
            
            for reminder in active_reminders:
                # Check if reminder is due within any of the reminder_days
                days_until_due = reminder.days_until_due()
                reminder_days_list = reminder.get_reminder_days()
                
                if days_until_due is not None and reminder_days_list:
                    # Check if today matches any reminder day
                    if days_until_due in reminder_days_list and days_until_due >= 0:
                        # Get users who should receive notifications for this company
                        company_users = NotificationService._get_notification_recipients(reminder.company_id)
                        
                        for user in company_users:
                            # Create notification
                            title = f"Compliance Reminder: {reminder.title}"
                            
                            if days_until_due == 0:
                                message = f"'{reminder.title}' is due today ({reminder.due_date.strftime('%d %B %Y')})."
                            elif days_until_due == 1:
                                message = f"'{reminder.title}' is due tomorrow ({reminder.due_date.strftime('%d %B %Y')})."
                            else:
                                message = f"'{reminder.title}' is due in {days_until_due} days ({reminder.due_date.strftime('%d %B %Y')})."
                            
                            if reminder.description:
                                message += f" Description: {reminder.description}"
                            
                            notification = ReminderNotification.create_notification(
                                user_id=user.id,
                                reminder_id=reminder.id,
                                title=title,
                                message=message
                            )
                            
                            if notification:
                                notifications_sent += 1
                                logger.info(f"Created notification for user {user.id}, reminder {reminder.id}")
                        
                        # Send email notifications if enabled
                        recipient_emails = [u.email for u in company_users if u.email]
                        if recipient_emails:
                            NotificationService._send_email_notifications(reminder, recipient_emails)
            
            logger.info(f"Notification scan completed. {notifications_sent} notifications created.")
            return notifications_sent
            
        except Exception as e:
            logger.error(f"Error during notification scan: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def _get_notification_recipients(company_id):
        """Get users who should receive notifications for a company"""
        # Get company owner and accountants who have access to this company
        company = Company.query.get(company_id)
        if not company:
            return []
        
        recipients = []
        
        # Add all users associated with this company
        for user in company.users:
            if user.is_admin or user.is_accountant:
                recipients.append(user)
        
        return recipients
    
    @staticmethod
    def _send_email_notifications(reminder, recipients):
        """Send email notifications for compliance reminders"""
        from app.services.email import send_email

        subject = f"Reminder: {reminder.title}"
        body = (
            f"This reminder is due on {reminder.due_date.strftime('%Y-%m-%d')}.\n\n"
            f"{reminder.description or ''}"
        )

        for email in recipients:
            send_email(subject, body, [email])
    
    @staticmethod
    def mark_notification_as_read(notification_id, user_id):
        """Mark a specific notification as read"""
        notification = ReminderNotification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.mark_as_read()
            return True
        return False
    
    @staticmethod
    def mark_all_notifications_as_read(user_id):
        """Mark all notifications as read for a user"""
        notifications = ReminderNotification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return len(notifications)
    
    @staticmethod
    def get_dashboard_notifications(user_id, limit=5):
        """Get recent notifications for dashboard display"""
        return ReminderNotification.get_recent_for_user(user_id, limit)
    
    @staticmethod
    def cleanup_old_notifications(days_old=30):
        """Clean up notifications older than specified days"""
        cutoff_date = date.today() - timedelta(days=days_old)
        
        old_notifications = ReminderNotification.query.filter(
            db.func.date(ReminderNotification.created_at) < cutoff_date
        ).all()
        
        count = len(old_notifications)
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        logger.info(f"Cleaned up {count} old notifications")
        return count
