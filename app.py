#!/usr/bin/env python3
"""
Simple Flask app entry point for AWS Amplify
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
app = create_app()

# For local development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
