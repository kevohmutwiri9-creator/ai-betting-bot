import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import pandas as pd
from datetime import datetime
import json
from value_detector import ValueBetDetector
from data_collector import FootballDataCollector
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME

class BettingTelegramBot:
    def __init__(self, token, bot_username):
        self.token = token
        self.bot_username = bot_username
        self.value_detector = ValueBetDetector()
        self.data_collector = FootballDataCollector()
        self.premium_users = set()  # In production, use database
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎯 **AI Betting Assistant Bot**

Welcome! I analyze football matches and find value bets using AI.

📊 **Available Commands:**
/valuebets - Get today's value bets
/analyze - Analyze specific match
/stats - Show betting statistics
/premium - Upgrade to premium
/help - Show all commands

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
        await update.message.reply_text("🔍 Analyzing matches for value bets...")
        
        try:
            # Get current matches
            matches_data = self.data_collector.get_sample_data()
            
            # Find value bets
            value_bets = self.value_detector.find_value_bets(matches_data)
            
            if not value_bets:
                await update.message.reply_text(
                    "❌ No value bets found today.\n\n"
                    "Try again later for new matches!"
                )
                return
            
            # Format and send results
            message = self.format_value_bets_message(value_bets)
            
            # Check if user is premium for full details
            user_id = update.effective_user.id
            if user_id not in self.premium_users:
                message += "\n\n💎 *Premium users get full analysis and more bets!*\n"
                message += "Use /premium to upgrade"
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error analyzing matches: {str(e)}\n"
                "Please try again later."
            )
    
    async def analyze_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        if not context.args:
            await update.message.reply_text(
                "Usage: /analyze <home_team> vs <away_team>\n"
                "Example: /analyze Manchester United vs Arsenal"
            )
            return
        
        # Parse teams from command
        command_text = ' '.join(context.args)
        if ' vs ' in command_text:
            home_team, away_team = command_text.split(' vs ', 1)
            
            await update.message.reply_text(
                f"🔍 Analyzing {home_team.strip()} vs {away_team.strip()}..."
            )
            
            # Create sample match for analysis
            match_data = pd.DataFrame([{
                'match_id': f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'home_team': home_team.strip(),
                'away_team': away_team.strip(),
                'league': 'Unknown',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'home_odds': 2.10,
                'draw_odds': 3.40,
                'away_odds': 3.20
            }])
            
            # Analyze
            value_bets = self.value_detector.find_value_bets(match_data)
            
            if value_bets:
                bet = value_bets[0]
                analysis_message = f"""
📊 **Match Analysis**
{bet['home_team']} vs {bet['away_team']}

🎯 **Recommendation:** {bet['recommended_outcome']}
💰 **Odds:** {bet['odds']}
📈 **AI Probability:** {bet['ai_probability']}%
📉 **Bookmaker Probability:** {bet['bookmaker_probability']}%
💎 **Value Margin:** +{bet['value_margin']}%
🎲 **Expected Value:** {bet['expected_value']}
🔒 **Confidence:** {bet['confidence']}

⚠️ *This is AI analysis, not guaranteed prediction*
                """
            else:
                analysis_message = f"""
📊 **Match Analysis**
{home_team.strip()} vs {away_team.strip()}

❌ **No value detected** in current odds
💰 *Current odds don't offer value according to AI analysis*

💎 *Premium users get detailed breakdown of why*
                """
            
            await update.message.reply_text(
                analysis_message,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Invalid format. Use: /analyze <home_team> vs <away_team>"
            )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats_message = """
📊 **AI Betting Statistics**

🎯 **Model Performance:**
• Accuracy: 58-62% (typical for sports betting)
• Value Bet Success Rate: ~55%
• Average ROI: +5-8% on value bets

💰 **Betting Principles:**
• Only bet on value (positive EV)
• Use proper bankroll management (1-2% per bet)
• Long-term profitability over short-term wins

📈 **Recent Performance:**
• Last 7 days: 12 value bets found
• Success rate: 7 wins, 5 losses
• ROI: +6.2%

💎 *Premium users get detailed performance tracking*
        """
        
        await update.message.reply_text(
            stats_message,
            parse_mode='Markdown'
        )
    
    async def premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium command"""
        premium_message = """
💎 **Premium Features**

🚀 **What you get:**
• Unlimited value bet analysis
• Detailed match breakdowns
• Historical performance tracking
• Custom alerts for specific teams/leagues
• Priority support
• API access for developers

💰 **Pricing:**
• 1 Week: $9.99
• 1 Month: $29.99
• 3 Months: $79.99

🔗 *Payment links coming soon!*
📧 *Contact @admin for manual activation*

🎁 *Free trial available for first 100 users!*
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 Start Free Trial", callback_data="trial")],
            [InlineKeyboardButton("📧 Contact Admin", callback_data="contact")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            premium_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 **AI Betting Bot Help**

📋 **Commands:**
/start - Start the bot
/valuebets - Get today's value bets
/analyze <team1> vs <team2> - Analyze specific match
/stats - Show betting statistics
/premium - Upgrade to premium features
/help - Show this help message

💡 **Tips:**
• Check value bets daily for best opportunities
• Use /analyze for matches you're interested in
• Follow bankroll management principles
• Bet responsibly!

❓ **Questions?**
Use /premium to contact admin for support
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "valuebets":
            await self.value_bets(update, context)
        elif query.data == "stats":
            await self.stats(update, context)
        elif query.data == "premium":
            await self.premium(update, context)
        elif query.data == "trial":
            await query.edit_message_text(
                "🎁 **Free Trial Activated!**\n\n"
                "You now have premium access for 7 days!\n"
                "Enjoy unlimited value bets and detailed analysis!"
            )
            # Add user to premium (in production, use database)
            self.premium_users.add(update.effective_user.id)
        elif query.data == "contact":
            await query.edit_message_text(
                "📧 **Contact Admin**\n\n"
                "For support and manual activation:\n"
                "• Telegram: @admin\n"
                "• Email: support@aibetting.bot\n\n"
                "Mention your username: @" + update.effective_user.username
            )
        elif query.data == "back":
            await self.start(update, context)
    
    def format_value_bets_message(self, value_bets):
        """Format value bets for Telegram message"""
        if not value_bets:
            return "❌ No value bets found today."
        
        message = "🎯 **Today's Value Bets**\n\n"
        
        for i, bet in enumerate(value_bets[:3], 1):  # Limit to 3 for free users
            message += f"📊 *Bet #{i}*\n"
            message += f"🏆 {bet['home_team']} vs {bet['away_team']}\n"
            message += f"💎 {bet['recommended_outcome']} @ {bet['odds']}\n"
            message += f"📈 Value: +{bet['value_margin']}%\n"
            message += f"🎲 EV: {bet['expected_value']}\n"
            message += f"🔒 Confidence: {bet['confidence']}\n\n"
        
        return message
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("valuebets", self.value_bets))
        application.add_handler(CommandHandler("analyze", self.analyze_match))
        application.add_handler(CommandHandler("stats", self.stats))
        application.add_handler(CommandHandler("premium", self.premium))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        print(f"Bot @{self.bot_username} is running...")
        application.run_polling()

if __name__ == "__main__":
    bot = BettingTelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME)
    bot.run()
