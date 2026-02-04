# AI Betting Bot - Production Deployment Guide

## 🚀 Quick Deployment

### Prerequisites
- Docker & Docker Compose
- Git
- At least 2GB RAM
- 10GB disk space

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd ai-betting-bot
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Deploy
```bash
chmod +x deploy.sh
./deploy.sh deploy
```

## 📋 Environment Configuration

### Required Environment Variables
```bash
# Security
TELEGRAM_BOT_TOKEN=your_actual_token
API_SECRET_KEY=your_secret_key_here
SESSION_SECRET_KEY=your_session_secret_here
JWT_SECRET_KEY=your_jwt_secret_here

# Database (for production)
DATABASE_URL=postgresql://betting_user:password@postgres:5432/betting_bot
REDIS_URL=redis://redis:6379/0

# Email (optional)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Payment (optional)
STRIPE_PUBLIC_KEY=pk_live_your_key
STRIPE_SECRET_KEY=sk_live_your_key
```

## 🏗️ Architecture

### Services Overview
- **betting-bot**: Main Flask application
- **postgres**: Production database
- **redis**: Caching and sessions
- **nginx**: Reverse proxy with SSL

### Data Flow
```
User → Nginx → Flask App → PostgreSQL/Redis
```

## 🔧 Configuration Files

### Docker Compose
- **Web Service**: Main application on port 5000
- **Database**: PostgreSQL with persistent storage
- **Cache**: Redis for performance
- **Proxy**: Nginx with SSL termination

### Nginx Configuration
- SSL/TLS encryption
- Rate limiting
- Static file serving
- API proxying

## 📊 Monitoring

### Logs Location
- Application logs: `./logs/`
- Nginx logs: Docker container logs
- Database logs: PostgreSQL container logs

### Health Checks
```bash
# Application health
curl https://localhost/health

# Service status
docker-compose ps
```

## 🔒 Security Considerations

### Production Security
1. **Change all default passwords**
2. **Use production SSL certificates**
3. **Enable firewall rules**
4. **Regular security updates**
5. **Monitor logs for suspicious activity**

### SSL Certificates
```bash
# For production, use Let's Encrypt
certbot --nginx -d your-domain.com

# Or upload your own certificates to ./ssl/
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# In docker-compose.yml
services:
  betting-bot:
    deploy:
      replicas: 3
```

### Database Optimization
- Add read replicas
- Implement connection pooling
- Use PostgreSQL-specific features

## 🔍 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose logs betting-bot

# Check environment
docker-compose exec betting-bot env
```

#### Database Connection Issues
```bash
# Test database connection
docker-compose exec postgres psql -U betting_user -d betting_bot

# Restart database
docker-compose restart postgres
```

#### High Memory Usage
```bash
# Monitor resources
docker stats

# Clean up unused containers
docker system prune
```

### Performance Optimization

#### Database Indexes
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_matches_date ON matches(date);
CREATE INDEX CONCURRENTLY idx_user_created_at ON users(created_at);
```

#### Caching Strategy
- Redis for API responses
- Application-level caching
- CDN for static assets

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull

# Rebuild and restart
./deploy.sh update
```

### Database Backups
```bash
# Manual backup
docker-compose exec postgres pg_dump -U betting_user betting_bot > backup.sql

# Automated backup (add to cron)
0 2 * * * /path/to/backup-script.sh
```

### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/ai-betting-bot
```

## 📱 Mobile Deployment

### Telegram Bot Deployment
```bash
# Deploy only the Telegram bot
docker-compose --profile telegram up -d telegram-bot
```

### API-Only Deployment
```bash
# Deploy without web interface
docker-compose up -d postgres redis betting-bot
```

## 🌐 Domain Configuration

### DNS Settings
```
A record: your-domain.com → YOUR_SERVER_IP
AAAA record: your-domain.com → YOUR_IPV6_ADDRESS (optional)
```

### SSL Configuration
```bash
# Generate CSR for production SSL
openssl req -new -newkey rsa:2048 -nodes -keyout private.key -out server.csr
```

## 📞 Support

### Monitoring Commands
```bash
# Real-time logs
docker-compose logs -f

# Resource usage
docker stats

# Service health
docker-compose exec betting-bot curl localhost:5000/health
```

### Emergency Procedures
```bash
# Quick stop all services
./deploy.sh stop

# Full reset (destructive)
./deploy.sh clean

# Restart with clean state
docker-compose down -v
docker-compose up -d
```

## 🎯 Production Checklist

### Before Going Live
- [ ] All environment variables set
- [ ] SSL certificates configured
- [ ] Database backups enabled
- [ ] Monitoring configured
- [ ] Rate limits tested
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Error handling verified
- [ ] Logging confirmed working
- [ ] Backup procedures tested

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify user registration
- [ ] Test payment processing
- [ ] Confirm email delivery
- [ ] Validate API responses

---

**🎉 Your AI Betting Bot is now production-ready!**
