import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

# Initialize extensions with session options to avoid expiration on commit
db = SQLAlchemy(model_class=Base, session_options={"expire_on_commit": False})
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    from app.context_processors import register_context_processors
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Set secret key
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Configure proxy fix for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)

    # Configure caching
    app.config.setdefault('CACHE_DEFAULT_TIMEOUT', 900)
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        app.config.setdefault('CACHE_TYPE', 'RedisCache')
        app.config.setdefault('CACHE_REDIS_URL', redis_url)
    else:
        app.config.setdefault('CACHE_TYPE', 'SimpleCache')

    try:
        cache.init_app(app)
    except Exception as e:
        app.logger.warning('Cache initialization failed: %s; using SimpleCache', e)
        app.config.update({'CACHE_TYPE': 'SimpleCache'})
        cache.init_app(app)
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize CSRF protection
    csrf.init_app(app)

    # Register global context processors
    register_context_processors(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        app.logger.debug("Loading user with ID: %s", user_id)
        user = User.query.get(int(user_id))
        app.logger.debug("User loaded: %s", user is not None)
        return user
    
    @app.before_request
    def make_session_permanent():
        from flask import session
        session.permanent = True
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.employees import employees_bp
    from app.routes.payroll import payroll_bp
    from app.routes.accountant_dashboard import accountant_dashboard_bp
    from app.routes.calendar import calendar_bp
    from app.routes.company import bp as company_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    from app.routes.admin_compliance import admin_compliance_bp
    from app.routes.reminders import reminders_bp
    from app.routes.notifications import notifications_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(accountant_dashboard_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_compliance_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(notifications_bp)
    
    # Create database tables
    with app.app_context():
        # Import models to ensure they're registered
        from app.models import employee as _employee  # imported for side effects
        assert _employee
        db.create_all()
        
        # Initialize sample data only for existing demo companies
        from app.services.employee_service import EmployeeService as _EmployeeService
        assert _EmployeeService
        # Sample data initialization is disabled for multi-tenant mode
        # to prevent demo employees appearing in new user companies
        # EmployeeService.initialize_sample_data()
    
    # Root route redirect with authentication
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('auth.login'))
    
    return app
