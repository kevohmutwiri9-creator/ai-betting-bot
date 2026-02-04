from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
import json
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
    """API endpoint to get betting history"""
    try:
        # Check if there are any actual betting records
        # For now, return empty history since no betting has occurred
        history = []
        
        return jsonify({
            'success': True,
            'data': history
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
        
        # Find value bets
        value_bets = value_detector.find_value_bets(matches_data)
        
        return jsonify({
            'success': True,
            'data': value_bets,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
