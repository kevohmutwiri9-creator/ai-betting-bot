"""Live Match Tracking Commands for Telegram Bot"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def get_live_matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE, live_tracker):
    """Handle /live command - show live matches with scores and stats"""
    try:
        message = live_tracker.format_live_matches_message()
        
        keyboard = [
            [InlineKeyboardButton("Refresh", callback_data="refresh_live")],
            [InlineKeyboardButton("In-Play Bets", callback_data="inplay")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error fetching live matches: {e}")
        await update.message.reply_text("Error fetching live matches.")

async def get_inplay_bets_command(update: Update, context: ContextTypes.DEFAULT_TYPE, live_tracker):
    """Handle /inplay command - show in-play betting opportunities"""
    try:
        message = live_tracker.format_inplay_message()
        
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

async def subscribe_live_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE, subscribed_users: set):
    """Handle /livenotify command - subscribe to live match alerts"""
    user_id = update.effective_user.id
    subscribed_users.add(user_id)
    
    message = """
✅ **Live Match Alerts Enabled!**

You'll receive notifications when:
- Goals are scored
- Red cards shown
- Key betting opportunities arise
- Match momentum shifts

Use /unlivenotify to disable alerts.

⚠️ **Tips:**
- Alerts come with betting recommendations
- Act fast - odds change quickly
- Bet responsibly
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"User {user_id} subscribed to live alerts")

async def unsubscribe_live_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE, subscribed_users: set):
    """Handle /unlivenotify command - unsubscribe from live match alerts"""
    user_id = update.effective_user.id
    subscribed_users.discard(user_id)
    
    await update.message.reply_text(
        "❌ **Live Alerts Disabled**\n\n"
        "You've been unsubscribed from live match notifications.",
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user_id} unsubscribed from live alerts")
