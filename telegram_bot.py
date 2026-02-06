"""Telegram Bot for AI Betting Predictions"""

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
import pandas as pd
from datetime import datetime
import json
from value_detector import ValueBetDetector
from data_collector import FootballDataCollector
from live_tracker import LiveMatchTracker
from telegram_gambling import (
    get_casino_games,
    get_virtual_sports,
    get_jackpot_bets,
    get_betika_matches,
    get_sportpesa_matches,
    get_odibet_matches,
)
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME
from logger import logger

class BettingTelegramBot:
    def __init__(self, token, bot_username):
        self.token = token
        self.bot_username = bot_username
        self.value_detector = ValueBetDetector()
        self.data_collector = FootballDataCollector()
        self.live_tracker = LiveMatchTracker()
        self.premium_users = set()
        self.subscribed_users = set()
        self.live_subscribed_users = set()  # Users subscribed to live match alerts
        self.notification_jobs = {}
        
        # Notification settings
        self.notification_interval = 3600  # Check for value bets every hour
        self.min_value_threshold = 0.05   # Minimum value margin for notifications

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command - enable value bet notifications"""
        user_id = update.effective_user.id
        self.subscribed_users.add(user_id)
        
        await update.message.reply_text(
            "✅ *Notifications Enabled!*\n\n"
            "You'll receive notifications when new value bets are found.\n"
            "Use /unsubscribe to stop notifications.",
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user_id} subscribed to notifications")
    
    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unsubscribe command - disable value bet notifications"""
        user_id = update.effective_user.id
        self.subscribed_users.discard(user_id)
        
        await update.message.reply_text(
            "❌ *Notifications Disabled*\n\n"
            "You've been unsubscribed from value bet alerts.",
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user_id} unsubscribed from notifications")
    
    # ==================== GAMBLING/CASINO COMMANDS ====================
    
    async def get_casino_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /casino and /slots commands"""
        await get_casino_games(update, context)
    
    async def get_virtual_sports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /virtual command"""
        await get_virtual_sports(update, context)
    
    async def get_jackpot_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /jackpot command"""
        await get_jackpot_bets(update, context)
    
    async def get_betika_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /betika command"""
        await get_betika_matches(update, context)
    
    async def get_sportpesa_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sportpesa command"""
        await get_sportpesa_matches(update, context)
    
    async def get_odibet_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /odibet command"""
        await get_odibet_matches(update, context)
    
    async def get_inplay_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /inplay command - show in-play betting opportunities"""
        try:
            message = self.live_tracker.format_inplay_message()
            
            keyboard = [
                [InlineKeyboardButton("Refresh", callback_data="refresh_inplay")],
                [InlineKeyboardButton("Live Matches", callback_data="live_matches")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error fetching in-play bets: {e}")
            await update.message.reply_text("Error fetching in-play betting opportunities.")
    
    async def subscribe_live_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /livenotify command - subscribe to live match alerts"""
        user_id = update.effective_user.id
        self.live_subscribed_users.add(user_id)
        
        message = """
✅ **Live Match Alerts Enabled!**

You will receive notifications when:
- Goals are scored
- Red cards shown
- Key betting opportunities arise
- Match momentum shifts

Use /unlivenotify to disable alerts.

Tips:
- Alerts come with betting recommendations
- Act fast - odds change quickly
- Bet responsibly
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"User {user_id} subscribed to live alerts")
    
    async def unsubscribe_live_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unlivenotify command - unsubscribe from live match alerts"""
        user_id = update.effective_user.id
        self.live_subscribed_users.discard(user_id)
        
        await update.message.reply_text(
            "❌ **Live Alerts Disabled**\n\n"
            "You have been unsubscribed from live match notifications.",
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user_id} unsubscribed from live alerts")
    
    # ==================== PREMIUM COMMANDS ====================
    
    async def premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium command - show premium features"""
        user_id = update.effective_user.id
        is_premium = user_id in self.premium_users
        
        if is_premium:
            status = "✅ **PREMIUM ACTIVE**"
            features = """
🎯 **Premium Features:**
• Instant Value Bet Notifications
• Higher Confidence Predictions
• Advanced Stats & Analytics
• Personal Betting Strategy
• Priority Support
            """
        else:
            status = "🌟 **Upgrade to Premium**"
            features = """
🎁 **Free Features:**
• Basic Predictions
• Match Analysis
• Value Bet Finder
• Daily Tips

🎯 **Premium Includes:**
• Instant Notifications
• 85%+ Confidence Picks
• Custom Strategy
• VIP Support
            """
        
        premium_message = f"""
{status}

{features}

📧 **Contact Admin:**
• Email: kevohmutwiri35@gmail.com
• Telegram: @Klaus_debbugg

💳 **Payment Methods:**
• M-PESA: 0748392884
• PayPal: kevohmutwiri35@gmail.com
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 Contact Admin", url="https://t.me/Klaus_debbugg")],
            [InlineKeyboardButton("💳 Upgrade", callback_data="upgrade")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            premium_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    def format_value_bets_message(self, value_bets):
        """Format value bets for display"""
        message = "🎯 *VALUE BETS FOUND*\n\n"
        
        for i, bet in enumerate(value_bets[:10], 1):
            message += f"📊 *Bet #{i}*\n"
            message += f"🏆 {bet['home_team']} vs {bet['away_team']}\n"
            message += f"💎 Recommendation: *{bet['recommended_outcome']}*\n"
            message += f"📈 Odds: {bet['odds']:.2f}\n"
            message += f"🎯 Value: +{bet['value_margin']:.1f}%\n"
            message += f"🎲 Expected Value: {bet['expected_value']:.2f}\n"
            
            if 'stake' in bet:
                message += f"💰 Suggested Stake: KES {bet['stake']:.2f}\n"
            
            if 'confidence' in bet:
                message += f"📊 Confidence: {bet['confidence']}\n"
            
            message += "\n"
        
        message += "📧 **Contact Admin**\n"
        message += "kevohmutwiri35@gmail.com | @Klaus_debbugg\n\n"
        
        message += "—\n"
        message += "🤖 *AI Betting Bot* | Bet responsibly!\n"
        
        return message
    
    async def broadcast_value_bets(self, context: ContextTypes.DEFAULT_TYPE):
        """Send value bet notifications to subscribed users"""
        try:
            # Get current matches
            matches_data = self.data_collector.get_sample_data()
            
            # Find value bets
            value_bets = self.value_detector.find_value_bets(matches_data)
            
            # Filter by minimum value threshold
            filtered_bets = [
                bet for bet in value_bets 
                if bet.get('value_margin', 0) >= (self.min_value_threshold * 100)
            ]
            
            if not filtered_bets:
                logger.info("No value bets found above threshold")
                return
            
            # Format message
            message = self.format_value_bets_message(filtered_bets)
            
            # Send to all subscribed users
            for user_id in self.subscribed_users:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent value bet notification to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in broadcast_value_bets: {e}")
    
    async def value_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /valuebets command - show current value bets"""
        try:
            await update.message.reply_text("🔍 *Searching for value bets...*", parse_mode='Markdown')
            
            # Get current matches from data collector
            matches_data = self.data_collector.get_sample_data()
            
            # Find value bets
            value_bets = self.value_detector.find_value_bets(matches_data)
            
            if value_bets:
                message = self.format_value_bets_message(value_bets)
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_bets")],
                    [InlineKeyboardButton("📊 Analyze", callback_data="analyze")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    message, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ *No value bets found at the moment.*\n\n"
                    "Check back later for new opportunities!",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error fetching value bets: {e}")
            await update.message.reply_text("❌ Error fetching value bets. Please try again later!")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "refresh_bets":
            await self.value_bets(update, context)
        elif query.data == "analyze":
            await query.edit_message_text("🔍 *Analysis Mode*\n\nUse /analyze <team1> vs <team2> for detailed analysis.")
        elif query.data == "upgrade":
            await self.premium(update, context)
        elif query.data.startswith("bet_"):
            await query.edit_message_text("💰 *Bet Placed!*\n\nGood luck! Remember to bet responsibly.")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and hasattr(update, 'effective_message'):
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_message = f"""
🎰 *Welcome to AI Betting Bot* 🎰

Hello {user.first_name}! I'm your AI-powered betting assistant.

🏆 *What I Do:*
• Analyze football matches
• Find value bets with positive expected value
• Provide predictions with confidence scores
• Send instant notifications

📊 *Available Commands:*
• /valuebets - Find current value bets
• /today - Today's matches
• /tomorrow - Tomorrow's matches
• /live - Currently live matches
• /premier - Premier League
• /laliga - La Liga
• /seriea - Serie A
• /bundesliga - Bundesliga
• /analyze - Detailed match analysis
• /stats - AI model statistics
• /premium - Premium features
• /subscribe - Get notifications
• /help - All commands

🎮 *Casino & Games:*
• /casino - Casino games
• /slots - Slot games
• /virtual - Virtual sports
• /jackpot - Jackpot predictions
• /betika - Betika matches
• /sportpesa - SportPesa matches
• /odibet - Odibet matches

📧 *Contact:* kevohmutwiri35@gmail.com

⚠️ *Disclaimer:* Bet responsibly. 18+ Only.
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Find Value Bets", callback_data="find_bets")],
            [InlineKeyboardButton("📊 Live Matches", callback_data="live")],
            [InlineKeyboardButton("🎰 Casino Games", callback_data="casino")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"User {user.id} started the bot")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - show all available commands"""
        help_text = """
🎰 *AI Betting Bot - Help*

📊 *Main Commands:*
• /start - Start the bot
• /help - Show this help message
• /valuebets - Find current value bets
• /today - Today's matches
• /tomorrow - Tomorrow's matches
• /live - Currently live matches
• /premier - Premier League matches
• /laliga - La Liga matches
• /seriea - Serie A matches
• /bundesliga - Bundesliga matches

🎮 *Analysis:*
• /analyze <team1> vs <team2> - Detailed match analysis
• /stats - AI model statistics

💎 *Premium:*
• /premium - View premium features
• /subscribe - Enable notifications
• /unsubscribe - Disable notifications

🎰 *Casino & Games:*
• /casino - Casino games
• /slots - Slot games
• /virtual - Virtual sports
• /jackpot - Jackpot predictions
• /betika - Betika matches
• /sportpesa - SportPesa matches
• /odibet - Odibet matches

📧 *Support:* kevohmutwiri35@gmail.com

⚠️ *Disclaimer:* Bet responsibly. 18+ Only.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - show AI model statistics"""
        stats = self.value_detector.get_statistics()
        
        stats_message = f"""
📊 *AI Model Statistics*

📈 *Performance Metrics:*
• Total Predictions: {stats['total_predictions']}
• Value Bets Found: {stats['value_bets_found']}
• Average Value: {stats['average_value']:.2f}%
• Win Rate: {stats['win_rate']:.1f}%

🎯 *Value Detection:*
• Min Value Threshold: {stats['min_value_threshold']:.1f}%
• Avg Odds: {stats['average_odds']:.2f}

🤖 *Model Status:*
• Status: Active
• Last Updated: Real-time

📧 *Contact Admin:* kevohmutwiri35@gmail.com

⚠️ *Note:* Past performance doesn't guarantee future results. Bet responsibly.
        """
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
    
    async def get_today_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /today command - show today's matches"""
        await self._send_matches_by_date(update, context, 'today')
    
    async def get_tomorrow_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tomorrow command - show tomorrow's matches"""
        await self._send_matches_by_date(update, context, 'tomorrow')
    
    async def get_live_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /live command - show live matches"""
        await self._send_matches_by_date(update, context, 'live')
    
    async def get_league_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle league-specific commands"""
        command = update.message.text.split()[0][1:]  # Get command without /
        
        league_map = {
            'premier': 'Premier League',
            'laliga': 'La Liga',
            'seriea': 'Serie A',
            'bundesliga': 'Bundesliga'
        }
        
        league = league_map.get(command, command.title())
        await self._send_matches_by_league(update, context, league)
    
    async def _send_matches_by_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, date_filter: str):
        """Helper to send matches by date"""
        chat_id = update.effective_chat.id
        
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔍 *Fetching {date_filter} matches...*",
                parse_mode='Markdown'
            )
            
            matches = self.data_collector.get_sample_data()
            
            if not matches:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ No matches found for {date_filter}."
                )
                return
            
            message = f"⚽ *{date_filter.upper()} MATCHES*\\n\\n"
            
            for i, match in enumerate(matches[:10], 1):
                home = match.get('home_team', 'TBD')
                away = match.get('away_team', 'TBD')
                odds_home = match.get('home_odds', 0)
                odds_away = match.get('away_odds', 0)
                odds_draw = match.get('draw_odds', 0)
                
                message += f"📊 *Match #{i}*\\n"
                message += f"🏆 {home} vs {away}\\n"
                message += f"💰 {odds_home:.2f} | {odds_draw:.2f} | {odds_away:.2f}\\n\\n"
            
            message += "📧 *Contact Admin:* kevohmutwiri35@gmail.com"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error fetching {date_filter} matches: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error fetching matches. Please try again later!"
            )
    
    async def _send_matches_by_league(self, update: Update, context: ContextTypes.DEFAULT_TYPE, league: str):
        """Helper to send matches by league"""
        chat_id = update.effective_chat.id
        
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔍 *Fetching {league} matches...*",
                parse_mode='Markdown'
            )
            
            matches = self.data_collector.get_sample_data()
            
            league_matches = [
                m for m in matches 
                if league.lower() in m.get('league', '').lower()
            ]
            
            if not league_matches:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ No {league} matches found at the moment."
                )
                return
            
            message = f"⚽ *{league.upper()}*\\n\\n"
            
            for i, match in enumerate(league_matches[:10], 1):
                home = match.get('home_team', 'TBD')
                away = match.get('away_team', 'TBD')
                odds_home = match.get('home_odds', 0)
                odds_away = match.get('away_odds', 0)
                odds_draw = match.get('draw_odds', 0)
                
                message += f"📊 *Match #{i}*\\n"
                message += f"🏆 {home} vs {away}\\n"
                message += f"💰 {odds_home:.2f} | {odds_draw:.2f} | {odds_away:.2f}\\n\\n"
            
            message += "📧 *Contact Admin:* kevohmutwiri35@gmail.com"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error fetching {league} matches: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error fetching league matches. Try again later!"
            )
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - provide detailed match analysis"""
        # Get match details from command arguments
        args = context.args
        
        if not args:
            help_text = """
📝 **Analyze a Match**

Usage: /analyze <home_team> vs <away_team>

Example:
/analyze Arsenal vs Chelsea
/analyze Man Utd vs Liverpool

📧 Contact: kevohmutwiri35@gmail.com
            """
            await update.message.reply_text(help_text, parse_mode='Markdown')
            return
        
        # Parse the match from arguments
        match_text = ' '.join(args)
        
        # Try to extract teams (handles "Team A vs Team B" or "Team A - Team B")
        if ' vs ' in match_text:
            parts = match_text.split(' vs ')
        elif ' - ' in match_text:
            parts = match_text.split(' - ')
        else:
            parts = match_text.split(' vs ')
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format. Use: /analyze <home_team> vs <away_team>"
            )
            return
        
        home_team = parts[0].strip()
        away_team = ' vs '.join(parts[1:]).strip()
        
        # Handle both regular messages and callback queries
        if update.callback_query:
            await update.callback_query.edit_message_text(
                f"🔍 Analyzing: {home_team} vs {away_team}..."
            )
            chat = update.callback_query.message
        else:
            await update.message.reply_text(
                f"🔍 Analyzing: {home_team} vs {away_team}..."
            )
            chat = update.message
        
        # Generate analysis
        try:
            # Get predictions from AI model
            analysis = self.value_detector.analyze_match(home_team, away_team)
            
            # Format and send the analysis
            analysis_text = f"""
📊 *MATCH ANALYSIS*

🏆 *{home_team}* vs *{away_team}*

📈 *AI Prediction:*
• Prediction: {analysis['prediction']}
• Confidence: {analysis['confidence']}
• Expected Goals: {analysis['expected_goals']}

🎯 *Odds Analysis:*
• Home Win: {analysis['home_odds']:.2f}
• Draw: {analysis['draw_odds']:.2f}
• Away Win: {analysis['away_odds']:.2f}

💎 *Value Bet:*
• Recommended: {analysis['recommended_bet']}
• Odds: {analysis['recommended_odds']:.2f}
• Value: +{analysis['value_margin']:.1f}%

📝 *Key Factors:*
{analysis['factors']}

⚠️ *Disclaimer:* This is AI-generated analysis. Bet responsibly.
            """
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    analysis_text,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    analysis_text,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error analyzing match: {e}")
            error_text = f"""
❌ *Analysis Error*

Could not analyze {home_team} vs {away_team}.

Please try again later or contact support.

📧 Contact: kevohmutwiri35@gmail.com
            """
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    error_text,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    error_text,
                    parse_mode='Markdown'
                )
    
    def run(self):
        """Run the bot"""
        try:
            application = Application.builder().token(self.token).build()
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("valuebets", self.value_bets))
            application.add_handler(CommandHandler("today", self.get_today_matches))
            application.add_handler(CommandHandler("tomorrow", self.get_tomorrow_matches))
            application.add_handler(CommandHandler("live", self.get_live_matches))
            application.add_handler(CommandHandler("premier", self.get_league_matches))
            application.add_handler(CommandHandler("laliga", self.get_league_matches))
            application.add_handler(CommandHandler("seriea", self.get_league_matches))
            application.add_handler(CommandHandler("bundesliga", self.get_league_matches))
            # Gambling/Casino commands
            application.add_handler(CommandHandler("casino", self.get_casino_games))
            application.add_handler(CommandHandler("slots", self.get_casino_games))
            application.add_handler(CommandHandler("virtual", self.get_virtual_sports))
            application.add_handler(CommandHandler("jackpot", self.get_jackpot_bets))
            application.add_handler(CommandHandler("betika", self.get_betika_matches))
            application.add_handler(CommandHandler("sportpesa", self.get_sportpesa_matches))
            application.add_handler(CommandHandler("odibet", self.get_odibet_matches))
            application.add_handler(CommandHandler("inplay", self.get_inplay_bets))
            application.add_handler(CommandHandler("livenotify", self.subscribe_live_alerts))
            application.add_handler(CommandHandler("unlivenotify", self.unsubscribe_live_alerts))
            application.add_handler(CommandHandler("analyze", self.analyze))
            application.add_handler(CommandHandler("stats", self.stats))
            application.add_handler(CommandHandler("premium", self.premium))
            application.add_handler(CommandHandler("subscribe", self.subscribe))
            application.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
            application.add_handler(CommandHandler("help", self.help))
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Add error handler
            application.add_error_handler(self.error_handler)
            
            # Setup notification job
            try:
                application.job_queue.run_repeating(
                    self.broadcast_value_bets,
                    interval=self.notification_interval,
                    first=60  # Wait 60 seconds before first check
                )
            except Exception as e:
                logger.warning(f"Could not setup job queue: {e}")
            
            # Start polling
            print("🤖 Bot is running...")
            application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")


if __name__ == "__main__":
    # Initialize and run the bot
    if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME:
        bot = BettingTelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME)
        bot.run()
    else:
        print("Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME in config.py")
