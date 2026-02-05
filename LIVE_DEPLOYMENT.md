# 🚀 AI Betting Bot - Live Deployment Guide

## Quick Start (5 Minutes)

### 1. Get FREE API Keys

#### Football Data APIs (FREE Tiers Available)

**API-Football** (https://www.api-football.com/)
- Sign up for FREE trial (100 requests/day)
- Get your API key from dashboard
- Covers: Premier League, La Liga, Serie A, Bundesliga, etc.

**Football-Data.org** (https://www.football-data.org/)
- FREE tier: 10 requests/minute
- Register and get API key immediately
- Covers: 30+ leagues worldwide

**RapidAPI Football Data** (https://rapidapi.com/)
- Search for "football" APIs
- Many have free tiers (e.g., API-Football, Football-Data)
- Subscribe to free tier for key

### 2. Configure Telegram Bot

**Create Bot:**
1. Open Telegram, search for @BotFather
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the HTTP API token

**Get Bot Username:**
- The username is what comes after `@` in your bot link
- Example: `@aibettingbotbot` → username: `aibettingbotbot`

### 3. Deploy to Render (FREE)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for live deployment"
   git push origin main
   ```

2. **Connect to Render:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `render.yaml` file

3. **Add Environment Variables:**
   In Render dashboard, go to Environment section and add:

   | Key | Value |
   |-----|--------|
   | TELEGRAM_BOT_TOKEN | Your bot token from BotFather |
   | TELEGRAM_BOT_USERNAME | Your bot username |
   | API_FOOTBALL_KEY | Your api-football.com key |
   | FOOTBALL_DATA_API_KEY | Your football-data.org key |
   | DEBUG_MODE | false |

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for build to complete (~3-5 minutes)
   - Your bot will be live at: https://your-service.onrender.com

### 4. Set Up Telegram Webhook (For Production)

**For Web Dashboard:**
```bash
curl -F "url=https://YOUR-RENDER-URL/webhook" \
     -F "secret_token=YOUR_SECRET" \
     https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook
```

### 5. Test Your Live Bot

1. Open Telegram and search for your bot
2. Send `/start` - should reply with welcome message
3. Send `/matches live` - should show live games
4. Send `/value` - should show value bets

---

## 📋 Complete Environment Variables Reference

### Required for Basic Operation
| Variable | Description | Get From |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | @BotFather |
| `TELEGRAM_BOT_USERNAME` | Bot username | @BotFather |
| `API_FOOTBALL_KEY` | Football data API key | api-football.com |
| `FOOTBALL_DATA_API_KEY` | Backup football data | football-data.org |

### Optional for Advanced Features
| Variable | Description | Get From |
|----------|-------------|----------|
| `BETFAIR_API_KEY` | Betfair Exchange API | developers.betfair.com |
| `PINNACLE_API_KEY` | Pinnacle Sports API | pinnacle.com |
| `BET365_API_KEY` | Bet365 API | bet365.com/developers |
| `DRAFTKINGS_API_KEY` | DraftKings API | draftkings.com |

### Kelly Criterion Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `KELLY_FRACTION` | 0.5 | Use half Kelly (recommended) |
| `MAX_STAKE_PERCENT` | 0.1 | Max 10% bankroll per bet |
| `MIN_STAKE` | 1.0 | Minimum stake amount |

### Auto-Betting Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_BET_ENABLED` | false | Enable auto-betting |
| `MIN_VALUE_THRESHOLD` | 0.05 | Minimum value to bet |
| `CONFIDENCE_THRESHOLD` | 0.6 | Min AI confidence |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Render Deployment                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌───────────────────────────┐  │
│  │  Web Dashboard       │    │   Telegram Bot Worker     │  │
│  │  (Flask + Gunicorn)  │    │   (python-telegram-bot)   │  │
│  └──────────┬──────────┘    └─────────────┬─────────────┘  │
│             │                             │                │
│             ▼                             ▼                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              AI Betting Engine                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐   │  │
│  │  │  AI      │ │ Value   │ │ Kelly   │ │ Odds     │   │  │
│  │  │ Model    │→│ Detector │→│ Calculator│→│ Comparator│   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
│             │                             │                │
│             ▼                             ▼                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              External APIs                            │  │
│  │  API-Football │ Football-Data.org │ Telegram API    │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Bot Not Responding
1. Check Render logs for errors
2. Verify TELEGRAM_BOT_TOKEN is correct
3. Ensure webhook is set (for production)

### No Matches Showing
1. Check API keys are valid
2. Verify API-Football/ Football-Data have quota remaining
3. Check logs for rate limiting errors

### Network Errors
- Local DNS issues → Deploy to Render (cloud DNS)
- API rate limits → Wait or upgrade API plan
- Timeout errors → Increase timeout settings

---

## 📊 Supported Leagues

| League | API Coverage | Status |
|--------|--------------|--------|
| Premier League | ✅ Full | Live |
| La Liga | ✅ Full | Live |
| Serie A | ✅ Full | Live |
| Bundesliga | ✅ Full | Live |
| Ligue 1 | ✅ Full | Live |
| Eredivisie | ✅ Full | Live |
| Primeira Liga | ✅ Full | Live |
| Champions League | ✅ Full | Live |
| Europa League | ✅ Full | Live |
| MLS | ✅ Full | Live |
| Kenya Premier League | ⚠️ Limited | Demo |
| AFCON | ✅ Full | Live |

---

## 🚦 Production Checklist

- [ ] Telegram bot created and tested
- [ ] API keys obtained and tested
- [ ] Render deployment successful
- [ ] Webhook configured (for production)
- [ ] Kelly criterion settings configured
- [ ] Notifications enabled
- [ ] Logs monitored for errors

---

## 📞 Support

- **Telegram Bot:** @your_bot_username
- **Dashboard:** https://your-service.onrender.com
- **GitHub:** https://github.com/kevohmutwiri9-creator/ai-betting-bot

---

## ⚠️ Disclaimer

This bot is for educational purposes only. Always gamble responsibly and never bet more than you can afford to lose.
