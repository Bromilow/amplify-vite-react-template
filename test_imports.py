#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

try:
    print("Testing Flask import...")
    from flask import Flask
    print("✅ Flask imported successfully")
except Exception as e:
    print(f"❌ Flask import failed: {e}")

try:
    print("Testing app import...")
    from app import create_app
    print("✅ App import successful")
except Exception as e:
    print(f"❌ App import failed: {e}")

try:
    print("Testing app creation...")
    app = create_app()
    print("✅ App created successfully")
except Exception as e:
    print(f"❌ App creation failed: {e}")

try:
    print("Testing database...")
    from app import db
    print("✅ Database import successful")
except Exception as e:
    print(f"❌ Database import failed: {e}")

print("Import test completed!")
