# Pre-Deployment Checklist

## ✅ Backend Checklist

- [ ] Update requirements.txt with all dependencies
- [ ] Set DEBUG=False in production config
- [ ] Configure CORS for production domains
- [ ] Add database migration scripts
- [ ] Test API endpoints locally
- [ ] Update SECRET_KEY for production
- [ ] Configure environment variables

## ✅ Frontend Checklist

- [ ] Update API base URL for production
- [ ] Build and test locally
- [ ] Configure production preview command
- [ ] Update CORS settings to match backend

## ✅ Database Checklist

- [ ] Export sample data if needed
- [ ] Create database initialization scripts
- [ ] Test database connection
- [ ] Verify all tables and views exist

## ✅ Security Checklist

- [ ] Use strong SECRET_KEY
- [ ] Configure proper CORS origins
- [ ] Set appropriate token expiration
- [ ] Remove debug information
- [ ] Validate all environment variables

## ✅ Deployment Steps

1. Create PostgreSQL database on Render
2. Deploy backend service with environment variables
3. Deploy frontend service with API URL
4. Test complete application flow
5. Monitor logs for any issues
