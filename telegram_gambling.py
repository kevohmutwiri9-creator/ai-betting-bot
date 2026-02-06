"""Gambling/Casino Commands for Telegram Bot"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Casino games data
CASINO_GAMES = [
    {'name': 'Blackjack', 'vs': 'Dealer', 'odds_home': 1.95, 'odds_away': 2.05, 'type': 'Casino'},
    {'name': 'Roulette', 'vs': 'House', 'odds_home': 2.37, 'odds_away': 2.37, 'type': 'Casino'},
    {'name': 'Baccarat', 'vs': 'Player', 'odds_home': 1.95, 'odds_away': 2.05, 'type': 'Casino'},
    {'name': 'Poker', 'vs': 'Players', 'odds_home': 2.0, 'odds_away': 1.8, 'type': 'Casino'},
    {'name': 'Dice', 'vs': 'Roll', 'odds_home': 1.9, 'odds_away': 1.9, 'type': 'Casino'},
]

# Virtual sports data
VIRTUAL_MATCHES = [
    {'home': 'Virtual Madrid', 'away': 'Virtual Barca', 'h_odds': 2.1, 'd_odds': 3.2, 'a_odds': 2.9},
    {'home': 'Virtual Chelsea', 'away': 'Virtual Arsenal', 'h_odds': 1.95, 'd_odds': 3.4, 'a_odds': 3.1},
    {'home': 'Virtual Bayern', 'away': 'Virtual Dortmund', 'h_odds': 1.85, 'd_odds': 3.5, 'a_odds': 3.3},
    {'home': 'Virtual Juventus', 'away': 'Virtual Milan', 'h_odds': 2.0, 'd_odds': 3.1, 'a_odds': 3.0},
]

# Betika matches
BETIKA_MATCHES = [
    {'home': 'Man United', 'away': 'Man City', 'h': 3.2, 'd': 3.4, 'a': 2.1, 'league': 'Premier League'},
    {'home': 'Liverpool', 'away': 'Arsenal', 'h': 1.9, 'd': 3.6, 'a': 3.8, 'league': 'Premier League'},
    {'home': 'Barcelona', 'away': 'Sevilla', 'h': 1.5, 'd': 4.2, 'a': 6.0, 'league': 'La Liga'},
    {'home': 'PSG', 'away': 'Lyon', 'h': 1.55, 'd': 4.0, 'a': 5.5, 'league': 'Ligue 1'},
]

# SportPesa matches
SPORTPESA_MATCHES = [
    {'home': 'Tottenham', 'away': 'Newcastle', 'h': 1.8, 'd': 3.5, 'a': 4.0, 'league': 'Premier League'},
    {'home': 'Real Madrid', 'away': 'Atletico', 'h': 1.7, 'd': 3.3, 'a': 4.5, 'league': 'La Liga'},
    {'home': 'Bayern', 'away': 'Leverkusen', 'h': 1.6, 'd': 3.8, 'a': 4.5, 'league': 'Bundesliga'},
]

async def get_casino_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /casino and /slots commands"""
    try:
        message = "🎰 **Casino Games & Slots**\n\n"
        
        for game in CASINO_GAMES:
            message += f"🎲 **{game['name']}** vs {game['vs']}\n"
            message += f"💰 Odds: {game['odds_home']} | {game['odds_away']}\n"
            message += f"🏷️ {game['type']}\n\n"
        
        message += "—" * 20 + "\n\n"
        message += "🎰 **Popular Slots**\n"
        message += "• Mega Fortune\n"
        message += "• Starburst\n"
        message += "• Book of Ra\n"
        message += "• Gonzo's Quest\n"
        message += "• Mega Moolah\n\n"
        
        message += "⚠️ **Play Responsibly!**\n"
        message += "🎰 18+ Only\n"
        message += "💰 Set limits before playing"
        
        keyboard = [
            [InlineKeyboardButton("🎰 Play Now", url="https://betika.com")],
            [InlineKeyboardButton("🎰 Slots", callback_data="slots")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in get_casino_games: {e}")
        await update.message.reply_text("❌ Error loading casino games.")

async def get_virtual_sports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /virtual command"""
    try:
        message = "🎮 **Virtual Sports**\n\n"
        message += "⏱️ New matches every 3 minutes!\n\n"
        
        for match in VIRTUAL_MATCHES:
            message += f"⚽ **{match['home']}** vs **{match['away']}**\n"
            message += f"💰 {match['h_odds']} | {match['d_odds']} | {match['a_odds']}\n\n"
        
        message += "🎮 **Virtual Leagues Available:**\n"
        message += "• Virtual Football\n"
        message += "• Virtual Basketball\n"
        message += "• Virtual Tennis\n"
        message += "• Virtual Horse Racing\n\n"
        
        message += "⚠️ **Play Responsibly!**\n"
        message += "🎰 18+ Only"
        
        keyboard = [
            [InlineKeyboardButton("🎮 Bet Virtuals", callback_data="virtual_bet")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in get_virtual_sports: {e}")
        await update.message.reply_text("❌ Error loading virtual sports.")

async def get_jackpot_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /jackpot command"""
    try:
        message = "🏆 **Jackpot Predictions**\n\n"
        message += "📅 Last Updated: Today\n"
        message += "📊 Tip Accuracy: 65-75%\n\n"
        
        message += "—" * 20 + "\n\n"
        message += "📋 **Betika JP (17 Games)**\n\n"
        
        tips = [
            ("Man City", "Liverpool", "1", 75),
            ("Arsenal", "Chelsea", "1", 70),
            ("Barcelona", "Real Madrid", "X", 60),
            ("Bayern", "Dortmund", "1", 72),
            ("Juventus", "Inter", "1", 68),
            ("PSG", "Monaco", "1", 78),
            ("Tottenham", "Man United", "2", 55),
            ("Atletico", "Sevilla", "1", 65),
        ]
        
        for i, (home, away, pred, conf) in enumerate(tips, 1):
            message += f"{i}. {home} vs {away}: **{pred}** ({conf}%)\n"
        
        message += "\n" + "—" * 20 + "\n\n"
        message += "📋 **SportPesa JP (13 Games)**\n\n"
        
        tips2 = [
            ("Chelsea", "Liverpool", "2", 70),
            ("Real Madrid", "Atletico", "1", 68),
            ("Bayern", "Leverkusen", "1", 75),
            ("Juventus", "AC Milan", "1", 65),
            ("Barcelona", "Valencia", "1", 80),
        ]
        
        for i, (home, away, pred, conf) in enumerate(tips2, 1):
            message += f"{i}. {home} vs {away}: **{pred}** ({conf}%)\n"
        
        message += "\n" + "—" * 20 + "\n\n"
        message += "💰 **Betika JP:** KES 10,000,000+\n"
        message += "💰 **SportPesa JP:** KES 5,000,000+\n\n"
        
        message += "⚠️ **Disclaimer:**\n"
        message += "• Predictions only - bet at own risk\n"
        message += "• Never bet more than you can afford\n"
        message += "• 18+ Only\n"
        message += "• Gamble responsibly"
        
        keyboard = [
            [InlineKeyboardButton("🎰 Betika JP", url="https://betika.com/jackpot")],
            [InlineKeyboardButton("📊 SportPesa JP", url="https://sportpesa.com/jackpot")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in get_jackpot_bets: {e}")
        await update.message.reply_text("❌ Error loading jackpot predictions.")

async def get_betika_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /betika command"""
    try:
        message = "🎰 **Betika Matches**\n\n"
        
        for match in BETIKA_MATCHES:
            message += f"⚽ **{match['home']}** vs **{match['away']}**\n"
            message += f"💰 {match['h']} | {match['d']} | {match['a']}\n"
            message += f"🏷️ {match['league']}\n\n"
        
        message += "—" * 20 + "\n\n"
        message += "📱 **Betika Available On:**\n"
        message += "• Website: betika.com\n"
        message += "• Android App\n"
        message += "• iOS App\n"
        message += "• USSD: *790#\n\n"
        
        message += "🎁 **New Customer Bonus:**\n"
        message += "• 100% up to KES 500 on first deposit!\n\n"
        
        message += "🎰 **Other Betika Games:**\n"
        message += "• Casino & Slots\n"
        message += "• Virtual Sports\n"
        message += "• Jackpot\n"
        message += "• Lucky Numbers\n\n"
        
        message += "⚠️ Play responsibly! 18+ Only"
        
        keyboard = [
            [InlineKeyboardButton("🎰 Open Betika", url="https://betika.com")],
            [InlineKeyboardButton("🎰 Casino", callback_data="betika_casino")],
            [InlineKeyboardButton("🎮 Virtuals", callback_data="betika_virtual")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in get_betika_matches: {e}")
        await update.message.reply_text("❌ Error loading Betika matches.")

async def get_sportpesa_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sportpesa command"""
    try:
        message = "📊 **SportPesa Matches**\n\n"
        
        for match in SPORTPESA_MATCHES:
            message += f"⚽ **{match['home']}** vs **{match['away']}**\n"
            message += f"💰 {match['h']} | {match['d']} | {match['a']}\n"
            message += f"🏷️ {match['league']}\n\n"
        
        message += "—" * 20 + "\n\n"
        message += "📱 **SportPesa Available On:**\n"
        message += "• Website: sportpesa.com\n"
        message += "• Android App\n"
        message += "• iOS App\n\n"
        
        message += "💥 **Mega Jackpot:**\n"
        message += "• Every Weekend!\n"
        message += "• KES 5,000,000+ to win\n"
        message += "• Predict 17 games correctly\n\n"
        
        message += "📊 **Other SportPesa Games:**\n"
        message += "• Casino & Games\n"
        message += "• Virtual Sports\n"
        message += "• Aviator\n"
        message += "• Lucky Numbers\n\n"
        
        message += "⚠️ Play responsibly! 18+ Only"
        
        keyboard = [
            [InlineKeyboardButton("📊 Open SportPesa", url="https://sportpesa.com")],
            [InlineKeyboardButton("💥 Jackpot", callback_data="sportpesa_jackpot")],
            [InlineKeyboardButton("🎮 Aviator", callback_data="sportpesa_aviator")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in get_sportpesa_matches: {e}")
        await update.message.reply_text("❌ Error loading SportPesa matches.")

async def get_odibet_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /odibet command"""
    try:
        message = "🎯 **Odibet Matches**\n\n"
        
        odibet_matches = [
            {'home': 'Gor Mahia', 'away': 'Amujae', 'h': 1.4, 'd': 3.8, 'a': 6.0, 'league': 'KPL'},
            {'home': 'AFC Leopards', 'away': 'Tusker', 'h': 2.5, 'd': 3.2, 'a': 2.5, 'league': 'KPL'},
        ]
        
        for match in odibet_matches:
            message += f"⚽ **{match['home']}** vs **{match['away']}**\n"
            message += f"💰 {match['h']} | {match['d']} | {match['a']}\n"
            message += f"🏷️ {match['league']}\n\n"
        
        message += "📱 **Odibet Available On:**\n"
        message += "• Website: odibets.com\n"
        message += "• Android App\n"
        message += "• iOS App\n\n"
        
        message += "🎁 **Daily Boosts & Offers!**\n\n"
        message += "⚠️ Play responsibly! 18+ Only"
        
        keyboard = [
            [InlineKeyboardButton("🎯 Open Odibet", url="https://odibets.com")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in get_odibet_matches: {e}")
        await update.message.reply_text("❌ Error loading Odibet matches.")
