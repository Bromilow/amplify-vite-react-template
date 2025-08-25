import schedule
import time
import threading
from datetime import datetime
import logging
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Scheduler for compliance reminder notifications"""
    
    def __init__(self):
        self.scheduler_thread = None
        self.running = False
    
    def start_scheduler(self):
        """Start the notification scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule daily notification scan at 6:00 AM
        schedule.every().day.at("06:00").do(self._run_notification_scan)
        
        # Schedule cleanup of old notifications weekly
        schedule.every().sunday.at("02:00").do(self._cleanup_old_notifications)
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Notification scheduler started")
    
    def stop_scheduler(self):
        """Stop the notification scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Notification scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Continue running even if there's an error
    
    def _run_notification_scan(self):
        """Run the notification scan job"""
        logger.info("Starting scheduled notification scan")
        try:
            notifications_sent = NotificationService.scan_and_dispatch_reminders()
            logger.info(f"Scheduled notification scan completed. {notifications_sent} notifications sent.")
        except Exception as e:
            logger.error(f"Error during scheduled notification scan: {str(e)}")
    
    def _cleanup_old_notifications(self):
        """Clean up old notifications"""
        logger.info("Starting scheduled notification cleanup")
        try:
            cleaned_count = NotificationService.cleanup_old_notifications(days_old=30)
            logger.info(f"Notification cleanup completed. {cleaned_count} old notifications removed.")
        except Exception as e:
            logger.error(f"Error during notification cleanup: {str(e)}")

# Global scheduler instance
notification_scheduler = NotificationScheduler()

def start_notification_scheduler():
    """Start the global notification scheduler"""
    notification_scheduler.start_scheduler()

def stop_notification_scheduler():
    """Stop the global notification scheduler"""
    notification_scheduler.stop_scheduler()

def run_manual_scan():
    """Manually trigger a notification scan (for testing)"""
    logger.info("Running manual notification scan")
    return NotificationService.scan_and_dispatch_reminders()