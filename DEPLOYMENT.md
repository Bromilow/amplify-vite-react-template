# PayrollPro Deployment Guide - AWS Amplify

## Overview
This guide will help you deploy the PayrollPro Flask application to AWS Amplify.

## Prerequisites
- AWS Account
- Git repository with your code
- AWS Amplify Console access

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository contains these files:
- `amplify.yml` - Build specification
- `requirements.txt` - Python dependencies
- `wsgi.py` - WSGI entry point
- `Procfile` - Process definition
- `config.py` - Application configuration

### 2. Connect to AWS Amplify

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click "New app" → "Host web app"
3. Choose your Git provider (GitHub, GitLab, Bitbucket, etc.)
4. Connect your repository
5. Select the branch you want to deploy (usually `main` or `master`)

### 3. Configure Build Settings

Amplify will automatically detect the `amplify.yml` file. The build process will:
- Install Python dependencies from `requirements.txt`
- Initialize the Flask application
- Deploy using Gunicorn WSGI server

### 4. Environment Variables

Set these environment variables in Amplify Console:

#### Required Variables:
```
FLASK_ENV=production
SESSION_SECRET=your-super-secret-key-here
```

#### Optional Variables:
```
DATABASE_URL=your-database-url (if using external database)
REDIS_URL=your-redis-url (if using Redis for caching)
```

### 5. Database Configuration

#### Option A: SQLite (Default)
- No additional setup required
- Database file will be created automatically
- **Note**: Data will be lost on each deployment

#### Option B: PostgreSQL (Recommended for Production)
1. Create an RDS PostgreSQL instance
2. Set `DATABASE_URL` environment variable:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

### 6. Custom Domain (Optional)

1. In Amplify Console, go to "Domain management"
2. Add your custom domain
3. Configure DNS settings as instructed

### 7. SSL Certificate

Amplify automatically provides SSL certificates for your domain.

## Post-Deployment

### 1. Initial Setup
After deployment, visit your app URL and:
1. Register a new account
2. Create your first company
3. Start using the payroll system

### 2. Database Migration
If using PostgreSQL, you may need to run database migrations:
```bash
# Connect to your Amplify build environment
# Run migrations if needed
```

### 3. Monitoring
- Use AWS CloudWatch for logs
- Monitor application performance
- Set up alerts for errors

## Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check build logs in Amplify Console
   - Verify all dependencies are in `requirements.txt`
   - Ensure Python version compatibility

2. **Database Connection Issues**
   - Verify `DATABASE_URL` environment variable
   - Check database security groups
   - Ensure database is accessible from Amplify

3. **Static Files Not Loading**
   - Check file paths in templates
   - Verify static folder structure

4. **WeasyPrint Issues**
   - WeasyPrint requires system libraries
   - Consider using alternative PDF generation for production

### Build Logs
Check build logs in Amplify Console for detailed error information.

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to Git
   - Use Amplify environment variables for sensitive data

2. **Database Security**
   - Use strong passwords
   - Restrict database access
   - Enable SSL connections

3. **Application Security**
   - Keep dependencies updated
   - Use HTTPS in production
   - Implement proper session management

## Performance Optimization

1. **Database**
   - Use connection pooling
   - Optimize queries
   - Consider read replicas for heavy loads

2. **Caching**
   - Enable Redis caching
   - Use CDN for static assets
   - Implement application-level caching

3. **Monitoring**
   - Set up performance monitoring
   - Monitor database performance
   - Track user experience metrics

## Support

For issues specific to:
- **AWS Amplify**: Check AWS documentation
- **Flask Application**: Check application logs
- **Database**: Check RDS console and logs

## Next Steps

After successful deployment:
1. Set up monitoring and alerts
2. Configure backup strategies
3. Plan for scaling
4. Implement CI/CD pipeline
5. Set up staging environment
