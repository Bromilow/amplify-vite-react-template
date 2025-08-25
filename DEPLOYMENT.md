# Deployment Guide for PayrollPro Flask Application

## Current Issue

The error "This page can't be found" at `main.dzx2fam15gdb8.amplifyapp.com` occurs because **AWS Amplify is designed for static websites and single-page applications (SPAs)**, not for server-side applications like Flask.

## Why Amplify Doesn't Work for Flask Apps

AWS Amplify provides:
- Static file hosting
- CDN distribution
- Build automation for frontend frameworks

Flask applications require:
- Server-side processing
- Database connections
- Session management
- Dynamic routing

## Recommended Deployment Options

### 1. AWS Elastic Beanstalk (Recommended)
**Best for:** Production Flask applications with full server capabilities

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.9 payrollpro

# Create environment
eb create payrollpro-prod

# Deploy
eb deploy
```

### 2. AWS App Runner
**Best for:** Containerized applications with automatic scaling

```bash
# Create Dockerfile
echo 'FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "wsgi.py"]' > Dockerfile

# Deploy via AWS Console or CLI
```

### 3. Heroku
**Best for:** Quick deployment and development

```bash
# Install Heroku CLI
# Create Procfile
echo 'web: python wsgi.py' > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
heroku create payrollpro-app
git push heroku main
```

### 4. DigitalOcean App Platform
**Best for:** Simple containerized deployments

```bash
# Create app.yaml
echo 'name: payrollpro
services:
- name: web
  source_dir: /
  github:
    repo: your-repo
    branch: main
  run_command: python wsgi.py
  environment_slug: python' > app.yaml
```

## Quick Fix for Current Amplify Setup

The updated `amplify.yml` will now show an informational page explaining that this is a Flask application and suggesting proper deployment options.

## Database Considerations

For production deployment, consider:
- **AWS RDS** for PostgreSQL/MySQL
- **AWS DynamoDB** for NoSQL
- **Heroku Postgres** for Heroku deployments
- **DigitalOcean Managed Databases**

## Environment Variables

Set these in your deployment platform:
```bash
FLASK_ENV=production
DATABASE_URL=your_database_url
SESSION_SECRET=your_secret_key
REDIS_URL=your_redis_url  # Optional
```

## Next Steps

1. **Choose a deployment platform** from the options above
2. **Set up a production database**
3. **Configure environment variables**
4. **Deploy your application**
5. **Set up custom domain** (optional)

## Support

For specific deployment platform questions, refer to:
- [AWS Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)
- [DigitalOcean App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
