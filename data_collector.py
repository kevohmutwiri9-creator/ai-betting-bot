"""
Football Data Collector Module
Handles fetching and processing football match data from various sources
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import time
import json
import os
from dotenv import load_dotenv

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import (
    FOOTBALL_DATA_API_KEY, API_FOOTBALL_KEY, SPORTMONKS_TOKEN,
    ENABLE_FOOTBALL_DATA_API, ENABLE_API_FOOTBALL, ENABLE_SPORTMONKS,
    MATCHES_UPDATE_INTERVAL, ODDS_UPDATE_INTERVAL, LIVE_SCORES_UPDATE_INTERVAL
)

# Configure basic logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class FootballDataCollector:
    def __init__(self, db_path="betting_data.db"):
        self.db_path = db_path
        self.api_keys = {
            'football_data': FOOTBALL_DATA_API_KEY,
            'api_football': API_FOOTBALL_KEY,
            'sportmonks': SPORTMONKS_TOKEN
        }
        self.base_urls = {
            'football_data': 'https://api.football-data.org/v4',
            'api_football': 'https://v1.football.api-sports.io',
            'sportmonks': 'https://api.sportmonks.com/v3/football'
        }
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        self.init_database()
    
    def fetch_from_football_data_api(self, endpoint, params=None):
        """Fetch data from football-data.org API"""
        if not self.api_keys['football_data']:
            logger.warning("Football Data API key not configured")
            return None
        
        url = f"{self.base_urls['football_data']}/{endpoint}"
        headers = {'X-Auth-Token': self.api_keys['football_data']}
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Football Data API error: {e}")
            return None
    
    def fetch_from_api_football(self, endpoint, params=None):
        """Fetch data from API-Football"""
        if not self.api_keys['api_football']:
            logger.warning("API-Football key not configured")
            return None
        
        url = f"{self.base_urls['api_football']}/{endpoint}"
        headers = {'x-apisports-key': self.api_keys['api_football']}
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API-Football error: {e}")
            return None
    
    def get_live_matches(self):
        """Get currently live matches from API"""
        # Try football-data.org first if enabled
        if ENABLE_FOOTBALL_DATA_API:
            data = self.fetch_from_football_data_api('matches?status=LIVE')
            if data and 'matches' in data:
                return self._parse_football_data_matches(data['matches'])
        
        # Fallback to API-Football if enabled
        if ENABLE_API_FOOTBALL:
            data = self.fetch_from_api_football('fixtures?status=LIVE')
            if data and 'response' in data:
                return self._parse_api_football_matches(data['response'])
        
        return []
    
    def get_upcoming_matches(self, days_ahead=7):
        """Get upcoming matches for the next N days"""
        today = datetime.now()
        matches = []
        
        for i in range(days_ahead):
            date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # Try football-data.org if enabled
            if ENABLE_FOOTBALL_DATA_API:
                data = self.fetch_from_football_data_api(f'matches?date={date}')
                if data and 'matches' in data:
                    parsed = self._parse_football_data_matches(data['matches'])
                    matches.extend(parsed)
                    
                # Rate limiting
                time.sleep(0.5)
            
            # Try API-Football if enabled
            if ENABLE_API_FOOTBALL:
                data = self.fetch_from_api_football(f'fixtures?date={date}')
                if data and 'response' in data:
                    parsed = self._parse_api_football_matches(data['response'])
                    matches.extend(parsed)
                
                # Rate limiting
                time.sleep(0.5)
        
        return matches
    
    def get_match_odds(self, match_id):
        """Get odds for a specific match from multiple bookmakers"""
        data = self.fetch_from_football_data_api(f'matches/{match_id}/odds')
        if data and 'odds' in data:
            return self._parse_odds(data['odds'])
        return []
    
    def get_team_stats(self, team_id):
        """Get team statistics from API"""
        data = self.fetch_from_football_data_api(f'teams/{team_id}')
        if data:
            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'country': data.get('country'),
                'founded': data.get('founded'),
                'venue': data.get('venue', {}).get('name') if data.get('venue') else None
            }
        return None
    
    def _parse_football_data_matches(self, matches_data):
        """Parse matches from football-data.org format"""
        matches = []
        for match in matches_data:
            matches.append({
                'match_id': str(match.get('id')),
                'home_team': match.get('homeTeam', {}).get('name', 'Unknown'),
                'away_team': match.get('awayTeam', {}).get('name', 'Unknown'),
                'league': match.get('competition', {}).get('name', 'Unknown'),
                'date': match.get('utcDate', '')[:10],
                'status': match.get('status', 'UNKNOWN'),
                'home_goals': match.get('score', {}).get('fullTime', {}).get('home'),
                'away_goals': match.get('score', {}).get('fullTime', {}).get('away'),
                'home_odds': None,
                'draw_odds': None,
                'away_odds': None
            })
        return matches
    
    def _parse_api_football_matches(self, matches_data):
        """Parse matches from API-Football format"""
        matches = []
        for match in matches_data:
            fixture = match.get('fixture', {})
            teams = match.get('teams', {})
            goals = match.get('goals', {})
            league = match.get('league', {})
            
            matches.append({
                'match_id': str(fixture.get('id')),
                'home_team': teams.get('home', {}).get('name', 'Unknown'),
                'away_team': teams.get('away', {}).get('name', 'Unknown'),
                'league': league.get('name', 'Unknown'),
                'date': fixture.get('date', '')[:10],
                'status': fixture.get('status', {}).get('short', 'UNKNOWN'),
                'home_goals': goals.get('home'),
                'away_goals': goals.get('away'),
                'home_odds': None,
                'draw_odds': None,
                'away_odds': None
            })
        return matches
    
    def _parse_odds(self, odds_data):
        """Parse odds from API response"""
        parsed = []
        for bookmaker in odds_data:
            for bet in bookmaker.get('bets', []):
                if bet.get('name') == 'Match Winner':
                    for value in bet.get('values', []):
                        parsed.append({
                            'bookmaker': bookmaker.get('name'),
                            'outcome': value.get('outcome'),
                            'odds': float(value.get('odd'))
                        })
        return parsed
    
    def init_database(self):
        """Initialize SQLite database for storing match data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT UNIQUE,
                home_team TEXT,
                away_team TEXT,
                league TEXT,
                date TEXT,
                home_goals INTEGER,
                away_goals INTEGER,
                home_odds REAL,
                draw_odds REAL,
                away_odds REAL,
                created_at TEXT
            )
        ''')
        
        # Add indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_match_id ON matches(match_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_league ON matches(league)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON matches(date)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT,
                league TEXT,
                matches_played INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                goals_scored INTEGER,
                goals_conceded INTEGER,
                form TEXT,
                updated_at TEXT
            )
        ''')
        
        # Add indexes for team stats
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_team ON team_stats(team)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_league ON team_stats(team, league)')
        
        conn.commit()
        conn.close()
    
    def get_league_matches(self, league_id):
        """Get matches for a specific league"""
        # Sample data for different leagues
        league_matches = {
            'premier_league': [
                {
                    'match_id': 'pl_001',
                    'home_team': 'Manchester United',
                    'away_team': 'Liverpool',
                    'league': 'Premier League',
                    'date': '2024-02-03',
                    'home_odds': 2.40,
                    'draw_odds': 3.20,
                    'away_odds': 2.80
                },
                {
                    'match_id': 'pl_002',
                    'home_team': 'Arsenal',
                    'away_team': 'Chelsea',
                    'league': 'Premier League',
                    'date': '2024-02-03',
                    'home_odds': 1.90,
                    'draw_odds': 3.60,
                    'away_odds': 4.00
                },
                {
                    'match_id': 'pl_003',
                    'home_team': 'Manchester City',
                    'away_team': 'Tottenham',
                    'league': 'Premier League',
                    'date': '2024-02-04',
                    'home_odds': 1.35,
                    'draw_odds': 5.00,
                    'away_odds': 8.50
                },
                {
                    'match_id': 'pl_004',
                    'home_team': 'Newcastle',
                    'away_team': 'Brighton',
                    'league': 'Premier League',
                    'date': '2024-02-04',
                    'home_odds': 1.75,
                    'draw_odds': 3.80,
                    'away_odds': 4.20
                },
                {
                    'match_id': 'pl_005',
                    'home_team': 'West Ham',
                    'away_team': 'Aston Villa',
                    'league': 'Premier League',
                    'date': '2024-02-04',
                    'home_odds': 2.05,
                    'draw_odds': 3.40,
                    'away_odds': 3.60
                }
            ],
            'la_liga': [
                {
                    'match_id': 'll_001',
                    'home_team': 'Barcelona',
                    'away_team': 'Real Madrid',
                    'league': 'La Liga',
                    'date': '2024-02-03',
                    'home_odds': 2.10,
                    'draw_odds': 3.40,
                    'away_odds': 3.00
                },
                {
                    'match_id': 'll_002',
                    'home_team': 'Atletico Madrid',
                    'away_team': 'Sevilla',
                    'league': 'La Liga',
                    'date': '2024-02-04',
                    'home_odds': 1.75,
                    'draw_odds': 3.80,
                    'away_odds': 4.20
                },
                {
                    'match_id': 'll_003',
                    'home_team': 'Real Betis',
                    'away_team': 'Valencia',
                    'league': 'La Liga',
                    'date': '2024-02-04',
                    'home_odds': 2.25,
                    'draw_odds': 3.30,
                    'away_odds': 2.90
                }
            ],
            'serie_a': [
                {
                    'match_id': 'sa_001',
                    'home_team': 'Juventus',
                    'away_team': 'AC Milan',
                    'league': 'Serie A',
                    'date': '2024-02-03',
                    'home_odds': 1.85,
                    'draw_odds': 3.40,
                    'away_odds': 4.10
                },
                {
                    'match_id': 'sa_002',
                    'home_team': 'Inter Milan',
                    'away_team': 'Napoli',
                    'league': 'Serie A',
                    'date': '2024-02-04',
                    'home_odds': 1.55,
                    'draw_odds': 4.20,
                    'away_odds': 5.50
                },
                {
                    'match_id': 'sa_003',
                    'home_team': 'AS Roma',
                    'away_team': 'Lazio',
                    'league': 'Serie A',
                    'date': '2024-02-04',
                    'home_odds': 2.15,
                    'draw_odds': 3.25,
                    'away_odds': 3.40
                }
            ],
            'bundesliga': [
                {
                    'match_id': 'bl_001',
                    'home_team': 'Bayern Munich',
                    'away_team': 'Borussia Dortmund',
                    'league': 'Bundesliga',
                    'date': '2024-02-03',
                    'home_odds': 1.40,
                    'draw_odds': 5.20,
                    'away_odds': 7.00
                },
                {
                    'match_id': 'bl_002',
                    'home_team': 'RB Leipzig',
                    'away_team': 'Bayer Leverkusen',
                    'league': 'Bundesliga',
                    'date': '2024-02-04',
                    'home_odds': 2.05,
                    'draw_odds': 3.60,
                    'away_odds': 3.40
                },
                {
                    'match_id': 'bl_003',
                    'home_team': 'Borussia Mönchengladbach',
                    'away_team': 'Eintracht Frankfurt',
                    'league': 'Bundesliga',
                    'date': '2024-02-04',
                    'home_odds': 1.95,
                    'draw_odds': 3.70,
                    'away_odds': 3.80
                }
            ],
            'ligue_1': [
                {
                    'match_id': 'l1_001',
                    'home_team': 'PSG',
                    'away_team': 'Marseille',
                    'league': 'Ligue 1',
                    'date': '2024-02-03',
                    'home_odds': 1.30,
                    'draw_odds': 5.50,
                    'away_odds': 9.00
                },
                {
                    'match_id': 'l1_002',
                    'home_team': 'Lyon',
                    'away_team': 'Monaco',
                    'league': 'Ligue 1',
                    'date': '2024-02-04',
                    'home_odds': 2.20,
                    'draw_odds': 3.40,
                    'away_odds': 3.00
                }
            ],
            'champions_league': [
                {
                    'match_id': 'cl_001',
                    'home_team': 'Manchester City',
                    'away_team': 'Real Madrid',
                    'league': 'Champions League',
                    'date': '2024-02-06',
                    'home_odds': 1.65,
                    'draw_odds': 4.20,
                    'away_odds': 4.80
                },
                {
                    'match_id': 'cl_002',
                    'home_team': 'Bayern Munich',
                    'away_team': 'Arsenal',
                    'league': 'Champions League',
                    'date': '2024-02-07',
                    'home_odds': 1.45,
                    'draw_odds': 4.80,
                    'away_odds': 6.00
                }
            ],
            'europa_league': [
                {
                    'match_id': 'el_001',
                    'home_team': 'Liverpool',
                    'away_team': 'AC Milan',
                    'league': 'Europa League',
                    'date': '2024-02-08',
                    'home_odds': 1.55,
                    'draw_odds': 4.20,
                    'away_odds': 5.50
                },
                {
                    'match_id': 'el_002',
                    'home_team': 'Roma',
                    'away_team': 'Ajax',
                    'league': 'Europa League',
                    'date': '2024-02-08',
                    'home_odds': 1.75,
                    'draw_odds': 3.80,
                    'away_odds': 4.20
                }
            ],
            'eredivisie': [
                {
                    'match_id': 'er_001',
                    'home_team': 'Ajax',
                    'away_team': 'PSV',
                    'league': 'Eredivisie',
                    'date': '2024-02-03',
                    'home_odds': 1.85,
                    'draw_odds': 3.60,
                    'away_odds': 4.00
                },
                {
                    'match_id': 'er_002',
                    'home_team': 'Feyenoord',
                    'away_team': 'Utrecht',
                    'league': 'Eredivisie',
                    'date': '2024-02-04',
                    'home_odds': 1.40,
                    'draw_odds': 4.80,
                    'away_odds': 7.00
                }
            ],
            # GAMBLING GAMES
            'casino_games': [
                {
                    'match_id': 'cg_001',
                    'home_team': 'Blackjack',
                    'away_team': 'Dealer',
                    'league': 'Casino Games',
                    'date': '2024-02-03',
                    'home_odds': 1.95,
                    'draw_odds': 0.0,
                    'away_odds': 2.05
                },
                {
                    'match_id': 'cg_002',
                    'home_team': 'Roulette',
                    'away_team': 'House',
                    'league': 'Casino Games',
                    'date': '2024-02-03',
                    'home_odds': 2.37,
                    'draw_odds': 0.0,
                    'away_odds': 2.37
                },
                {
                    'match_id': 'cg_003',
                    'home_team': 'Poker',
                    'away_team': 'Players',
                    'league': 'Casino Games',
                    'date': '2024-02-04',
                    'home_odds': 1.90,
                    'draw_odds': 0.0,
                    'away_odds': 2.10
                },
                {
                    'match_id': 'cg_004',
                    'home_team': 'Baccarat',
                    'away_team': 'Banker',
                    'league': 'Casino Games',
                    'date': '2024-02-04',
                    'home_odds': 1.95,
                    'draw_odds': 8.50,
                    'away_odds': 0.90
                },
                {
                    'match_id': 'cg_005',
                    'home_team': 'Craps',
                    'away_team': 'Shooter',
                    'league': 'Casino Games',
                    'date': '2024-02-04',
                    'home_odds': 1.80,
                    'draw_odds': 0.0,
                    'away_odds': 2.20
                }
            ],
            'slot_games': [
                {
                    'match_id': 'sg_001',
                    'home_team': 'Mega Moolah',
                    'away_team': 'Jackpot',
                    'league': 'Slot Games',
                    'date': '2024-02-03',
                    'home_odds': 100.00,
                    'draw_odds': 0.0,
                    'away_odds': 0.01
                },
                {
                    'match_id': 'sg_002',
                    'home_team': 'Starburst',
                    'away_team': 'Payout',
                    'league': 'Slot Games',
                    'date': '2024-02-03',
                    'home_odds': 50.00,
                    'draw_odds': 0.0,
                    'away_odds': 0.02
                },
                {
                    'match_id': 'sg_003',
                    'home_team': 'Gonzo\'s Quest',
                    'away_team': 'Treasure',
                    'league': 'Slot Games',
                    'date': '2024-02-04',
                    'home_odds': 75.00,
                    'draw_odds': 0.0,
                    'away_odds': 0.013
                },
                {
                    'match_id': 'sg_004',
                    'home_team': 'Book of Ra',
                    'away_team': 'Riches',
                    'league': 'Slot Games',
                    'date': '2024-02-04',
                    'home_odds': 60.00,
                    'draw_odds': 0.0,
                    'away_odds': 0.017
                }
            ],
            'poker_games': [
                {
                    'match_id': 'pg_001',
                    'home_team': 'Texas Hold\'em',
                    'away_team': 'Players',
                    'league': 'Poker Games',
                    'date': '2024-02-03',
                    'home_odds': 2.10,
                    'draw_odds': 0.0,
                    'away_odds': 1.90
                },
                {
                    'match_id': 'pg_002',
                    'home_team': 'Omaha',
                    'away_team': 'Pot',
                    'league': 'Poker Games',
                    'date': '2024-02-03',
                    'home_odds': 2.00,
                    'draw_odds': 0.0,
                    'away_odds': 2.00
                },
                {
                    'match_id': 'pg_003',
                    'home_team': 'Seven Card Stud',
                    'away_team': 'Deck',
                    'league': 'Poker Games',
                    'date': '2024-02-04',
                    'home_odds': 1.95,
                    'draw_odds': 0.0,
                    'away_odds': 2.05
                }
            ],
            'virtual_sports': [
                {
                    'match_id': 'vs_001',
                    'home_team': 'Virtual Football',
                    'away_team': 'Team A',
                    'league': 'Virtual Sports',
                    'date': '2024-02-03',
                    'home_odds': 2.10,
                    'draw_odds': 3.20,
                    'away_odds': 3.00
                },
                {
                    'match_id': 'vs_002',
                    'home_team': 'Virtual Horse Racing',
                    'away_team': 'Horse 1',
                    'league': 'Virtual Sports',
                    'date': '2024-02-03',
                    'home_odds': 3.50,
                    'draw_odds': 0.0,
                    'away_odds': 2.80
                },
                {
                    'match_id': 'vs_003',
                    'home_team': 'Virtual Greyhounds',
                    'away_team': 'Dog 3',
                    'league': 'Virtual Sports',
                    'date': '2024-02-04',
                    'home_odds': 4.20,
                    'draw_odds': 0.0,
                    'away_odds': 2.10
                }
            ],
            'esports': [
                {
                    'match_id': 'es_001',
                    'home_team': 'Team Liquid',
                    'away_team': 'Cloud9',
                    'league': 'Esports - CS:GO',
                    'date': '2024-02-03',
                    'home_odds': 1.75,
                    'draw_odds': 0.0,
                    'away_odds': 2.15
                },
                {
                    'match_id': 'es_002',
                    'home_team': 'T1',
                    'away_team': 'Gen.G',
                    'league': 'Esports - League of Legends',
                    'date': '2024-02-03',
                    'home_odds': 1.45,
                    'draw_odds': 0.0,
                    'away_odds': 2.80
                },
                {
                    'match_id': 'es_003',
                    'home_team': 'FaZe Clan',
                    'away_team': 'NaVi',
                    'league': 'Esports - CS:GO',
                    'date': '2024-02-04',
                    'home_odds': 1.85,
                    'draw_odds': 0.0,
                    'away_odds': 1.95
                },
                {
                    'match_id': 'es_004',
                    'home_team': 'G2 Esports',
                    'away_team': 'Fnatic',
                    'league': 'Esports - League of Legends',
                    'date': '2024-02-04',
                    'home_odds': 1.60,
                    'draw_odds': 0.0,
                    'away_odds': 2.30
                }
            ]
        }
        
        # Return matches for the requested league, or default sample data
        matches = league_matches.get(league_id, self.get_sample_data().to_dict('records'))
        return pd.DataFrame(matches)
    
    def get_sample_data(self):
        """Get comprehensive football data with date filtering"""
        print("🔍 Starting comprehensive data collection...")
        
        # Try API-Football first for live and today's games
        try:
            import requests
            from datetime import datetime, timedelta
            
            api_football_key = os.getenv('API_FOOTBALL_KEY', '')
            print(f"🔑 API-Football key found: {len(api_football_key)} characters")
            
            if api_football_key and len(api_football_key) > 10:
                all_matches = []
                
                # 1. Get LIVE matches first
                print("🌐 Getting LIVE matches...")
                url_live = "https://v3.football.api-sports.io/fixtures?live=all"
                headers = {"x-apisports-key": api_football_key}
                
                response = requests.get(url_live, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for fixture in data.get('response', []):
                        fixture_time = fixture.get('fixture', {}).get('date', '')
                        match_date = fixture_time.split('T')[0] if 'T' in fixture_time else fixture_time
                        
                        match = {
                            'match_id': f"live_{fixture.get('fixture', {}).get('id')}",
                            'home_team': fixture.get('teams', {}).get('home', {}).get('name', ''),
                            'away_team': fixture.get('teams', {}).get('away', {}).get('name', ''),
                            'league': fixture.get('league', {}).get('name', ''),
                            'date': match_date,
                            'home_odds': 2.10,
                            'draw_odds': 3.40,
                            'away_odds': 3.20,
                            'status': 'LIVE',
                            'fixture_time': fixture_time
                        }
                        if match['home_team'] and match['away_team']:
                            all_matches.append(match)
                            print(f"⚽ LIVE: {match['home_team']} vs {match['away_team']}")
                
                # 2. Get TODAY's matches
                print("📅 Getting TODAY's matches...")
                today = datetime.now().strftime('%Y-%m-%d')
                url_today = f"https://v3.football.api-sports.io/fixtures?date={today}"
                
                response = requests.get(url_today, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for fixture in data.get('response', []):
                        fixture_time = fixture.get('fixture', {}).get('date', '')
                        match_date = fixture_time.split('T')[0] if 'T' in fixture_time else fixture_time
                        
                        match = {
                            'match_id': f"today_{fixture.get('fixture', {}).get('id')}",
                            'home_team': fixture.get('teams', {}).get('home', {}).get('name', ''),
                            'away_team': fixture.get('teams', {}).get('away', {}).get('name', ''),
                            'league': fixture.get('league', {}).get('name', ''),
                            'date': match_date,
                            'home_odds': 2.10,
                            'draw_odds': 3.40,
                            'away_odds': 3.20,
                            'status': 'TODAY',
                            'fixture_time': fixture_time
                        }
                        if match['home_team'] and match['away_team']:
                            all_matches.append(match)
                            print(f"📅 TODAY: {match['home_team']} vs {match['away_team']}")
                
                # 3. Get TOMORROW's matches
                print("📆 Getting TOMORROW's matches...")
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                url_tomorrow = f"https://v3.football.api-sports.io/fixtures?date={tomorrow}"
                
                response = requests.get(url_tomorrow, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for fixture in data.get('response', []):
                        fixture_time = fixture.get('fixture', {}).get('date', '')
                        match_date = fixture_time.split('T')[0] if 'T' in fixture_time else fixture_time
                        
                        match = {
                            'match_id': f"tomorrow_{fixture.get('fixture', {}).get('id')}",
                            'home_team': fixture.get('teams', {}).get('home', {}).get('name', ''),
                            'away_team': fixture.get('teams', {}).get('away', {}).get('name', ''),
                            'league': fixture.get('league', {}).get('name', ''),
                            'date': match_date,
                            'home_odds': 2.10,
                            'draw_odds': 3.40,
                            'away_odds': 3.20,
                            'status': 'TOMORROW',
                            'fixture_time': fixture_time
                        }
                        if match['home_team'] and match['away_team']:
                            all_matches.append(match)
                            print(f"📆 TOMORROW: {match['home_team']} vs {match['away_team']}")
                
                # 4. Get YESTERDAY's matches (for completed games)
                print("📅 Getting YESTERDAY's matches...")
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                url_yesterday = f"https://v3.football.api-sports.io/fixtures?date={yesterday}"
                
                response = requests.get(url_yesterday, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for fixture in data.get('response', []):
                        fixture_time = fixture.get('fixture', {}).get('date', '')
                        match_date = fixture_time.split('T')[0] if 'T' in fixture_time else fixture_time
                        
                        match = {
                            'match_id': f"yesterday_{fixture.get('fixture', {}).get('id')}",
                            'home_team': fixture.get('teams', {}).get('home', {}).get('name', ''),
                            'away_team': fixture.get('teams', {}).get('away', {}).get('name', ''),
                            'league': fixture.get('league', {}).get('name', ''),
                            'date': match_date,
                            'home_odds': 2.10,
                            'draw_odds': 3.40,
                            'away_odds': 3.20,
                            'status': 'COMPLETED',
                            'fixture_time': fixture_time
                        }
                        if match['home_team'] and match['away_team']:
                            all_matches.append(match)
                            print(f"✅ YESTERDAY: {match['home_team']} vs {match['away_team']}")
                
                if all_matches:
                    print(f"✅ SUCCESS: Got {len(all_matches)} total matches (LIVE + Today + Tomorrow + Yesterday)")
                    return pd.DataFrame(all_matches)
                else:
                    print("⚠️ No matches from API-Football")
                
        except Exception as e:
            print(f"❌ API-Football failed: {e}")
        
        # Try Football-Data API as backup
        try:
            import requests
            from datetime import datetime
            
            football_data_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
            print(f"🔑 Football-Data key found: {len(football_data_key)} characters")
            
            if football_data_key and len(football_data_key) > 10:
                print("🌐 Trying Football-Data API...")
                url = "https://api.football-data.org/v4/matches"
                headers = {"X-Auth-Token": football_data_key}
                
                response = requests.get(url, headers=headers, timeout=10)
                print(f"📡 Football-Data response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    real_matches = []
                    
                    for match in data.get('matches', []):
                        real_match = {
                            'match_id': f"fd_{match.get('id')}",
                            'home_team': match.get('homeTeam', {}).get('name', ''),
                            'away_team': match.get('awayTeam', {}).get('name', ''),
                            'league': match.get('competition', {}).get('name', ''),
                            'date': match.get('utcDate', '').split('T')[0],
                            'home_odds': 2.15,
                            'draw_odds': 3.30,
                            'away_odds': 3.10,
                            'status': 'SCHEDULED'
                        }
                        if real_match['home_team'] and real_match['away_team']:
                            real_matches.append(real_match)
                    
                    if real_matches:
                        print(f"✅ SUCCESS: Got {len(real_matches)} matches from Football-Data API")
                        return pd.DataFrame(real_matches)
            else:
                print("❌ Football-Data key missing or too short")
                
        except Exception as e:
            print(f"❌ Football-Data API failed: {e}")
        
        # If APIs fail, return empty DataFrame
        print("❌ FAILURE: All APIs failed - no real data available")
        return pd.DataFrame()
    
    def calculate_team_features(self, match_data):
        """Calculate features for AI model based on team statistics"""
        features = []
        
        for _, match in match_data.iterrows():
            # Sample feature calculation - in real app, use historical data
            home_form = self.get_team_form(match['home_team'])
            away_form = self.get_team_form(match['away_team'])
            
            feature = {
                'home_team_strength': home_form,
                'away_team_strength': away_form,
                'home_advantage': 1.0,  # Home field advantage
                'odds_ratio': match['home_odds'] / match['away_odds'],
                'league_competitiveness': self.get_league_rating(match['league'])
            }
            features.append(feature)
        
        return pd.DataFrame(features)
    
    def get_team_form(self, team_name):
        """Get recent team form (simplified)"""
        # In real implementation, query database for last 5 matches
        import random
        return random.uniform(0.3, 0.8)  # Sample form rating
    
    def get_league_rating(self, league):
        """Get league competitiveness rating"""
        league_ratings = {
            'Premier League': 0.9,
            'La Liga': 0.85,
            'Serie A': 0.8,
            'Bundesliga': 0.75
        }
        return league_ratings.get(league, 0.7)
    
    def save_match_data(self, match_data):
        """Save match data to database"""
        conn = sqlite3.connect(self.db_path)
        match_data.to_sql('matches', conn, if_exists='append', index=False)
        conn.close()
    
    def get_historical_data(self, limit=1000):
        """Retrieve historical match data for training"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM matches ORDER BY date DESC LIMIT ?"
        data = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return data
    
    def get_matches_by_date(self, date_filter='all'):
        """Get matches filtered by date: live, today, tomorrow, yesterday, or all"""
        from datetime import datetime, timedelta
        
        # Rate limiting - wait between API calls
        time.sleep(1.1)  # Respect free tier limits (10 req/min)
        
        # Try to get real data first
        real_matches = []
        
        if date_filter == 'live':
            real_matches = self.get_live_matches()
        elif date_filter == 'today':
            today = datetime.now().strftime('%Y-%m-%d')
            if ENABLE_FOOTBALL_DATA_API:
                data = self.fetch_from_football_data_api(f'matches?date={today}')
                if data and 'matches' in data:
                    real_matches = self._parse_football_data_matches(data['matches'])
            if not real_matches and ENABLE_API_FOOTBALL:
                data = self.fetch_from_api_football(f'fixtures?date={today}')
                if data and 'response' in data:
                    real_matches = self._parse_api_football_matches(data['response'])
        elif date_filter == 'tomorrow':
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            if ENABLE_FOOTBALL_DATA_API:
                data = self.fetch_from_football_data_api(f'matches?date={tomorrow}')
                if data and 'matches' in data:
                    real_matches = self._parse_football_data_matches(data['matches'])
            if not real_matches and ENABLE_API_FOOTBALL:
                data = self.fetch_from_api_football(f'fixtures?date={tomorrow}')
                if data and 'response' in data:
                    real_matches = self._parse_api_football_matches(data['response'])
        
        # If we got real matches, return them
        if real_matches:
            return real_matches
        
        # Fall back to sample data for demo
        all_matches = self.get_sample_data()
        
        if date_filter == 'all':
            return all_matches
        
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        filtered_matches = []
        for match in all_matches:
            match_date = match.get('date', '')
            
            if date_filter == 'live':
                # For demo, show first 3 matches as "live"
                if match in all_matches[:3]:
                    filtered_matches.append({**match, 'status': 'LIVE'})
            elif date_filter == 'today' and match_date == today:
                filtered_matches.append(match)
            elif date_filter == 'tomorrow' and match_date == tomorrow:
                filtered_matches.append(match)
            elif date_filter == 'yesterday' and match_date == yesterday:
                filtered_matches.append(match)
        
        return filtered_matches

if __name__ == "__main__":
    collector = FootballDataCollector()
    
    # Get sample data
    sample_data = collector.get_sample_data()
    print("Sample match data:")
    print(sample_data)
    
    # Calculate features
    features = collector.calculate_team_features(sample_data)
    print("\nCalculated features:")
    print(features)
