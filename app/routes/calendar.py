from flask import Blueprint, render_template
from flask_login import login_required

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/')
@login_required
def view():
    """Display full calendar view (placeholder)."""
    return render_template('calendar/view.html')
