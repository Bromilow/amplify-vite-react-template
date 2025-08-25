import click
from flask import current_app
from flask.cli import with_appcontext
from app.services.notification_service import NotificationService
from app.tasks.notification_scheduler import run_manual_scan

@click.command()
@with_appcontext
def scan_reminders():
    """Manually scan and dispatch compliance reminder notifications"""
    click.echo('Starting compliance reminder scan...')
    
    try:
        notifications_sent = NotificationService.scan_and_dispatch_reminders()
        click.echo(f'Scan completed successfully. {notifications_sent} notifications sent.')
    except Exception as e:
        click.echo(f'Error during scan: {str(e)}', err=True)

@click.command()
@click.option('--days', default=30, help='Number of days old to clean up')
@with_appcontext
def cleanup_notifications(days):
    """Clean up old notifications"""
    click.echo(f'Cleaning up notifications older than {days} days...')
    
    try:
        cleaned_count = NotificationService.cleanup_old_notifications(days_old=days)
        click.echo(f'Cleanup completed. {cleaned_count} notifications removed.')
    except Exception as e:
        click.echo(f'Error during cleanup: {str(e)}', err=True)

def register_commands(app):
    """Register CLI commands with the Flask app"""
    app.cli.add_command(scan_reminders)
    app.cli.add_command(cleanup_notifications)