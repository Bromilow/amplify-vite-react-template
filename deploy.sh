#!/bin/bash

# PayrollPro Deployment Script for AWS Amplify
# This script prepares the application for deployment

echo "🚀 Preparing PayrollPro for AWS Amplify deployment..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the project root."
    exit 1
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "📦 Creating requirements.txt..."
    python3 -m pip freeze > requirements.txt
fi

# Check if all required files exist
echo "🔍 Checking required deployment files..."

required_files=("amplify.yml" "requirements.txt" "wsgi.py" "Procfile" "config.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files: ${missing_files[*]}"
    echo "Please ensure all deployment files are present."
    exit 1
fi

echo "✅ All required files found!"

# Test the application locally
echo "🧪 Testing application initialization..."
if python3 -c "from app import create_app; app = create_app(); print('✅ App initialized successfully')"; then
    echo "✅ Application test passed!"
else
    echo "❌ Application test failed!"
    exit 1
fi

# Check for common issues
echo "🔍 Checking for common deployment issues..."

# Check if database file exists and is writable
if [ -f "instance/employees.db" ]; then
    echo "⚠️  Warning: Local database file found. This will be recreated in production."
fi

# Check for environment variables
if [ -z "$FLASK_ENV" ]; then
    echo "ℹ️  Note: FLASK_ENV not set. Will use default configuration."
fi

if [ -z "$SESSION_SECRET" ]; then
    echo "⚠️  Warning: SESSION_SECRET not set. Please set this in Amplify environment variables."
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Commit all changes to your Git repository"
echo "2. Push to your main branch"
echo "3. Connect your repository to AWS Amplify"
echo "4. Set environment variables in Amplify Console:"
echo "   - FLASK_ENV=production"
echo "   - SESSION_SECRET=your-secret-key"
echo "5. Deploy!"
echo ""
echo "📖 For detailed instructions, see DEPLOYMENT.md"
