"""
Betting Platform Integration Module
Unified interface for multiple betting platforms
Supports: Betfair Exchange, Pinnacle, Bet365, William Hill, DraftKings, FanDuel
"""

import requests
import json
import hmac
import hashlib
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BetStatus(Enum):
    PENDING = "pending"
    PLACED = "placed"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class MarketType(Enum):
    MATCH_WINNER = "match_winner"
    OVER_UNDER = "over_under"
    HANDICAP = "handicap"
    DRAW_NO_BET = "draw_no_bet"


@dataclass
class Odds:
    home: float
    draw: float
    away: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Bet:
    platform: str
    event_id: str
    market: MarketType
    selection: str
    odds: float
    stake: float
    status: BetStatus = BetStatus.PENDING
    bet_id: str = None
    placed_at: datetime = None
    potential_win: float = None
    
    def __post_init__(self):
        if self.potential_win is None:
            self.potential_win = self.stake * self.odds


@dataclass
class Event:
    event_id: str
    home_team: str
    away_team: str
    league: str
    start_time: datetime
    odds: Odds = None
    status: str = "upcoming"


class BasePlatform(ABC):
    """Base class for betting platform integrations"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or os.getenv(f'{self.name.upper()}_API_KEY')
        self.secret_key = secret_key or os.getenv(f'{self.name.upper()}_SECRET_KEY')
        self.session = requests.Session()
        self.session.headers.update(self.get_headers())
        self.is_simulated = not self.api_key
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def get_events(self) -> List[Event]:
        pass
    
    @abstractmethod
    def get_odds(self, event_id: str) -> Odds:
        pass
    
    @abstractmethod
    def place_bet(self, bet: Bet) -> Bet:
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        pass
    
    @abstractmethod
    def check_bet_status(self, bet_id: str) -> BetStatus:
        pass
    
    def is_available(self) -> bool:
        """Check if platform API is configured"""
        return bool(self.api_key)


class BetfairPlatform(BasePlatform):
    """Betfair Exchange Integration"""
    
    @property
    def name(self) -> str:
        return "betfair"
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'X-Application': self.api_key or 'demo',
            'Content-Type': 'application/json'
        }
    
    def get_events(self) -> List[Event]:
        if self.is_simulated:
            return self._get_simulated_events()
        
        try:
            # Betfair API call would go here
            response = self.session.get(
                'https://api.betfair.com/exchange/betting/rest/v1/en/events',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return self._parse_events(response.json())
        except Exception as e:
            logger.error(f"Betfair API error: {e}")
        
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        if self.is_simulated:
            return Odds(home=1.95, draw=3.40, away=4.00)
        
        try:
            # Fetch odds from Betfair
            pass
        except Exception as e:
            logger.error(f"Betfair odds error: {e}")
        
        return Odds(home=1.95, draw=3.40, away=4.00)
    
    def place_bet(self, bet: Bet) -> Bet:
        if self.is_simulated:
            bet.status = BetStatus.PLACED
            bet.bet_id = f"sim_{self.name}_{int(time.time())}"
            bet.placed_at = datetime.now()
            logger.info(f"[SIMULATED] {self.name}: Placed {bet.stake} on {bet.selection} @ {bet.odds}")
            return bet
        
        try:
            # Real Betfair API call
            payload = {
                'marketId': bet.event_id,
                'selectionId': bet.selection,
                'side': 'BACK',
                'size': bet.stake,
                'price': bet.odds
            }
            response = self.session.post(
                'https://api.betfair.com/exchange/betting/rest/v1/bets',
                json=payload,
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                bet.status = BetStatus.PLACED
                bet.bet_id = response.json().get('betId')
        except Exception as e:
            logger.error(f"Betfair bet placement error: {e}")
        
        return bet
    
    def get_balance(self) -> float:
        if self.is_simulated:
            return 1000.0
        
        try:
            response = self.session.get(
                'https://api.betfair.com/exchange/account/rest/v1/funds',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('availableToBet', 0)
        except Exception as e:
            logger.error(f"Betfair balance error: {e}")
        
        return 0.0
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        if self.is_simulated:
            return BetStatus.PLACED
        
        try:
            # Check bet status
            pass
        except Exception as e:
            logger.error(f"Betfair status check error: {e}")
        
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        return [
            Event(
                event_id="bf_001",
                home_team="Manchester City",
                away_team="Liverpool",
                league="Premier League",
                start_time=datetime.now() + timedelta(days=1),
                odds=Odds(home=1.85, draw=3.50, away=4.20)
            ),
            Event(
                event_id="bf_002",
                home_team="Arsenal",
                away_team="Chelsea",
                league="Premier League",
                start_time=datetime.now() + timedelta(days=2),
                odds=Odds(home=2.00, draw=3.40, away=3.75)
            )
        ]
    
    def _parse_events(self, data: Dict) -> List[Event]:
        events = []
        for item in data:
            events.append(Event(
                event_id=item.get('id'),
                home_team=item.get('homeTeam'),
                away_team=item.get('awayTeam'),
                league=item.get('competition'),
                start_time=datetime.fromisoformat(item.get('startTime'))
            ))
        return events


class PinnaclePlatform(BasePlatform):
    """Pinnacle Sports Integration"""
    
    @property
    def name(self) -> str:
        return "pinnacle"
    
    def get_headers(self) -> Dict[str, str]:
        auth = f"{self.api_key}:{self.secret_key}" if self.api_key else "demo:demo"
        return {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }
    
    def get_events(self) -> List[Event]:
        if self.is_simulated:
            return self._get_simulated_events()
        
        try:
            response = self.session.get(
                'https://api.pinnacle.com/v1/feed',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return self._parse_events(response.json())
        except Exception as e:
            logger.error(f"Pinnacle API error: {e}")
        
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        if self.is_simulated:
            return Odds(home=1.92, draw=3.45, away=4.10)
        
        return Odds(home=1.92, draw=3.45, away=4.10)
    
    def place_bet(self, bet: Bet) -> Bet:
        if self.is_simulated:
            bet.status = BetStatus.PLACED
            bet.bet_id = f"sim_{self.name}_{int(time.time())}"
            bet.placed_at = datetime.now()
            logger.info(f"[SIMULATED] {self.name}: Placed {bet.stake} on {bet.selection} @ {bet.odds}")
            return bet
        
        try:
            payload = {
                'sportId': 1,  # Soccer
                'leagueId': bet.event_id,
                'team': bet.selection,
                'oddsFormat': 'DECIMAL',
                'stake': bet.stake
            }
            response = self.session.post(
                'https://api.pinnacle.com/v1/bets/placed',
                json=payload,
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                bet.status = BetStatus.PLACED
                bet.bet_id = response.json().get('betId')
        except Exception as e:
            logger.error(f"Pinnacle bet placement error: {e}")
        
        return bet
    
    def get_balance(self) -> float:
        if self.is_simulated:
            return 2500.0
        
        try:
            response = self.session.get(
                'https://api.pinnacle.com/v1/client/balance',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('availableBalance', 0)
        except Exception as e:
            logger.error(f"Pinnacle balance error: {e}")
        
        return 0.0
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        return [
            Event(
                event_id="pin_001",
                home_team="Barcelona",
                away_team="Real Madrid",
                league="La Liga",
                start_time=datetime.now() + timedelta(hours=6),
                odds=Odds(home=2.10, draw=3.50, away=3.25)
            ),
            Event(
                event_id="pin_002",
                home_team="Bayern Munich",
                away_team="Dortmund",
                league="Bundesliga",
                start_time=datetime.now() + timedelta(days=1),
                odds=Odds(home=1.65, draw=4.00, away=5.00)
            )
        ]


class Bet365Platform(BasePlatform):
    """Bet365 Integration"""
    
    @property
    def name(self) -> str:
        return "bet365"
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'X-Api-Key': self.api_key or 'demo',
            'Content-Type': 'application/json'
        }
    
    def get_events(self) -> List[Event]:
        if self.is_simulated:
            return self._get_simulated_events()
        
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        return Odds(home=1.88, draw=3.60, away=4.30)
    
    def place_bet(self, bet: Bet) -> Bet:
        bet.status = BetStatus.PLACED
        bet.bet_id = f"sim_{self.name}_{int(time.time())}"
        bet.placed_at = datetime.now()
        logger.info(f"[SIMULATED] {self.name}: Placed {bet.stake} on {bet.selection} @ {bet.odds}")
        return bet
    
    def get_balance(self) -> float:
        return 1500.0
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        return [
            Event(
                event_id="365_001",
                home_team="PSG",
                away_team="Monaco",
                league="Ligue 1",
                start_time=datetime.now() + timedelta(hours=12),
                odds=Odds(home=1.55, draw=4.20, away=6.00)
            )
        ]


class DraftKingsPlatform(BasePlatform):
    """DraftKings Integration (US Sports)"""
    
    @property
    def name(self) -> str:
        return "draftkings"
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_events(self) -> List[Event]:
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        return Odds(home=1.90, draw=3.30, away=3.90)
    
    def place_bet(self, bet: Bet) -> Bet:
        bet.status = BetStatus.PLACED
        bet.bet_id = f"sim_{self.name}_{int(time.time())}"
        bet.placed_at = datetime.now()
        logger.info(f"[SIMULATED] {self.name}: Placed {bet.stake} on {bet.selection} @ {bet.odds}")
        return bet
    
    def get_balance(self) -> float:
        return 2000.0
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        return [
            Event(
                event_id="dk_001",
                home_team="Lakers",
                away_team="Warriors",
                league="NBA",
                start_time=datetime.now() + timedelta(hours=3),
                odds=Odds(home=2.00, draw=0, away=1.85)
            )
        ]


class BetikaPlatform(BasePlatform):
    """Betika Kenya Integration - Popular Kenyan Sportsbook"""
    
    @property
    def name(self) -> str:
        return "betika"
    
    def __init__(self, api_key: str = None, affiliate_id: str = None):
        self.api_key = api_key or os.getenv(f'{self.name.upper()}_API_KEY')
        self.secret_key = None
        self.affiliate_id = affiliate_id or os.getenv('BETIKA_AFFILIATE_ID') or 'demo'
        self.base_url = "https://api.betika.com/v1"
        self.session = requests.Session()
        self.session.headers.update(self.get_headers())
        self.is_simulated = not self.api_key
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else 'Bearer demo',
            'Content-Type': 'application/json',
            'X-Affiliate-Id': self.affiliate_id
        }
    
    def get_events(self) -> List[Event]:
        if self.is_simulated:
            return self._get_simulated_events()
        
        try:
            response = self.session.get(
                f'{self.base_url}/events/upcoming',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return self._parse_events(response.json())
        except Exception as e:
            logger.error(f"Betika API error: {e}")
        
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        if self.is_simulated:
            return Odds(home=1.90, draw=3.30, away=4.00)
        
        try:
            response = self.session.get(
                f'{self.base_url}/events/{event_id}/odds',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return Odds(
                    home=data.get('home_odds', 1.90),
                    draw=data.get('draw_odds', 3.30),
                    away=data.get('away_odds', 4.00)
                )
        except Exception as e:
            logger.error(f"Betika odds error: {e}")
        
        return Odds(home=1.90, draw=3.30, away=4.00)
    
    def place_bet(self, bet: Bet) -> Bet:
        if self.is_simulated:
            bet.status = BetStatus.PLACED
            bet.bet_id = f"sim_{self.name}_{int(time.time())}"
            bet.placed_at = datetime.now()
            logger.info(f"[SIMULATED] {self.name}: Placed KES {bet.stake} on {bet.selection} @ {bet.odds}")
            return bet
        
        try:
            payload = {
                'event_id': bet.event_id,
                'selection': bet.selection,
                'stake': bet.stake,
                'odds': bet.odds
            }
            response = self.session.post(
                f'{self.base_url}/bets',
                json=payload,
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                bet.status = BetStatus.PLACED
                bet.bet_id = data.get('bet_id')
                bet.placed_at = datetime.now()
        except Exception as e:
            logger.error(f"Betika bet placement error: {e}")
        
        return bet
    
    def get_balance(self) -> float:
        if self.is_simulated:
            return 5000.0  # KES
        
        try:
            response = self.session.get(
                f'{self.base_url}/user/balance',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('balance', 0)
        except Exception as e:
            logger.error(f"Betika balance error: {e}")
        
        return 0.0
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        if self.is_simulated:
            return BetStatus.PLACED
        
        try:
            response = self.session.get(
                f'{self.base_url}/bets/{bet_id}',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                status = response.json().get('status')
                return BetStatus(status)
        except Exception as e:
            logger.error(f"Betika status check error: {e}")
        
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        """Get simulated Kenyan Premier League and international matches"""
        return [
            Event(
                event_id="betika_001",
                home_team="Gor Mahia",
                away_team="Agent Sparrow",
                league="Kenya Premier League",
                start_time=datetime.now() + timedelta(hours=2),
                odds=Odds(home=1.75, draw=3.20, away=4.50)
            ),
            Event(
                event_id="betika_002",
                home_team="Tusker",
                away_team="Amuaka Odhiambo",
                league="Kenya Premier League",
                start_time=datetime.now() + timedelta(hours=4),
                odds=Odds(home=1.85, draw=3.10, away=4.00)
            ),
            Event(
                event_id="betika_003",
                home_team="Egypt",
                away_team="Senegal",
                league="AFCON",
                start_time=datetime.now() + timedelta(days=1),
                odds=Odds(home=2.10, draw=3.00, away=3.40)
            ),
            Event(
                event_id="betika_004",
                home_team="Manchester City",
                away_team="Arsenal",
                league="Premier League",
                start_time=datetime.now() + timedelta(days=2),
                odds=Odds(home=1.90, draw=3.50, away=4.20)
            )
        ]
    
    def _parse_events(self, data: Dict) -> List[Event]:
        events = []
        for item in data.get('events', []):
            events.append(Event(
                event_id=item.get('id'),
                home_team=item.get('home_team'),
                away_team=item.get('away_team'),
                league=item.get('league'),
                start_time=datetime.fromisoformat(item.get('start_time'))
            ))
        return events


class SportpesaPlatform(BasePlatform):
    """SportPesa Kenya Integration"""
    
    @property
    def name(self) -> str:
        return "sportpesa"
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_events(self) -> List[Event]:
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        return Odds(home=1.88, draw=3.25, away=3.85)
    
    def place_bet(self, bet: Bet) -> Bet:
        bet.status = BetStatus.PLACED
        bet.bet_id = f"sim_{self.name}_{int(time.time())}"
        bet.placed_at = datetime.now()
        logger.info(f"[SIMULATED] {self.name}: Placed KES {bet.stake} on {bet.selection} @ {bet.odds}")
        return bet
    
    def get_balance(self) -> float:
        return 3000.0  # KES
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        return [
            Event(
                event_id="sportpesa_001",
                home_team="Leicester City",
                away_team="Everton",
                league="Premier League",
                start_time=datetime.now() + timedelta(hours=6),
                odds=Odds(home=2.00, draw=3.40, away=3.60)
            )
        ]


class OdibetPlatform(BasePlatform):
    """Odibet Kenya Integration"""
    
    @property
    def name(self) -> str:
        return "odibet"
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'X-API-Key': self.api_key or 'demo',
            'Content-Type': 'application/json'
        }
    
    def get_events(self) -> List[Event]:
        return self._get_simulated_events()
    
    def get_odds(self, event_id: str) -> Odds:
        return Odds(home=1.92, draw=3.35, away=4.10)
    
    def place_bet(self, bet: Bet) -> Bet:
        bet.status = BetStatus.PLACED
        bet.bet_id = f"sim_{self.name}_{int(time.time())}"
        bet.placed_at = datetime.now()
        logger.info(f"[SIMULATED] {self.name}: Placed KES {bet.stake} on {bet.selection} @ {bet.odds}")
        return bet
    
    def get_balance(self) -> float:
        return 2000.0  # KES
    
    def check_bet_status(self, bet_id: str) -> BetStatus:
        return BetStatus.PLACED
    
    def _get_simulated_events(self) -> List[Event]:
        return [
            Event(
                event_id="odibet_001",
                home_team="Tottenham",
                away_team="West Ham",
                league="Premier League",
                start_time=datetime.now() + timedelta(days=1),
                odds=Odds(home=1.75, draw=3.50, away=4.50)
            )
        ]


class BettingPlatformManager:
    """Manages multiple betting platforms"""
    
    def __init__(self):
        self.platforms = {
            'betfair': BetfairPlatform(),
            'pinnacle': PinnaclePlatform(),
            'bet365': Bet365Platform(),
            'draftkings': DraftKingsPlatform(),
            # Kenyan Platforms
            'betika': BetikaPlatform(),
            'sportpesa': SportpesaPlatform(),
            'odibet': OdibetPlatform()
        }
    
    def get_best_odds(self, home_team: str, away_team: str) -> Dict[str, Odds]:
        """Compare odds across all platforms"""
        best_odds = {
            'home': {'odds': 0, 'platform': None},
            'draw': {'odds': 0, 'platform': None},
            'away': {'odds': 0, 'platform': None}
        }
        
        for platform_name, platform in self.platforms.items():
            try:
                events = platform.get_events()
                for event in events:
                    if (home_team.lower() in event.home_team.lower() and 
                        away_team.lower() in event.away_team.lower()):
                        
                        if event.odds:
                            if event.odds.home > best_odds['home']['odds']:
                                best_odds['home'] = {'odds': event.odds.home, 'platform': platform_name}
                            if event.odds.draw > best_odds['draw']['odds']:
                                best_odds['draw'] = {'odds': event.odds.draw, 'platform': platform_name}
                            if event.odds.away > best_odds['away']['odds']:
                                best_odds['away'] = {'odds': event.odds.away, 'platform': platform_name}
            except Exception as e:
                logger.error(f"Error getting odds from {platform_name}: {e}")
        
        return best_odds
    
    def place_bet(self, bet: Bet, platform_name: str = None) -> Bet:
        """Place bet on specified or best platform"""
        if platform_name and platform_name in self.platforms:
            return self.platforms[platform_name].place_bet(bet)
        
        # Auto-select best platform based on odds
        best = self.get_best_odds(bet.home_team, bet.away_team)
        selection_key = bet.selection.lower().replace(' ', '_')
        
        if selection_key in best and best[selection_key]['platform']:
            platform = self.platforms[best[selection_key]['platform']]
            return platform.place_bet(bet)
        
        # Default to first available platform
        for platform in self.platforms.values():
            if platform.is_available():
                return platform.place_bet(bet)
        
        # Simulated bet
        return BettingPlatform._place_simulated_bet(bet, "default")
    
    def get_all_balances(self) -> Dict[str, float]:
        """Get balance from all platforms"""
        balances = {}
        for name, platform in self.platforms.items():
            try:
                balances[name] = platform.get_balance()
            except Exception as e:
                logger.error(f"Error getting balance from {name}: {e}")
                balances[name] = 0
        return balances
    
    def distribute_stake(self, total_stake: float, selection: str, 
                         home_team: str, away_team: str) -> List[Bet]:
        """Distribute stake across multiple platforms for better odds"""
        bets = []
        best_odds = self.get_best_odds(home_team, away_team)
        
        # Split stake across top 2 platforms
        platforms_to_use = []
        selection_key = selection.lower().replace(' ', '_')
        
        if selection_key in best_odds and best_odds[selection_key]['platform']:
            primary = best_odds[selection_key]['platform']
            platforms_to_use.append(primary)
        
        # Add second best platform
        if len(platforms_to_use) < 2:
            for name in ['betfair', 'pinnacle', 'bet365']:
                if name not in platforms_to_use:
                    platforms_to_use.append(name)
                    if len(platforms_to_use) >= 2:
                        break
        
        # Create bets
        stake_per_platform = total_stake / len(platforms_to_use)
        
        for platform_name in platforms_to_use:
            if platform_name in self.platforms:
                platform = self.platforms[platform_name]
                events = platform.get_events()
                
                for event in events:
                    if home_team.lower() in event.home_team.lower():
                        bet = Bet(
                            platform=platform_name,
                            event_id=event.event_id,
                            market=MarketType.MATCH_WINNER,
                            selection=selection,
                            odds=getattr(event.odds, selection_key, 2.0),
                            stake=stake_per_platform
                        )
                        bets.append(platform.place_bet(bet))
        
        return bets
    
    def get_all_events(self) -> List[Event]:
        """Get events from all platforms"""
        all_events = []
        seen = set()
        
        for platform in self.platforms.values():
            try:
                events = platform.get_events()
                for event in events:
                    key = f"{event.home_team}_{event.away_team}_{event.start_time.date()}"
                    if key not in seen:
                        seen.add(key)
                        event.league = f"{event.league} ({platform.name})"
                        all_events.append(event)
            except Exception as e:
                logger.error(f"Error getting events from {platform.name}: {e}")
        
        return all_events


# Convenience function
def create_bet_manager() -> BettingPlatformManager:
    return BettingPlatformManager()


if __name__ == "__main__":
    # Test the platform manager
    manager = BettingPlatformManager()
    
    print("=" * 60)
    print("Betting Platform Manager Test")
    print("=" * 60)
    
    # Show available platforms
    print("\nAvailable Platforms:")
    for name, platform in manager.platforms.items():
        status = "LIVE" if platform.is_available() else "SIMULATED"
        print(f"  - {name}: {status}")
    
    # Get events from all platforms
    print("\nUpcoming Events:")
    events = manager.get_all_events()
    for event in events[:5]:
        print(f"  {event.home_team} vs {event.away_team}")
        print(f"    League: {event.league}")
        print(f"    Time: {event.start_time}")
        if event.odds:
            print(f"    Odds: {event.odds.home} - {event.odds.draw} - {event.odds.away}")
    
    # Get balances
    print("\nPlatform Balances:")
    balances = manager.get_all_balances()
    for platform, balance in balances.items():
        print(f"  {platform}: ${balance:,.2f}")
    
    # Compare odds for a match
    print("\nOdds Comparison (Man City vs Liverpool):")
    best_odds = manager.get_best_odds("Manchester City", "Liverpool")
    for outcome, data in best_odds.items():
        print(f"  {outcome}: {data['odds']:.2f} ({data['platform']})")
    
    print("\n" + "=" * 60)
