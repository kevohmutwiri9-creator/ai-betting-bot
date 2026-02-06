"""Live Match Tracking Module for In-Play Betting"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

# Live matches cache
LIVE_MATCHES_CACHE = {}

# Sample live match data for demo
SAMPLE_LIVE_MATCHES = [
    {
        'match_id': 'live_001',
        'home_team': 'Arsenal',
        'away_team': 'Liverpool',
        'league': 'Premier League',
        'home_score': 1,
        'away_score': 1,
        'status': 'LIVE',
        'time': '67\'',
        'home_odds': 2.5,
        'draw_odds': 3.4,
        'away_odds': 2.8,
        'over_25_odds': 1.85,
        'under_25_odds': 1.95,
        'btts_yes': 1.7,
        'btts_no': 2.1,
        'home_corners': 5,
        'away_corners': 3,
        'home_cards': 2,
        'away_cards': 1,
        'possession': {'home': 48, 'away': 52},
        'shots_on_target': {'home': 4, 'away': 3},
        'last_event': 'Goal by Salah (67\')',
        ' momentum': 'home',
    },
    {
        'match_id': 'live_002',
        'home_team': 'Barcelona',
        'away_team': 'Real Madrid',
        'league': 'La Liga',
        'home_score': 0,
        'away_score': 0,
        'status': 'LIVE',
        'time': '23\'',
        'home_odds': 2.3,
        'draw_odds': 3.2,
        'away_odds': 3.0,
        'over_25_odds': 2.0,
        'under_25_odds': 1.8,
        'btts_yes': 1.85,
        'btts_no': 1.95,
        'home_corners': 2,
        'away_corners': 1,
        'home_cards': 0,
        'away_cards': 1,
        'possession': {'home': 55, 'away': 45},
        'shots_on_target': {'home': 2, 'away': 1},
        'last_event': 'Yellow card to Vinicius Jr (20\')',
        'momentum': 'neutral',
    },
    {
        'match_id': 'live_003',
        'home_team': 'Bayern Munich',
        'away_team': 'Dortmund',
        'league': 'Bundesliga',
        'home_score': 2,
        'away_score': 1,
        'status': 'LIVE',
        'time': '78\'',
        'home_odds': 1.4,
        'draw_odds': 4.5,
        'away_odds': 7.0,
        'over_25_odds': 1.35,
        'under_25_odds': 3.0,
        'btts_yes': 1.5,
        'btts_no': 2.5,
        'home_corners': 8,
        'away_corners': 4,
        'home_cards': 1,
        'away_cards': 3,
        'possession': {'home': 62, 'away': 38},
        'shots_on_target': {'home': 7, 'away': 4},
        'last_event': 'Goal by Kane (75\')',
        'momentum': 'home',
    },
    {
        'match_id': 'live_004',
        'home_team': 'Juventus',
        'away_team': 'Inter',
        'league': 'Serie A',
        'home_score': 1,
        'away_score': 2,
        'status': 'LIVE',
        'time': '55\'',
        'home_odds': 4.5,
        'draw_odds': 3.5,
        'away_odds': 1.8,
        'over_25_odds': 2.2,
        'under_25_odds': 1.65,
        'btts_yes': 1.9,
        'btts_no': 1.9,
        'home_corners': 3,
        'away_corners': 5,
        'home_cards': 2,
        'away_cards': 1,
        'possession': {'home': 45, 'away': 55},
        'shots_on_target': {'home': 2, 'away': 5},
        'last_event': 'Goal by Martinez (52\')',
        'momentum': 'away',
    },
    {
        'match_id': 'live_005',
        'home_team': 'Man City',
        'away_team': 'Chelsea',
        'league': 'Premier League',
        'home_score': 3,
        'away_score': 0,
        'status': 'LIVE',
        'time': '82\'',
        'home_odds': 1.1,
        'draw_odds': 8.0,
        'away_odds': 15.0,
        'over_35_odds': 1.45,
        'under_35_odds': 2.6,
        'btts_yes': 1.35,
        'btts_no': 3.0,
        'home_corners': 10,
        'away_corners': 2,
        'home_cards': 0,
        'away_cards': 2,
        'possession': {'home': 68, 'away': 32},
        'shots_on_target': {'home': 10, 'away': 1},
        'last_event': 'Hat-trick by Haaland (78\')',
        'momentum': 'home',
    },
]


class LiveMatchTracker:
    """Track live matches and in-play betting opportunities"""
    
    def __init__(self):
        self.live_matches = {}
        self.last_update = None
        self.update_interval = 30  # seconds
    
    def get_live_matches(self) -> List[Dict]:
        """Get current live matches"""
        # For demo, return sample data
        # In production, fetch from live API
        return SAMPLE_LIVE_MATCHES
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get details for a specific live match"""
        for match in SAMPLE_LIVE_MATCHES:
            if match['match_id'] == match_id:
                return match
        return None
    
    def get_inplay_bets(self) -> List[Dict]:
        """Get in-play betting opportunities"""
        opportunities = []
        
        for match in SAMPLE_LIVE_MATCHES:
            time = int(match['time'].replace('\'', ''))
            
            # Late goal opportunity
            if time > 75 and match['home_score'] == match['away_score']:
                opportunities.append({
                    'type': 'LATE_GOAL',
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'recommendation': 'Over 0.5 Goals',
                    'odds': 1.5,
                    'reason': f"Draw at {time}' - likely goal incoming",
                    'match_id': match['match_id'],
                })
            
            # Comeback opportunity
            if time > 60 and abs(match['home_score'] - match['away_score']) == 1:
                trailing_team = match['away_team'] if match['home_score'] > match['away_score'] else match['home_team']
                opportunities.append({
                    'type': 'COMEBACK',
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'recommendation': f'{trailing_team} to score next',
                    'odds': 2.2,
                    'reason': f"One goal deficit at {time}' - pressing for equalizer",
                    'match_id': match['match_id'],
                })
            
            # Over goals
            if time < 60 and match['home_score'] + match['away_score'] >= 2:
                opportunities.append({
                    'type': 'OVER_GOALS',
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'recommendation': 'Over 2.5 Goals',
                    'odds': match.get('over_25_odds', 1.8),
                    'reason': f"{match['home_score'] + match['away_score']} goals already at {time}'",
                    'match_id': match['match_id'],
                })
            
            # Corners opportunity
            if match.get('home_corners', 0) + match.get('away_corners', 0) >= 8:
                opportunities.append({
                    'type': 'CORNERS',
                    'match': f"{match['home_team']} vs {match['away_team']}",
                    'recommendation': 'Over 10.5 Corners',
                    'odds': 1.75,
                    'reason': f"High corner count ({match.get('home_corners', 0)} + {match.get('away_corners', 0)})",
                    'match_id': match['match_id'],
                })
        
        return opportunities[:10]
    
    def format_live_matches_message(self) -> str:
        """Format live matches for Telegram display"""
        matches = self.get_live_matches()
        
        if not matches:
            return "❌ No live matches at the moment."
        
        message = "🔴 **LIVE MATCHES**\n\n"
        
        for i, match in enumerate(matches, 1):
            status_emoji = "🔴" if match['status'] == 'LIVE' else "🟡"
            
            message += f"{status_emoji} *Match #{i}*\n"
            message += f"🏆 **{match['home_team']}** {match['home_score']} - {match['away_score']} **{match['away_team']}**\n"
            message += f"⏱️ {match['time']} | {match['league']}\n"
            
            message += f"💰 **Odds:** {match['home_odds']:.2f} | {match['draw_odds']:.2f} | {match['away_odds']:.2f}\n"
            
            message += f"📊 **Stats:** 🏐 {match.get('home_corners', 0)} corners | 🎯 {match.get('shots_on_target', {}).get('home', 0)} shots\n"
            
            message += f"📝 *{match['last_event']}*\n"
            message += "\n"
        
        message += "—" * 20 + "\n\n"
        message += "💡 **Tips:**\n"
        message += "• Watch momentum shifts\n"
        message += "• Check injury time opportunities\n"
        message += "• Look for tired defense late game\n\n"
        
        message += "⚠️ **In-Play Betting:**\n"
        message += "• Odds change rapidly\n"
        message += "• Bet responsibly\n"
        message += "• 18+ Only"
        
        return message
    
    def format_inplay_message(self) -> str:
        """Format in-play betting opportunities"""
        opportunities = self.get_inplay_bets()
        
        if not opportunities:
            return "❌ No in-play betting opportunities at the moment."
        
        message = "🎯 **IN-PLAY BETTING OPPORTUNITIES**\n\n"
        message += f"📅 Updated: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        type_icons = {
            'LATE_GOAL': '⚽',
            'COMEBACK': '🔥',
            'OVER_GOALS': '📈',
            'CORNERS': '🏐',
        }
        
        for i, opp in enumerate(opportunities, 1):
            icon = type_icons.get(opp['type'], '💎')
            
            message += f"{icon} **Opportunity #{i}** ({opp['type']})\n"
            message += f"⚽ {opp['match']}\n"
            message += f"💎 **{opp['recommendation']}** @ {opp['odds']:.2f}\n"
            message += f"📝 {opp['reason']}\n\n"
        
        message += "—" * 20 + "\n\n"
        message += "⚠️ **Disclaimer:**\n"
        message += "• Live betting carries higher risk\n"
        message += "• Odds change rapidly\n"
        message += "• Never bet more than you can afford\n"
        message += "• 18+ Only | Gamble responsibly"
        
        return message
    
    def get_live_odds_change(self, match_id: str) -> Dict:
        """Get odds changes for a match (simulated)"""
        match = self.get_match_details(match_id)
        if not match:
            return {}
        
        return {
            'match_id': match_id,
            'home_odds_change': f"+{0.1:.2f}" if match['home_score'] >= match['away_score'] else f"-{0.1:.2f}",
            'away_odds_change': f"+{0.2:.2f}" if match['away_score'] > match['home_score'] else f"-{0.15:.2f}",
            'draw_odds_change': "-0.15" if abs(match['home_score'] - match['away_score']) > 1 else "+0.1",
            'last_update': datetime.now().strftime('%H:%M:%S'),
        }
    
    def subscribe_to_match(self, user_id: int, match_id: str) -> bool:
        """Subscribe user to match updates"""
        if match_id not in self.live_matches:
            self.live_matches[match_id] = set()
        self.live_matches[match_id].add(user_id)
        return True
    
    def unsubscribe_from_match(self, user_id: int, match_id: str) -> bool:
        """Unsubscribe user from match updates"""
        if match_id in self.live_matches:
            self.live_matches[match_id].discard(user_id)
            return True
        return False


# Singleton instance
live_tracker = LiveMatchTracker()
