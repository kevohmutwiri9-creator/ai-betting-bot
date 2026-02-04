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

load_dotenv()

class FootballDataCollector:
    def __init__(self, db_path="betting_data.db"):
        self.db_path = db_path
        self.init_database()
    
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
        """Generate sample football data for demonstration"""
        # Try to get real data first
        try:
            import requests
            from datetime import datetime
            
            # Try API-Football for real data
            url = "https://v3.football.api-sports.io/fixtures"
            headers = {"x-apisports-key": os.getenv('API_FOOTBALL_KEY', '')}
            
            if headers["x-apisports-key"]:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    real_matches = []
                    
                    for fixture in data.get('response', [])[:10]:  # Limit to 10 matches
                        match = {
                            'match_id': f"real_{fixture.get('fixture', {}).get('id')}",
                            'home_team': fixture.get('teams', {}).get('home', {}).get('name', ''),
                            'away_team': fixture.get('teams', {}).get('away', {}).get('name', ''),
                            'league': fixture.get('league', {}).get('name', ''),
                            'date': fixture.get('fixture', {}).get('date', '').split('T')[0],
                            'home_odds': 2.10,  # Would get from real odds API
                            'draw_odds': 3.40,
                            'away_odds': 3.20
                        }
                        real_matches.append(match)
                    
                    if real_matches:
                        print(f"✅ Got {len(real_matches)} real matches from API")
                        return real_matches
        except Exception as e:
            print(f"❌ Real API failed: {e}")
        
        # Fallback to sample data
        print("📊 Using sample data (no API key or API failed)")
        sample_matches = [
            {
                'match_id': 'man_ars_001',
                'home_team': 'Manchester United',
                'away_team': 'Arsenal',
                'league': 'Premier League',
                'date': '2024-02-03',
                'home_odds': 2.10,
                'draw_odds': 3.40,
                'away_odds': 3.20
            },
            {
                'match_id': 'liv_che_001',
                'home_team': 'Liverpool',
                'away_team': 'Chelsea',
                'league': 'Premier League',
                'date': '2024-02-04',
                'home_odds': 1.85,
                'draw_odds': 3.60,
                'away_odds': 4.10
            },
            {
                'match_id': 'bar_mad_001',
                'home_team': 'Barcelona',
                'away_team': 'Real Madrid',
                'league': 'La Liga',
                'date': '2024-02-05',
                'home_odds': 2.30,
                'draw_odds': 3.20,
                'away_odds': 2.80
            },
            {
                'match_id': 'bay_mun_001',
                'home_team': 'Bayern Munich',
                'away_team': 'Borussia Dortmund',
                'league': 'Bundesliga',
                'date': '2024-02-03',
                'home_odds': 1.75,
                'draw_odds': 3.80,
                'away_odds': 4.20
            },
            {
                'match_id': 'psg_oly_001',
                'home_team': 'PSG',
                'away_team': 'Olympique Lyon',
                'league': 'Ligue 1',
                'date': '2024-02-04',
                'home_odds': 1.65,
                'draw_odds': 3.90,
                'away_odds': 4.80
            },
            {
                'match_id': 'man_cit_001',
                'home_team': 'Manchester City',
                'away_team': 'Tottenham',
                'league': 'Premier League',
                'date': '2024-02-05',
                'home_odds': 1.45,
                'draw_odds': 4.50,
                'away_odds': 6.00
            },
            {
                'match_id': 'real_soc_001',
                'home_team': 'Real Sociedad',
                'away_team': 'Atletico Madrid',
                'league': 'La Liga',
                'date': '2024-02-03',
                'home_odds': 2.60,
                'draw_odds': 3.30,
                'away_odds': 2.50
            },
            {
                'match_id': 'int_mil_001',
                'home_team': 'Inter Milan',
                'away_team': 'AC Milan',
                'league': 'Serie A',
                'date': '2024-02-04',
                'home_odds': 2.05,
                'draw_odds': 3.25,
                'away_odds': 3.40
            },
            {
                'match_id': 'nap_juv_001',
                'home_team': 'Napoli',
                'away_team': 'Juventus',
                'league': 'Serie A',
                'date': '2024-02-05',
                'home_odds': 2.40,
                'draw_odds': 3.10,
                'away_odds': 2.70
            },
            {
                'match_id': 'lei_ave_001',
                'home_team': 'Leicester City',
                'away_team': 'Aston Villa',
                'league': 'Premier League',
                'date': '2024-02-06',
                'home_odds': 2.80,
                'draw_odds': 3.40,
                'away_odds': 2.20
            }
        ]
        
        return pd.DataFrame(sample_matches)
    
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
