#!/usr/bin/env python3
"""
WSGI entry point for PayrollPro Flask application
This file is used by AWS Amplify and other WSGI servers
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DATABASE_URL', os.environ.get('DATABASE_URL', 'sqlite:///employees.db'))

# Import and create the Flask app
from app import create_app

# Create the application instance
application = create_app()

# For local development
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)
