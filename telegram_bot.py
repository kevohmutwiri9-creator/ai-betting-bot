import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
import pandas as pd
from datetime import datetime
import json
from value_detector import ValueBetDetector
from data_collector import FootballDataCollector
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME
from logger import logger

class BettingTelegramBot:
    def __init__(self, token, bot_username):
        self.token = token
        self.bot_username = bot_username
        self.value_detector = ValueBetDetector()
        self.data_collector = FootballDataCollector()
        self.premium_users = set()
        self.subscribed_users = set()  # Users subscribed to value bet alerts
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
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - show all available commands"""
        help_text = """
🎯 **AI Betting Bot - Help**

📊 **Commands:**
/start - Start the bot
/valuebets - Get current value bets
/analyze - Analyze a specific match
/stats - View betting statistics
/subscribe - Get notifications for new value bets
/unsubscribe - Stop notifications
/premium - View premium features
/help - Show this help message

💡 **Tips:**
• Use inline buttons for quick actions
• Subscribe to get instant alerts
• Check stats regularly for updates

📧 **Contact Admin**
For support and manual activation:
• Telegram: @admin
• Email: kevohmutwiri35@gmail.com
• WhatsApp: 0791674888
• Username: @Klaus_debbugg

⚠️ **Disclaimer:** Bet responsibly. This is an analysis tool only.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - show betting statistics"""
        try:
            stats_message = """
📊 **Betting Statistics**

🤖 **AI Model Status:**
• Status: Active
• Accuracy: ~32.5%
• Trained on historical data

📈 **Value Detection:**
• Min threshold: 5%
• Check interval: Hourly
• Active subscribers: {subscribers}

💎 **Premium Features:**
• Full match analysis
• Advanced statistics
• Priority notifications

📧 **Contact Admin**
For support: kevohmutwiri35@gmail.com
        """.format(
                subscribers=len(self.subscribed_users)
            )
            
            await update.message.reply_text(
                stats_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await update.message.reply_text(
                "❌ Error fetching statistics. Please try again later."
            )
            logger.error(f"Error in stats: {e}")
    
    async def premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium command - show premium features"""
        premium_message = """
💎 **Premium Features**

Upgrade to premium for:
• Full match analysis with detailed predictions
• Advanced statistics and trends
• Priority notifications for value bets
• Access to historical data
• Custom betting strategies

📧 **Contact Admin**
For manual activation:
• Telegram: @Klaus_debbugg
• Email: kevohmutwiri35@gmail.com
• Username: @Klaus_debbugg

Current AI accuracy is ~32.5%. Premium users get enhanced analysis tools.
        """
        
        keyboard = [
            [InlineKeyboardButton("📧 Contact Admin", url="https://t.me/admin")]
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
                logger.info("No value bets meeting threshold found")
                return
            
            # Format message
            message = self.format_notification_message(filtered_bets)
            
            # Send to all subscribed users
            for user_id in self.subscribed_users:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user_id}: {e}")
                    self.subscribed_users.discard(user_id)
            
            logger.info(f"Sent notifications to {len(self.subscribed_users)} users about {len(filtered_bets)} value bets")
            
        except Exception as e:
            logger.error(f"Error in broadcast_value_bets: {e}")
    
    def format_notification_message(self, value_bets):
        """Format value bets for notification"""
        message = "🎯 *NEW VALUE BETS FOUND!*\n\n"
        
        for i, bet in enumerate(value_bets[:5], 1):  # Max 5 bets per notification
            message += f"📊 *Bet #{i}*\n"
            message += f"🏆 {bet['home_team']} vs {bet['away_team']}\n"
            message += f"💎 {bet['recommended_outcome']} @ {bet['odds']}\n"
            message += f"📈 Value: +{bet['value_margin']}%\n"
            message += f"🎲 EV: {bet['expected_value']}\n\n"
        
        message += "—\n"
        message += "🤖 *AI Betting Bot*"
        
        return message  # In production, use database
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎯 **AI Betting Assistant Bot**

Welcome! I analyze football matches and find value bets using AI.

📊 **Available Commands:**
/valuebets - Get today's value bets
/today - Get today's matches
/tomorrow - Get tomorrow's matches
/live - Get live matches now
/premier - Premier League matches
/laliga - La Liga matches
/seriea - Serie A matches
/bundesliga - Bundesliga matches
/analyze - Analyze specific match
/stats - Show betting statistics
/premium - Upgrade to premium
/help - Show all commands

📧 **Contact Admin**
For support and manual activation:
• Telegram: @admin
• Email: kevohmutwiri35@gmail.com
• WhatsApp: 0791674888
• Username: @Klaus_debbugg

⚠️ **Disclaimer:** This is an analysis tool, not financial advice. Bet responsibly!
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Get Value Bets", callback_data="valuebets")],
            [InlineKeyboardButton("📊 View Stats", callback_data="stats")],
            [InlineKeyboardButton("💎 Premium Features", callback_data="premium")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def value_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /valuebets command"""
        # Check if this is a callback query
        if update.callback_query:
            await update.callback_query.answer()
            # For callback, we need to use edit_message_text
            await update.callback_query.edit_message_text("🔍 Analyzing matches for value bets...")
            chat_id = update.callback_query.message.chat_id
            user_id = update.callback_query.from_user.id
        else:
            await update.message.reply_text("🔍 Analyzing matches for value bets...")
            chat_id = update.message.chat_id
            user_id = update.effective_user.id
        
        try:
            # Get current matches
            matches_data = self.data_collector.get_sample_data()
            
            # Find value bets
            value_bets = self.value_detector.find_value_bets(matches_data)
            
            if not value_bets:
                no_bets_message = (
                    "❌ No value bets found today.\n\n"
                    "Try again later for new matches!\n\n"
                    "📧 Contact: kevohmutwiri35@gmail.com"
                )
                if update.callback_query:
                    await update.callback_query.edit_message_text(no_bets_message)
                else:
                    await update.message.reply_text(no_bets_message)
                return
            
            # Format and send results
            message = self.format_value_bets_message(value_bets)
            
            # Check if user is premium for full details
            if user_id not in self.premium_users:
                message += "\n\n💎 *Premium users get full analysis and more bets!*\n"
                message += "Use /premium to upgrade"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            error_message = f"❌ Error analyzing matches: {str(e)}"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
            
            logger.error(f"Error in value_bets: {e}")
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - analyze a specific match"""
        if update.callback_query:
            await update.callback_query.answer()
        
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
        
        # For demo, show sample analysis
        analysis_message = f"""
📊 **Match Analysis**

🏆 *{home_team} vs {away_team}*

🤖 **AI Prediction:**
• Home Win: 45%
• Draw: 30%
• Away Win: 25%

📈 **Key Factors:**
• Recent form: Both teams showing mixed results
• Home advantage: Slight edge to home team
• H2H: Historically competitive

⚠️ **Note:** This is a demo analysis. 
For full AI-powered predictions, subscribe to value bets!

📧 Contact: kevohmutwiri35@gmail.com
        """
        
        await chat.reply_text(analysis_message, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "valuebets":
            await self.value_bets(update, context)
        elif query.data == "stats":
            await self.stats(update, context)
        elif query.data == "premium":
            await self.premium(update, context)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later.\n\n"
                    "📧 Contact: kevohmutwiri35@gmail.com"
                )
            except:
                pass
    
    async def get_today_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /today command - Get today's matches"""
        await self._send_matches_by_date(update, context, 'today')
    
    async def get_tomorrow_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tomorrow command - Get tomorrow's matches"""
        await self._send_matches_by_date(update, context, 'tomorrow')
    
    async def get_live_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /live command - Get live matches"""
        await self._send_matches_by_date(update, context, 'live')
    
    async def get_league_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premier, /laliga, /seriea, /bundesliga commands"""
        # Get league from command
        command = update.message.text.split('@')[0].lower().replace('/', '')
        league_map = {
            'premier': 'Premier League',
            'laliga': 'La Liga',
            'seriea': 'Serie A',
            'bundesliga': 'Bundesliga'
        }
        league = league_map.get(command, 'Premier League')
        
        await update.message.reply_text(f"🔍 Fetching {league} matches...")
        
        try:
            # Get matches filtered by league
            matches_data = self.data_collector.get_league_matches(league.lower().replace(' ', '_'))
            
            if not matches_data:
                # Fall back to real API
                matches_data = self.data_collector.get_matches_by_date('all')
                matches_data = [m for m in matches_data if league in m.get('league', '')]
            
            if not matches_data:
                await update.message.reply_text(f"❌ No {league} matches found.\n\nTry again later!")
                return
            
            # Format and send matches
            message = f"⚽ *{league} Matches*\n\n"
            for match in matches_data[:10]:
                message += f"🏆 {match['home_team']} vs {match['away_team']}\n"
                message += f"📅 {match['date']} | {match.get('league', 'Unknown')}\n"
                if match.get('home_odds'):
                    message += f"💰 Odds: {match['home_odds']} | {match['draw_odds']} | {match['away_odds']}\n"
                message += "\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching league matches: {e}")
            await update.message.reply_text("❌ Error fetching matches. Try again later!")
    
    async def _send_matches_by_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, date_filter: str):
        """Helper to send matches filtered by date"""
        date_labels = {'today': 'Today', 'tomorrow': 'Tomorrow', 'live': 'LIVE'}
        
        if update.callback_query:
            await update.callback_query.answer()
            chat_id = update.callback_query.message.chat_id
        else:
            chat_id = update.message.chat_id
            await update.message.reply_text(f"🔍 Fetching {date_labels.get(date_filter, date_filter)} matches...")
        
        try:
            # Get real matches from API
            matches_data = self.data_collector.get_matches_by_date(date_filter)
            
            if not matches_data:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ No {date_labels.get(date_filter, date_filter)} matches found.\n\nThe API might be rate-limited or no matches scheduled.\n\nTry again later!"
                )
                return
            
            # Format matches
            message = f"⚽ *{date_labels.get(date_filter, date_filter)}'s Matches*\n\n"
            for match in matches_data[:10]:
                status = match.get('status', 'SCHEDULED')
                message += f"🏆 {match['home_team']} vs {match['away_team']}\n"
                message += f"📅 {match['date']} | {match.get('league', 'Unknown')}\n"
                if match.get('home_goals') is not None:
                    message += f"🔢 Score: {match['home_goals']} - {match['away_goals']} ({status})\n"
                else:
                    message += f"⏰ Status: {status}\n"
                if match.get('home_odds'):
                    message += f"💰 Odds: {match['home_odds']} | {match['draw_odds']} | {match['away_odds']}\n"
                message += "\n"
            
            message += f"📊 Total: {len(matches_data)} matches\n"
            message += "💎 Use /valuebets to find value bets!"
            
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
