from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Many-to-many association table for User-Company relationship
user_company = db.Table('user_company',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('company_id', db.Integer, db.ForeignKey('companies.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    """User model for multi-tenant payroll management with company access control"""
    
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # User information
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    cell_number = db.Column(db.String(20), nullable=True)
    
    # Role and permissions
    is_accountant = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_global_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_power_user = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Session management
    last_login = db.Column(db.DateTime, nullable=True)
    current_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def set_password(self, password):
        """Set password hash"""
        # Use SHA256 with salt for compatibility with Python 3.9
        import hashlib
        import os
        salt = os.urandom(16).hex()
        salted_password = salt + password
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        self.password_hash = f'{salt}${password_hash}'
    
    def check_password(self, password):
        """Check password against hash"""
        # Handle both old Werkzeug hashes and new SHA256 hashes
        if '$' in self.password_hash:
            # New SHA256 hash format
            try:
                salt, stored_hash = self.password_hash.split('$', 1)
                salted_password = salt + password
                password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
                return password_hash == stored_hash
            except:
                return False
        else:
            # Old Werkzeug hash format
            try:
                return check_password_hash(self.password_hash, password)
            except:
                return False
    
    def has_company_access(self, company_id):
        """Check if user has access to a specific company"""
        return any(company.id == company_id for company in self.companies)
    
    def get_accessible_companies(self):
        """Get list of companies the user can access"""
        return self.companies
    
    def get_id(self):
        """Return user ID as string for Flask-Login"""
        return str(self.id)
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'cell_number': self.cell_number,
            'full_name': self.full_name,
            'is_accountant': self.is_accountant,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'current_company_id': self.current_company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # Relationships
    companies = db.relationship('Company', secondary=user_company, backref='users', lazy='dynamic')
    current_company = db.relationship('Company', foreign_keys=[current_company_id], backref='current_users')
