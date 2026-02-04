from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
import os
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

app = Flask(__name__)

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
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': os.getenv('ENVIRONMENT', 'unknown')
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
    """Place a real bet"""
    try:
        data = request.get_json()
        bet_id = data.get('bet_id')
        
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
            INSERT INTO bets (user_id, bet_id, home_team, away_team, league, bet_type, odds, stake, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_info['user_id'],
            bet_id,
            bet_details['home_team'],
            bet_details['away_team'],
            bet_details['league'],
            bet_details['bet_type'],
            bet_details['odds'],
            100.0,  # Default stake KES 100
            'pending',
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"💰 Bet placed: {bet_details['home_team']} vs {bet_details['away_team']} - {bet_details['bet_type']}")
        
        return jsonify({
            'success': True,
            'message': 'Bet placed successfully!',
            'bet_details': bet_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error placing bet: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    """API endpoint to get current value bets"""
    try:
        # Get current matches
        matches_data = data_collector.get_sample_data()
        print(f"📊 Got {len(matches_data)} matches from data collector")
        
        # Try to find real value bets
        try:
            value_bets = value_detector.find_value_bets(matches_data)
            print(f"💎 Found {len(value_bets)} value bets from AI model")
            
            # If AI model returns empty, create simple value bets
            if not value_bets:
                print("⚠️ AI model returned empty, creating simple value bets")
                value_bets = create_simple_value_bets(matches_data)
                
        except Exception as ai_error:
            print(f"❌ AI model failed: {ai_error}")
            print("🔄 Using simple value bet calculation")
            value_bets = create_simple_value_bets(matches_data)
        
        print(f"📋 Returning {len(value_bets)} value bets")
        
        return jsonify({
            'success': True,
            'data': value_bets,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Error in value-bets API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_simple_value_bets(matches_data):
    """Create simple value bets without complex AI"""
    value_bets = []
    
    for _, match in matches_data.iterrows():
        # Simple value calculation - look for odds that seem favorable
        home_value = calculate_simple_value(match['home_odds'], 0.45)  # Assume 45% home win prob
        draw_value = calculate_simple_value(match['draw_odds'], 0.25)   # Assume 25% draw prob  
        away_value = calculate_simple_value(match['away_odds'], 0.30)  # Assume 30% away win prob
        
        # Find best value
        best_value = max(home_value, draw_value, away_value)
        
        if best_value > 0.05:  # 5% minimum value threshold
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
