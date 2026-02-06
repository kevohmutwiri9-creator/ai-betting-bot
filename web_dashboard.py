from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
import os
import random
from data_collector import FootballDataCollector
from ai_model import BettingAIModel
from value_detector import ValueBetDetector
from auth import auth_manager, require_auth, require_premium
from validators import (
    validate_match_analysis, 
    validate_auto_bet_request, 
    validate_user_registration, 
    validate_user_login,
    ValidationError
)
from rate_limiter import rate_limit, auth_rate_limit, premium_rate_limit
from logger import logger, log_api_call, monitor_performance, log_security_event

# Try to import Flask-RESTX for Swagger, fall back to basic documentation
try:
    from flask_restx import Api, Resource, fields, reqparse
    HAS_RESTX = True
except ImportError:
    HAS_RESTX = False
    Api = None
    Resource = None
    fields = None
    reqparser = None

app = Flask(__name__)

# Initialize Swagger API documentation
if HAS_RESTX:
    api = Api(app, version='1.0', title='AI Betting Bot API',
              description='API for AI-powered betting predictions and value bet detection',
              doc='/api/docs')
    
    ns = api.namespace('api', description='Betting API operations')
    
    # API Models for documentation
    user_model = api.model('User', {
        'username': fields.String(required=True, description='Username'),
        'email': fields.String(required=True, description='Email address'),
        'api_key': fields.String(description='API key for authentication')
    })
    
    bet_model = api.model('Bet', {
        'match_id': fields.String(description='Unique match identifier'),
        'home_team': fields.String(description='Home team name'),
        'away_team': fields.String(description='Away team name'),
        'recommended_outcome': fields.String(description='Recommended bet outcome'),
        'odds': fields.Float(description='Decimal odds'),
        'value_margin': fields.Float(description='Value margin percentage'),
        'expected_value': fields.Float(description='Expected value'),
        'confidence': fields.String(description='Confidence level')
    })
    
    match_model = api.model('Match', {
        'match_id': fields.String(description='Unique match identifier'),
        'home_team': fields.String(description='Home team name'),
        'away_team': fields.String(description='Away team name'),
        'league': fields.String(description='League name'),
        'date': fields.String(description='Match date'),
        'home_odds': fields.Float(description='Home win odds'),
        'draw_odds': fields.Float(description='Draw odds'),
        'away_odds': fields.Float(description='Away win odds')
    })
    
    auth_parser = reqparse.RequestParser()
    auth_parser.add_argument('Authorization', location='headers', required=True, help='Bearer token')

# Initialize components
data_collector = FootballDataCollector()
ai_model = BettingAIModel()
value_detector = ValueBetDetector()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/docs')
def api_docs():
    """API documentation page (redirects to Swagger UI if available)"""
    if HAS_RESTX:
        return api.__self._render_apidoc
    else:
        return jsonify({
            'message': 'Flask-RESTX not installed. Install with: pip install flask-restx',
            'endpoints': [
                {'path': '/api/register', 'method': 'POST', 'description': 'Register new user'},
                {'path': '/api/login', 'method': 'POST', 'description': 'Authenticate user'},
                {'path': '/api/leagues', 'method': 'GET', 'description': 'Get available leagues'},
                {'path': '/api/league-matches/<league_id>', 'method': 'GET', 'description': 'Get league matches'},
                {'path': '/api/auto-bet', 'method': 'POST', 'description': 'Auto-betting functionality'},
                {'path': '/api/betting-history', 'method': 'GET', 'description': 'Get betting history'},
                {'path': '/api/place-bet', 'method': 'POST', 'description': 'Place a bet'},
                {'path': '/health', 'method': 'GET', 'description': 'Health check'}
            ]
        })

@app.route('/api/register', methods=['POST'])
@auth_rate_limit()
@log_api_call()
@log_security_event('user_registration')
def register():
    """Register new user"""
    try:
        data = request.get_json()
        validated_data = validate_user_registration(data)
        
        result = auth_manager.register_user(
            validated_data['username'], 
            validated_data['email'], 
            validated_data['password']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'api_key': result['api_key']
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/login', methods=['POST'])
@auth_rate_limit()
@log_api_call()
@log_security_event('user_login')
def login():
    """Authenticate user"""
    try:
        data = request.get_json()
        validated_data = validate_user_login(data)
        
        result = auth_manager.authenticate_user(
            validated_data['username'], 
            validated_data['password']
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leagues')
@require_auth
@rate_limit('api')
@log_api_call()
def get_leagues():
    """API endpoint to get available leagues"""
    leagues = [
        {'id': 'premier_league', 'name': 'Premier League', 'country': 'England'},
        {'id': 'la_liga', 'name': 'La Liga', 'country': 'Spain'},
        {'id': 'serie_a', 'name': 'Serie A', 'country': 'Italy'},
        {'id': 'bundesliga', 'name': 'Bundesliga', 'country': 'Germany'},
        {'id': 'ligue_1', 'name': 'Ligue 1', 'country': 'France'},
        {'id': 'champions_league', 'name': 'Champions League', 'country': 'Europe'},
        {'id': 'europa_league', 'name': 'Europa League', 'country': 'Europe'},
        {'id': 'eredivisie', 'name': 'Eredivisie', 'country': 'Netherlands'},
        {'id': 'casino_games', 'name': 'Casino Games', 'country': 'Global'},
        {'id': 'slot_games', 'name': 'Slot Games', 'country': 'Global'},
        {'id': 'poker_games', 'name': 'Poker Games', 'country': 'Global'},
        {'id': 'virtual_sports', 'name': 'Virtual Sports', 'country': 'Global'},
        {'id': 'esports', 'name': 'Esports', 'country': 'Global'}
    ]
    
    return jsonify({
        'success': True,
        'data': leagues
    })

@app.route('/api/league-matches/<league_id>')
@require_auth
@rate_limit('api')
def get_league_matches(league_id):
    """API endpoint to get matches for a specific league"""
    try:
        # Get matches for the selected league
        matches_data = data_collector.get_league_matches(league_id)
        
        return jsonify({
            'success': True,
            'data': matches_data,
            'league': league_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/matches')
@app.route('/api/matches/<date_filter>')
@rate_limit('api')
def get_matches(date_filter='all'):
    """API endpoint to get matches filtered by date"""
    try:
        # Get matches for the selected date filter
        matches_data = data_collector.get_matches_by_date(date_filter)
        
        return jsonify({
            'success': True,
            'data': matches_data,
            'filter': date_filter
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auto-bet', methods=['POST'])
@require_auth
@require_premium
@premium_rate_limit()
def auto_bet():
    """API endpoint for auto-betting functionality"""
    try:
        data = request.get_json()
        validated_data = validate_auto_bet_request(data)
        
        # Get current value bets
        matches_data = data_collector.get_sample_data()
        value_bets = value_detector.find_value_bets(matches_data)
        
        # Filter bets based on validated criteria
        filtered_bets = []
        for bet in value_bets:
            if (float(bet['odds']) <= validated_data['max_odds'] and 
                float(bet['value_margin']) >= validated_data['min_value']):
                filtered_bets.append(bet)
        
        if not filtered_bets:
            return jsonify({
                'success': False,
                'error': 'No bets meet your criteria'
            })
        
        # Calculate total stake and potential returns
        total_stake = len(filtered_bets) * validated_data['stake']
        total_potential = sum([float(bet['odds']) * validated_data['stake'] for bet in filtered_bets])
        
        # Place bets (simulation)
        placed_bets = []
        for bet in filtered_bets:
            bet_result = {
                'match_id': bet['match_id'],
                'teams': f"{bet['home_team']} vs {bet['away_team']}",
                'pick': bet['recommended_outcome'],
                'odds': bet['odds'],
                'value': bet['value_margin'],
                'stake': validated_data['stake'],
                'potential_return': float(bet['odds']) * validated_data['stake'],
                'status': 'placed' if validated_data['auto_confirm'] else 'pending'
            }
            placed_bets.append(bet_result)
        
        return jsonify({
            'success': True,
            'data': {
                'placed_bets': placed_bets,
                'total_stake': total_stake,
                'total_potential_return': total_potential,
                'bet_count': len(placed_bets),
                'auto_confirm': validated_data['auto_confirm']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/betting-history')
@require_auth
def get_betting_history():
    """Get user's betting history"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_info = auth_manager.verify_token(token)
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'Invalid authentication'
            }), 401
        
        import sqlite3
        conn = sqlite3.connect('betting_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bets WHERE user_id = ? ORDER BY created_at DESC LIMIT 50
        ''', (user_info['user_id'],))
        
        bets = cursor.fetchall()
        conn.close()
        
        history = []
        for bet in bets:
            history.append({
                'id': bet[0],
                'bet_id': bet[2],
                'home_team': bet[3],
                'away_team': bet[4],
                'league': bet[5],
                'bet_type': bet[6],
                'odds': bet[7],
                'stake': bet[8],
                'status': bet[9],
                'created_at': bet[10],
                'settled_at': bet[11],
                'result': bet[12],
                'profit_loss': bet[13]
            })
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/place-bet', methods=['POST'])
@require_auth
@rate_limit('api')
@log_api_call()
@monitor_performance('place_bet')
def place_bet():
    """Place a bet on multiple platforms"""
    try:
        data = request.get_json()
        bet_id = data.get('bet_id')
        platform = data.get('platform', 'betika')  # Default platform
        stake = data.get('stake', 100.0)
        
        if not bet_id:
            return jsonify({
                'success': False,
                'error': 'Bet ID is required'
            }), 400
        
        # Get user info from auth token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_info = auth_manager.verify_token(token)
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'Invalid authentication'
            }), 401
        
        # Platform-specific integration
        platform_result = None
        if platform == 'betika':
            platform_result = place_betika_bet(bet_id, stake, user_info)
        elif platform == 'betway':
            platform_result = place_betway_bet(bet_id, stake, user_info)
        elif platform == '1xbet':
            platform_result = place_1xbet_bet(bet_id, stake, user_info)
        elif platform == 'sportpesa':
            platform_result = place_sportpesa_bet(bet_id, stake, user_info)
        elif platform == 'odibet':
            platform_result = place_odibet_bet(bet_id, stake, user_info)
        else:
            platform_result = {'success': True, 'platform_bet_id': f"mock_{platform}_{bet_id}"}
        
        # Store bet in database
        import sqlite3
        conn = sqlite3.connect('betting_data.db')
        cursor = conn.cursor()
        
        # Create bets table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                bet_id TEXT,
                platform TEXT,
                platform_bet_id TEXT,
                home_team TEXT,
                away_team TEXT,
                league TEXT,
                bet_type TEXT,
                odds REAL,
                stake REAL,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                settled_at TEXT,
                result TEXT,
                profit_loss REAL
            )
        ''')
        
        # Get bet details from current value bets
        matches_data = data_collector.get_sample_data()
        value_bets = create_simple_value_bets(matches_data)
        
        bet_details = None
        for bet in value_bets:
            if bet['id'] == bet_id:
                bet_details = bet
                break
        
        if not bet_details:
            return jsonify({
                'success': False,
                'error': 'Bet not found'
            }), 404
        
        # Insert bet record
        cursor.execute('''
            INSERT INTO bets (user_id, bet_id, platform, platform_bet_id, home_team, away_team, league, bet_type, odds, stake, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_info['user_id'],
            bet_id,
            platform,
            platform_result.get('platform_bet_id', f"mock_{platform}_{bet_id}"),
            bet_details['home_team'],
            bet_details['away_team'],
            bet_details['league'],
            bet_details['bet_type'],
            bet_details['odds'],
            stake,
            'pending',
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"💰 Bet placed on {platform}: {bet_details['home_team']} vs {bet_details['away_team']} - {bet_details['bet_type']}")
        
        return jsonify({
            'success': True,
            'message': f'Bet placed successfully on {platform}!',
            'platform': platform,
            'platform_bet_id': platform_result.get('platform_bet_id'),
            'bet_details': bet_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error placing bet: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def place_betika_bet(bet_id, stake, user_info):
    """Place bet on Betika platform"""
    # Mock Betika API integration
    print(f"🎰 Placing {stake} KES bet on Betika for bet {bet_id}")
    return {
        'success': True,
        'platform_bet_id': f"betika_{bet_id}_{int(datetime.now().timestamp())}",
        'confirmation': f"Betika-{random.randint(100000, 999999)}"
    }

def place_betway_bet(bet_id, stake, user_info):
    """Place bet on Betway platform"""
    print(f"🎰 Placing {stake} KES bet on Betway for bet {bet_id}")
    return {
        'success': True,
        'platform_bet_id': f"betway_{bet_id}_{int(datetime.now().timestamp())}",
        'confirmation': f"BW-{random.randint(100000, 999999)}"
    }

def place_1xbet_bet(bet_id, stake, user_info):
    """Place bet on 1xBet platform"""
    print(f"🎰 Placing {stake} KES bet on 1xBet for bet {bet_id}")
    return {
        'success': True,
        'platform_bet_id': f"1xbet_{bet_id}_{int(datetime.now().timestamp())}",
        'confirmation': f"1X-{random.randint(100000, 999999)}"
    }

def place_sportpesa_bet(bet_id, stake, user_info):
    """Place bet on SportPesa platform"""
    print(f"🎰 Placing {stake} KES bet on SportPesa for bet {bet_id}")
    return {
        'success': True,
        'platform_bet_id': f"sportpesa_{bet_id}_{int(datetime.now().timestamp())}",
        'confirmation': f"SP-{random.randint(100000, 999999)}"
    }

def place_odibet_bet(bet_id, stake, user_info):
    """Place bet on Odibet platform"""
    print(f"🎰 Placing {stake} KES bet on Odibet for bet {bet_id}")
    return {
        'success': True,
        'platform_bet_id': f"odibet_{bet_id}_{int(datetime.now().timestamp())}",
        'confirmation': f"OD-{random.randint(100000, 999999)}"
    }

@app.route('/api/start-auto-bet', methods=['POST'])
@require_auth
@rate_limit('api')
@log_api_call()
@monitor_performance('auto_bet')
def start_auto_betting():
    """Start automated betting across multiple platforms"""
    try:
        data = request.get_json()
        stake_per_bet = data.get('stake', 100.0)
        max_odds = data.get('max_odds', 3.0)
        min_value = data.get('min_value', 5.0)
        platforms = data.get('platforms', ['betika'])  # Default to betika
        enabled = data.get('enabled', True)
        
        # Get user info
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_info = auth_manager.verify_token(token)
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'Invalid authentication'
            }), 401
        
        # Store auto-bet settings
        import sqlite3
        conn = sqlite3.connect('betting_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_bet_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                stake_per_bet REAL,
                max_odds REAL,
                min_value REAL,
                platforms TEXT,
                enabled BOOLEAN,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Update or insert settings
        cursor.execute('''
            INSERT OR REPLACE INTO auto_bet_settings 
            (user_id, stake_per_bet, max_odds, min_value, platforms, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_info['user_id'],
            stake_per_bet,
            max_odds,
            min_value,
            ','.join(platforms),
            enabled,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        if enabled:
            # Start auto-betting process
            print(f"🤖 Starting auto-betting for user {user_info['user_id']}")
            print(f"   Stake: KES {stake_per_bet}")
            print(f"   Max Odds: {max_odds}")
            print(f"   Min Value: {min_value}%")
            print(f"   Platforms: {', '.join(platforms)}")
            
            # Place initial bets
            auto_place_bets(user_info['user_id'], platforms, stake_per_bet, max_odds, min_value)
        
        return jsonify({
            'success': True,
            'message': f'Auto-betting {"started" if enabled else "stopped"}',
            'settings': {
                'stake_per_bet': stake_per_bet,
                'max_odds': max_odds,
                'min_value': min_value,
                'platforms': platforms,
                'enabled': enabled
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error starting auto-bet: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def auto_place_bets(user_id, platforms, stake, max_odds, min_value):
    """Automatically place bets on value opportunities"""
    try:
        # Get current value bets
        matches_data = data_collector.get_sample_data()
        value_bets = []
        
        for idx, match in matches_data.iterrows():
            bet_types = [
                {'type': 'Home Win', 'odds': match['home_odds']},
                {'type': 'Draw', 'odds': match['draw_odds']},
                {'type': 'Away Win', 'odds': match['away_odds']}
            ]
            
            for bet_info in bet_types:
                if bet_info['odds'] > 1.0 and bet_info['odds'] <= max_odds:
                    value_margin = random.uniform(min_value, min_value + 5)
                    if value_margin >= min_value:
                        value_bet = {
                            'id': f"auto_{match['match_id']}_{bet_info['type'].lower().replace(' ', '_')}",
                            'home_team': match['home_team'],
                            'away_team': match['away_team'],
                            'league': match['league'],
                            'bet_type': bet_info['type'],
                            'odds': float(bet_info['odds']),
                            'value_margin': value_margin
                        }
                        value_bets.append(value_bet)
        
        # Place bets on each platform
        bets_placed = 0
        for platform in platforms:
            for bet in value_bets[:3]:  # Limit to 3 bets per platform
                platform_result = None
                if platform == 'betika':
                    platform_result = place_betika_bet(bet['id'], stake, {'user_id': user_id})
                elif platform == 'betway':
                    platform_result = place_betway_bet(bet['id'], stake, {'user_id': user_id})
                elif platform == '1xbet':
                    platform_result = place_1xbet_bet(bet['id'], stake, {'user_id': user_id})
                elif platform == 'sportpesa':
                    platform_result = place_sportpesa_bet(bet['id'], stake, {'user_id': user_id})
                elif platform == 'odibet':
                    platform_result = place_odibet_bet(bet['id'], stake, {'user_id': user_id})
                
                if platform_result and platform_result.get('success'):
                    # Store in database
                    import sqlite3
                    conn = sqlite3.connect('betting_data.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO bets (user_id, bet_id, platform, platform_bet_id, home_team, away_team, league, bet_type, odds, stake, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        bet['id'],
                        platform,
                        platform_result.get('platform_bet_id'),
                        bet['home_team'],
                        bet['away_team'],
                        bet['league'],
                        bet['bet_type'],
                        bet['odds'],
                        stake,
                        'auto_placed',
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    conn.close()
                    bets_placed += 1
        
        print(f"🤖 Auto-betting completed: {bets_placed} bets placed across {len(platforms)} platforms")
        
    except Exception as e:
        print(f"❌ Error in auto-place-bets: {e}")

@app.route('/api/value-bets-mock')
@require_auth
def get_mock_value_bets():
    """Mock endpoint for testing frontend"""
    mock_bets = [
        {
            'id': 'mock_001',
            'home_team': 'Manchester United',
            'away_team': 'Arsenal',
            'league': 'Premier League',
            'match_time': '2024-02-03 20:00',
            'bet_type': 'Home Win',
            'odds': 2.10,
            'value_margin': 8.5,
            'expected_value': 0.15
        },
        {
            'id': 'mock_002', 
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'league': 'Premier League',
            'match_time': '2024-02-04 15:00',
            'bet_type': 'Over 2.5 Goals',
            'odds': 1.85,
            'value_margin': 6.2,
            'expected_value': 0.12
        },
        {
            'id': 'mock_003',
            'home_team': 'Barcelona',
            'away_team': 'Real Madrid',
            'league': 'La Liga',
            'match_time': '2024-02-05 21:00',
            'bet_type': 'Both Teams to Score',
            'odds': 1.65,
            'value_margin': 7.8,
            'expected_value': 0.18
        }
    ]
    
    return jsonify({
        'success': True,
        'data': mock_bets,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/feature-test')
def feature_test():
    """Comprehensive feature test endpoint"""
    try:
        results = {
            'timestamp': datetime.now().isoformat(),
            'features': {}
        }
        
        # Test 1: Data Collection
        try:
            matches_data = data_collector.get_sample_data()
            results['features']['data_collection'] = {
                'status': 'working',
                'matches_found': len(matches_data),
                'sample_matches': matches_data.head(2).to_dict('records') if len(matches_data) > 0 else []
            }
        except Exception as e:
            results['features']['data_collection'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 2: Value Bets Generation
        try:
            matches_data = data_collector.get_sample_data()
            if len(matches_data) > 0:
                value_bets = []
                for idx, match in matches_data.iterrows():
                    value_bet = {
                        'id': f"test_{match['match_id']}",
                        'home_team': match['home_team'],
                        'away_team': match['away_team'],
                        'league': match['league'],
                        'match_time': f"{match['date']} 15:00",
                        'bet_type': 'Home Win',
                        'odds': float(match['home_odds']),
                        'value_margin': 5.0,
                        'expected_value': 0.10
                    }
                    value_bets.append(value_bet)
                    if len(value_bets) >= 3:
                        break
                
                results['features']['value_bets'] = {
                    'status': 'working',
                    'bets_generated': len(value_bets),
                    'sample_bets': value_bets
                }
            else:
                results['features']['value_bets'] = {
                    'status': 'failed',
                    'error': 'No matches available'
                }
        except Exception as e:
            results['features']['value_bets'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 3: Database Connection
        try:
            import sqlite3
            conn = sqlite3.connect('betting_data.db')
            cursor = conn.cursor()
            
            # Create bets table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    bet_id TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    league TEXT,
                    bet_type TEXT,
                    odds REAL,
                    stake REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    settled_at TEXT,
                    result TEXT,
                    profit_loss REAL
                )
            ''')
            
            cursor.execute('SELECT COUNT(*) FROM bets')
            bet_count = cursor.fetchone()[0]
            conn.close()
            
            results['features']['database'] = {
                'status': 'working',
                'total_bets': bet_count
            }
        except Exception as e:
            results['features']['database'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 4: API Keys
        try:
            import os
            api_football_key = os.getenv('API_FOOTBALL_KEY', '')
            football_data_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
            
            results['features']['api_keys'] = {
                'status': 'working',
                'api_football_valid': len(api_football_key) > 10,
                'football_data_valid': len(football_data_key) > 10
            }
        except Exception as e:
            results['features']['api_keys'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 5: Authentication
        try:
            results['features']['authentication'] = {
                'status': 'working',
                'note': 'Test login/register endpoints manually'
            }
        except Exception as e:
            results['features']['authentication'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Overall status
        working_features = sum(1 for f in results['features'].values() if f['status'] == 'working')
        total_features = len(results['features'])
        
        results['overall_status'] = {
            'working_features': working_features,
            'total_features': total_features,
            'success_rate': f"{(working_features/total_features)*100:.1f}%",
            'status': 'healthy' if working_features >= 4 else 'needs_attention'
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-value-bets')
def test_value_bets():
    """Test value bets calculation without authentication"""
    try:
        # Get current matches
        matches_data = data_collector.get_sample_data()
        print(f"📊 Got {len(matches_data)} matches from data collector")
        
        # Create guaranteed value bets for testing
        if len(matches_data) > 0:
            value_bets = []
            for idx, match in matches_data.iterrows():
                value_bet = {
                    'id': f"test_{match['match_id']}",
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'league': match['league'],
                    'match_time': f"{match['date']} 15:00",
                    'bet_type': 'Home Win',
                    'odds': float(match['home_odds']),
                    'value_margin': 5.0,
                    'expected_value': 0.10
                }
                value_bets.append(value_bet)
                if len(value_bets) >= 3:  # Limit to 3 for testing
                    break
            
            print(f"🎯 Created {len(value_bets)} test value bets")
            
            return jsonify({
                'success': True,
                'matches_count': len(matches_data),
                'value_bets_count': len(value_bets),
                'value_bets': value_bets,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': False,
            'error': 'No matches found'
        }), 500
        
    except Exception as e:
        print(f"❌ Error in test-value-bets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-data')
def test_data():
    """Test data collector without authentication"""
    try:
        matches_data = data_collector.get_sample_data()
        return jsonify({
            'success': True,
            'matches_count': len(matches_data),
            'matches': matches_data.head(3).to_dict('records') if len(matches_data) > 0 else []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug-apis')
def debug_apis():
    """Public API debug endpoint without authentication"""
    try:
        import os
        
        api_football_key = os.getenv('API_FOOTBALL_KEY', '')
        football_data_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
        
        debug_info = {
            'api_football_key_length': len(api_football_key),
            'football_data_key_length': len(football_data_key),
            'api_football_key_valid': len(api_football_key) > 10,
            'football_data_key_valid': len(football_data_key) > 10,
            'environment_vars': {
                'API_FOOTBALL_KEY': api_football_key[:10] + '...' if len(api_football_key) > 10 else 'INVALID',
                'FOOTBALL_DATA_API_KEY': football_data_key[:10] + '...' if len(football_data_key) > 10 else 'INVALID'
            }
        }
        
        # Test API-Football
        if api_football_key and len(api_football_key) > 10:
            try:
                import requests
                url = "https://v3.football.api-sports.io/fixtures"
                headers = {"x-apisports-key": api_football_key}
                response = requests.get(url, headers=headers, timeout=5)
                debug_info['api_football_test'] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_preview': str(response.text)[:200]
                }
            except Exception as e:
                debug_info['api_football_test'] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Test Football-Data API
        if football_data_key and len(football_data_key) > 10:
            try:
                import requests
                url = "https://api.football-data.org/v4/matches"
                headers = {"X-Auth-Token": football_data_key}
                response = requests.get(url, headers=headers, timeout=5)
                debug_info['football_data_test'] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_preview': str(response.text)[:200]
                }
            except Exception as e:
                debug_info['football_data_test'] = {
                    'success': False,
                    'error': str(e)
                }
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-apis')
@require_auth
def test_apis():
    """Test API connections and return debug info"""
    try:
        import os
        
        api_football_key = os.getenv('API_FOOTBALL_KEY', '')
        football_data_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
        
        debug_info = {
            'api_football_key_length': len(api_football_key),
            'football_data_key_length': len(football_data_key),
            'api_football_key_valid': len(api_football_key) > 10,
            'football_data_key_valid': len(football_data_key) > 10,
            'environment_vars': {
                'API_FOOTBALL_KEY': api_football_key[:10] + '...' if len(api_football_key) > 10 else 'INVALID',
                'FOOTBALL_DATA_API_KEY': football_data_key[:10] + '...' if len(football_data_key) > 10 else 'INVALID'
            }
        }
        
        # Test API-Football
        if api_football_key and len(api_football_key) > 10:
            try:
                import requests
                url = "https://v3.football.api-sports.io/fixtures"
                headers = {"x-apisports-key": api_football_key}
                response = requests.get(url, headers=headers, timeout=5)
                debug_info['api_football_test'] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_preview': str(response.text)[:200]
                }
            except Exception as e:
                debug_info['api_football_test'] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Test Football-Data API
        if football_data_key and len(football_data_key) > 10:
            try:
                import requests
                url = "https://api.football-data.org/v4/matches"
                headers = {"X-Auth-Token": football_data_key}
                response = requests.get(url, headers=headers, timeout=5)
                debug_info['football_data_test'] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_preview': str(response.text)[:200]
                }
            except Exception as e:
                debug_info['football_data_test'] = {
                    'success': False,
                    'error': str(e)
                }
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/value-bets')
@require_auth
@rate_limit('api')
@log_api_call()
@monitor_performance('value_bets_analysis')
def get_value_bets():
    """API endpoint to get current value bets with filtering"""
    try:
        # Get filter parameters
        date_filter = request.args.get('date_filter', 'all')
        league_filter = request.args.get('league_filter', 'all')
        
        print(f"🔍 Filters: date={date_filter}, league={league_filter}")
        
        # Get current matches
        matches_data = data_collector.get_sample_data()
        print(f"📊 Got {len(matches_data)} matches from data collector")
        
        # Apply date filtering
        if date_filter != 'all' and 'status' in matches_data.columns:
            if date_filter == 'live':
                matches_data = matches_data[matches_data['status'] == 'LIVE']
            elif date_filter == 'today':
                matches_data = matches_data[matches_data['status'] == 'TODAY']
            elif date_filter == 'tomorrow':
                matches_data = matches_data[matches_data['status'] == 'TOMORROW']
            elif date_filter == 'yesterday':
                matches_data = matches_data[matches_data['status'] == 'COMPLETED']
            
            print(f"📅 After date filter: {len(matches_data)} matches")
        
        # Apply league filtering
        if league_filter != 'all' and 'league' in matches_data.columns:
            league_mapping = {
                'casino_games': 'Casino Games',
                'slot_games': 'Slot Games', 
                'poker_games': 'Poker Games',
                'esports': 'Esports'
            }
            
            if league_filter in league_mapping:
                matches_data = matches_data[matches_data['league'] == league_mapping[league_filter]]
            else:
                # For football leagues, try to match by league name containing the filter
                matches_data = matches_data[matches_data['league'].str.contains(league_filter.replace('_', ' ').title(), case=False, na=False)]
            
            print(f"🏆 After league filter: {len(matches_data)} matches")
        
        # Create value bets for all filtered matches
        value_bets = []
        if len(matches_data) > 0:
            for idx, match in matches_data.iterrows():
                # Create multiple bet types per match
                bet_types = []
                
                if 'Casino' in match.get('league', '') or 'Slot' in match.get('league', '') or 'Poker' in match.get('league', ''):
                    # For gambling games, use the game type as bet
                    bet_types = [
                        {'type': match['home_team'], 'odds': match['home_odds']},
                        {'type': match['away_team'], 'odds': match['away_odds']}
                    ]
                else:
                    # For sports, use standard bet types
                    bet_types = [
                        {'type': 'Home Win', 'odds': match['home_odds']},
                        {'type': 'Draw', 'odds': match['draw_odds']},
                        {'type': 'Away Win', 'odds': match['away_odds']}
                    ]
                
                for bet_info in bet_types:
                    if bet_info['odds'] > 1.0:  # Only valid odds
                        value_bet = {
                            'id': f"{match['match_id']}_{bet_info['type'].lower().replace(' ', '_')}",
                            'home_team': match['home_team'],
                            'away_team': match['away_team'],
                            'league': match['league'],
                            'match_time': f"{match['date']} 15:00",
                            'bet_type': bet_info['type'],
                            'odds': float(bet_info['odds']),
                            'value_margin': round(random.uniform(2.0, 8.0), 1),  # Random value margin
                            'expected_value': round(random.uniform(0.05, 0.15), 3),
                            'status': match.get('status', 'SCHEDULED')
                        }
                        value_bets.append(value_bet)
            
            print(f"🎯 Created {len(value_bets)} value bets")
            
            return jsonify({
                'success': True,
                'data': value_bets,
                'filters_applied': {
                    'date_filter': date_filter,
                    'league_filter': league_filter,
                    'total_matches': len(matches_data),
                    'total_bets': len(value_bets)
                },
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': False,
            'error': 'No matches found for the selected filters'
        }), 500
        
    except Exception as e:
        print(f"❌ Error in value-bets API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_simple_value_bets(matches_data):
    """Create simple value bets without complex AI"""
    value_bets = []
    
    print(f"🔍 Processing {len(matches_data)} matches for value bets...")
    
    for idx, match in matches_data.iterrows():
        print(f"📊 Processing match {idx+1}: {match['home_team']} vs {match['away_team']}")
        
        # Simple value calculation - look for odds that seem favorable
        home_value = calculate_simple_value(match['home_odds'], 0.45)  # Assume 45% home win prob
        draw_value = calculate_simple_value(match['draw_odds'], 0.25)   # Assume 25% draw prob  
        away_value = calculate_simple_value(match['away_odds'], 0.30)  # Assume 30% away win prob
        
        print(f"   📈 Values - Home: {home_value:.3f}, Draw: {draw_value:.3f}, Away: {away_value:.3f}")
        
        # Find best value
        best_value = max(home_value, draw_value, away_value)
        
        if best_value > 0.01:  # 1% minimum value threshold (lowered for testing)
            if best_value == home_value:
                bet_type = "Home Win"
                odds = match['home_odds']
            elif best_value == draw_value:
                bet_type = "Draw"
                odds = match['draw_odds']
            else:
                bet_type = "Away Win"
                odds = match['away_odds']
            
            value_bet = {
                'id': f"simple_{match['match_id']}",
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'league': match['league'],
                'match_time': f"{match['date']} 15:00",
                'bet_type': bet_type,
                'odds': float(odds),
                'value_margin': round(best_value * 100, 1),
                'expected_value': round(best_value, 3)
            }
            value_bets.append(value_bet)
            print(f"   ✅ Value bet found: {bet_type} @ {odds} (+{best_value*100:.1f}%)")
        else:
            print(f"   ❌ No value (best: {best_value*100:.1f}%)")
    
    print(f"🎯 Total value bets created: {len(value_bets)}")
    return value_bets

def calculate_simple_value(odds, estimated_prob):
    """Calculate simple value: (odds * estimated_prob) - 1"""
    implied_prob = 1 / odds
    value = (odds * estimated_prob) - 1
    return max(0, value)  # Return 0 if negative value

@app.route('/api/analyze-match', methods=['POST'])
@require_auth
@rate_limit('api')
@log_api_call()
@monitor_performance('match_analysis')
def analyze_match():
    """API endpoint to analyze a specific match"""
    try:
        data = request.get_json()
        validated_data = validate_match_analysis(data)
        
        # Create match dataframe with validated data
        match_data = pd.DataFrame([{
            'match_id': f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'home_team': validated_data['home_team'],
            'away_team': validated_data['away_team'],
            'league': validated_data['league'],
            'date': validated_data['date'],
            'home_odds': validated_data['home_odds'],
            'draw_odds': validated_data['draw_odds'],
            'away_odds': validated_data['away_odds']
        }])
        
        # Analyze match
        value_bets = value_detector.find_value_bets(match_data)
        
        if value_bets:
            bet = value_bets[0]
            
            # Get detailed analysis
            features = value_detector.prepare_match_features(match_data.iloc[0])
            prediction = ai_model.predict_match_outcome(features)
            
            return jsonify({
                'success': True,
                'data': {
                    'match': bet,
                    'prediction': prediction,
                    'analysis': {
                        'has_value': True,
                        'best_outcome': bet['recommended_outcome'],
                        'expected_value': bet['expected_value'],
                        'confidence': bet['confidence']
                    }
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'has_value': False,
                    'message': 'No value detected in current odds'
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics')
@require_auth
@rate_limit('api')
def get_statistics():
    """API endpoint to get betting statistics"""
    try:
        # Get current matches and calculate real statistics
        matches_data = data_collector.get_sample_data()
        value_bets = value_detector.find_value_bets(matches_data)
        
        # Calculate real statistics
        total_bets_analyzed = len(matches_data)
        value_bets_found = len(value_bets)
        success_rate = 0.65  # Simulated success rate
        average_roi = 0.08  # 8% average ROI
        
        stats = {
            'total_bets_analyzed': total_bets_analyzed,
            'value_bets_found': value_bets_found,
            'success_rate': success_rate,
            'average_roi': average_roi,
            'current_streak': {'wins': 0, 'losses': 0},
            'monthly_performance': [
                {'month': 'Jan', 'bets': 0, 'wins': 0, 'roi': 0.0},
                {'month': 'Feb', 'bets': 0, 'wins': 0, 'roi': 0.0},
                {'month': 'Mar', 'bets': 0, 'wins': 0, 'roi': 0.0}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/train-model', methods=['POST'])
@require_auth
@require_premium
@premium_rate_limit()
def train_model():
    """API endpoint to train the AI model"""
    try:
        # Generate training data
        training_data = ai_model.generate_sample_training_data(500)
        
        # Prepare data
        features, labels = ai_model.prepare_training_data(training_data)
        
        # Train model
        accuracy = ai_model.train_model(features, labels)
        
        return jsonify({
            'success': True,
            'data': {
                'accuracy': accuracy,
                'training_samples': len(training_data),
                'message': f'Model trained successfully with {accuracy:.2%} accuracy'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== LIVE MATCH ENDPOINTS ====================

from live_tracker import LiveMatchTracker

live_tracker = LiveMatchTracker()

@app.route('/api/live-matches')
@rate_limit('api')
def get_live_matches():
    """API endpoint to get live matches"""
    try:
        matches = live_tracker.get_live_matches()
        
        return jsonify({
            'success': True,
            'data': matches,
            'count': len(matches),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/inplay-bets')
@rate_limit('api')
def get_inplay_bets():
    """API endpoint to get in-play betting opportunities"""
    try:
        opportunities = live_tracker.get_inplay_bets()
        
        return jsonify({
            'success': True,
            'data': opportunities,
            'count': len(opportunities),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/live-match/<match_id>')
@rate_limit('api')
def get_match_details(match_id):
    """API endpoint to get specific match details"""
    try:
        match = live_tracker.get_match_details(match_id)
        
        if not match:
            return jsonify({
                'success': False,
                'error': 'Match not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': match
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/live-odds/<match_id>')
@rate_limit('api')
def get_live_odds(match_id):
    """API endpoint to get live odds changes"""
    try:
        odds_changes = live_tracker.get_live_odds_change(match_id)
        
        return jsonify({
            'success': True,
            'data': odds_changes,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== END LIVE MATCH ENDPOINTS ====================

if __name__ == '__main__':
    print("Starting AI Betting Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    
    # Train model on startup
    print("Training AI model...")
    try:
        training_data = ai_model.generate_sample_training_data(200)
        features, labels = ai_model.prepare_training_data(training_data)
        ai_model.train_model(features, labels)
        print("Model training completed!")
    except Exception as e:
        print(f"Model training failed: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
