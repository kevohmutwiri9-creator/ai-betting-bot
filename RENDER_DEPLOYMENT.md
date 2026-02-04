# Render Deployment Guide for AI Betting Bot

## 🚀 Quick Setup

### 1. Push to GitHub (if not already done)
```bash
git add render.yaml
git commit -m "Add Render configuration"
git push origin main
```

### 2. Deploy on Render
1. Go to https://render.com/
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select your `ai-betting-bot` repo
5. Render will auto-detect from `render.yaml`

### 3. Set Environment Variables
In Render dashboard → your service → Environment:
```
TELEGRAM_BOT_TOKEN=8537708272:AAH-VGrOjlXhNohNwUWyyu3D2tDT8oVPXNg
TELEGRAM_BOT_USERNAME=aibettingbotbot
API_SECRET_KEY=your-secret-api-key-here
SESSION_SECRET_KEY=your-session-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FOOTBALL_DATA_API_KEY=d5e39e9b6eb742008c27d088be54a668
API_FOOTBALL_KEY=3960b893a559e8500663061fd7730e71
DEBUG_MODE=False
ENVIRONMENT=production
```

## 📊 What You Get

### Free Tier Features:
- ✅ 750 hours/month runtime
- ✅ Custom SSL certificate
- ✅ Auto-deploys from Git
- ✅ Built-in monitoring
- ✅ 512MB RAM
- ✅ Shared CPU

### Your App URLs:
- **Web Dashboard**: `https://ai-betting-bot.onrender.com`
- **API Endpoints**: `https://ai-betting-bot.onrender.com/api/*`

## 🤖 Telegram Bot on Render

For the Telegram bot, you have two options:

### Option 1: Background Worker (Recommended)
Create a separate service:
```yaml
# Add to render.yaml
  - type: worker
    name: telegram-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py --telegram $TELEGRAM_BOT_TOKEN $TELEGRAM_BOT_USERNAME
```

### Option 2: Use Webhooks
Modify your bot to use webhooks instead of polling (more efficient).

## 🔧 Troubleshooting

### Build Fails:
- Check `requirements.txt` has all dependencies
- Verify Python version compatibility
- Check Render build logs

### App Won't Start:
- Check start command: `gunicorn web_dashboard:app`
- Verify all environment variables are set
- Check Render service logs

### Telegram Bot Issues:
- Ensure bot token is correct
- Check bot is running on worker service
- Verify webhook URL (if using webhooks)

## 📈 Monitoring

Render provides:
- **Build logs**: See deployment issues
- **Service logs**: Runtime errors
- **Metrics**: CPU, memory usage
- **Health checks**: Service status

## 🎯 Next Steps

1. Deploy web dashboard
2. Test API endpoints
3. Set up Telegram bot worker
4. Configure custom domain (optional)
5. Set up monitoring alerts

Your AI Betting Bot will be live at: `https://ai-betting-bot.onrender.com` 🚀
