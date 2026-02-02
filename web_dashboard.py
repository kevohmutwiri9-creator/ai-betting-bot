from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
import json
from value_detector import ValueBetDetector
from data_collector import FootballDataCollector
from ai_model import BettingAIModel
from auth import auth_manager, require_auth, require_premium

app = Flask(__name__)

# Initialize components
value_detector = ValueBetDetector()
data_collector = FootballDataCollector()
ai_model = BettingAIModel()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        result = auth_manager.register_user(username, email, password)
        
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
def login():
    """Authenticate user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({
                'success': False,
                'error': 'Missing username or password'
            }), 400
        
        result = auth_manager.authenticate_user(username, password)
        
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
def auto_bet():
    """API endpoint for auto-betting functionality"""
    try:
        data = request.get_json()
        
        # Get betting parameters
        stake = float(data.get('stake', 100))
        max_odds = float(data.get('max_odds', 10.0))
        min_value = float(data.get('min_value', 5.0))
        auto_confirm = data.get('auto_confirm', False)
        
        # Get current value bets
        matches_data = data_collector.get_sample_data()
        value_bets = value_detector.find_value_bets(matches_data)
        
        # Filter bets based on criteria
        filtered_bets = []
        for bet in value_bets:
            if (float(bet['odds']) <= max_odds and 
                float(bet['value_margin']) >= min_value):
                filtered_bets.append(bet)
        
        if not filtered_bets:
            return jsonify({
                'success': False,
                'error': 'No bets meet your criteria'
            })
        
        # Calculate total stake and potential returns
        total_stake = len(filtered_bets) * stake
        total_potential = sum([float(bet['odds']) * stake for bet in filtered_bets])
        
        # Place bets (simulation)
        placed_bets = []
        for bet in filtered_bets:
            bet_result = {
                'match_id': bet['match_id'],
                'teams': f"{bet['home_team']} vs {bet['away_team']}",
                'pick': bet['recommended_outcome'],
                'odds': bet['odds'],
                'value': bet['value_margin'],
                'stake': stake,
                'potential_return': float(bet['odds']) * stake,
                'status': 'placed' if auto_confirm else 'pending'
            }
            placed_bets.append(bet_result)
        
        return jsonify({
            'success': True,
            'data': {
                'placed_bets': placed_bets,
                'total_stake': total_stake,
                'total_potential_return': total_potential,
                'bet_count': len(placed_bets),
                'auto_confirm': auto_confirm
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/betting-history')
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
def analyze_match():
    """API endpoint to analyze a specific match"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['home_team', 'away_team', 'home_odds', 'draw_odds', 'away_odds']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create match dataframe
        match_data = pd.DataFrame([{
            'match_id': f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'home_team': data['home_team'],
            'away_team': data['away_team'],
            'league': data.get('league', 'Custom'),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'home_odds': float(data['home_odds']),
            'draw_odds': float(data['draw_odds']),
            'away_odds': float(data['away_odds'])
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
