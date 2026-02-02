import pandas as pd
import numpy as np
from ai_model import BettingAIModel

class ValueBetDetector:
    def __init__(self, model_path="betting_model.pkl"):
        self.ai_model = BettingAIModel(model_path)
        self.min_value_threshold = 0.05  # 5% minimum value margin
    
    def calculate_implied_probability(self, odds):
        """Calculate implied probability from odds"""
        return 1 / odds
    
    def calculate_bookmaker_margin(self, home_odds, draw_odds, away_odds):
        """Calculate bookmaker's margin (vig)"""
        implied_home = self.calculate_implied_probability(home_odds)
        implied_draw = self.calculate_implied_probability(draw_odds)
        implied_away = self.calculate_implied_probability(away_odds)
        
        total_implied = implied_home + implied_draw + implied_away
        margin = total_implied - 1.0
        
        return margin
    
    def adjust_for_margin(self, implied_prob, margin):
        """Adjust implied probability for bookmaker margin"""
        return implied_prob / (1 + margin)
    
    def find_value_bets(self, matches_data):
        """Find value bets in a list of matches"""
        value_bets = []
        
        for _, match in matches_data.iterrows():
            # Prepare features for AI prediction
            features = self.prepare_match_features(match)
            
            # Get AI prediction
            try:
                prediction = self.ai_model.predict_match_outcome(features)
                
                # Calculate bookmaker margin
                margin = self.calculate_bookmaker_margin(
                    match['home_odds'], match['draw_odds'], match['away_odds']
                )
                
                # Calculate value for each outcome
                value_analysis = self.analyze_match_value(match, prediction, margin)
                
                # Check if any outcome has value
                best_bet = self.get_best_value_bet(value_analysis, match)
                
                if best_bet:
                    value_bets.append(best_bet)
                    
            except Exception as e:
                print(f"Error processing match {match.get('match_id', 'unknown')}: {e}")
                continue
        
        return value_bets
    
    def prepare_match_features(self, match):
        """Prepare feature vector for AI model"""
        home_strength = self.ai_model.calculate_team_strength(match['home_team'])
        away_strength = self.ai_model.calculate_team_strength(match['away_team'])
        
        return [
            home_strength,
            away_strength,
            1.0,  # Home advantage
            match['home_odds'],
            match['draw_odds'],
            match['away_odds']
        ]
    
    def analyze_match_value(self, match, prediction, margin):
        """Analyze value for all possible outcomes"""
        # Get bookmaker implied probabilities
        home_implied = self.calculate_implied_probability(match['home_odds'])
        draw_implied = self.calculate_implied_probability(match['draw_odds'])
        away_implied = self.calculate_implied_probability(match['away_odds'])
        
        # Adjust for margin
        home_bookmaker_prob = self.adjust_for_margin(home_implied, margin)
        draw_bookmaker_prob = self.adjust_for_margin(draw_implied, margin)
        away_bookmaker_prob = self.adjust_for_margin(away_implied, margin)
        
        # Calculate expected value for each outcome
        home_ev = self.calculate_expected_value(
            prediction['home_win_prob'], home_bookmaker_prob, match['home_odds']
        )
        draw_ev = self.calculate_expected_value(
            prediction['draw_prob'], draw_bookmaker_prob, match['draw_odds']
        )
        away_ev = self.calculate_expected_value(
            prediction['away_win_prob'], away_bookmaker_prob, match['away_odds']
        )
        
        return {
            'home_win': {
                'ai_probability': prediction['home_win_prob'],
                'bookmaker_probability': home_bookmaker_prob,
                'odds': match['home_odds'],
                'expected_value': home_ev,
                'value_margin': prediction['home_win_prob'] - home_bookmaker_prob
            },
            'draw': {
                'ai_probability': prediction['draw_prob'],
                'bookmaker_probability': draw_bookmaker_prob,
                'odds': match['draw_odds'],
                'expected_value': draw_ev,
                'value_margin': prediction['draw_prob'] - draw_bookmaker_prob
            },
            'away_win': {
                'ai_probability': prediction['away_win_prob'],
                'bookmaker_probability': away_bookmaker_prob,
                'odds': match['away_odds'],
                'expected_value': away_ev,
                'value_margin': prediction['away_win_prob'] - away_bookmaker_prob
            },
            'margin': margin
        }
    
    def calculate_expected_value(self, ai_prob, bookmaker_prob, odds):
        """Calculate expected value of a bet"""
        # EV = (Probability * Payout) - (Probability * Stake)
        # Where Payout = odds and Stake = 1
        return (ai_prob * odds) - 1
    
    def get_best_value_bet(self, value_analysis, match):
        """Get the best value bet from the analysis"""
        outcomes = ['home_win', 'draw', 'away_win']
        best_bet = None
        highest_ev = -float('inf')
        
        for outcome in outcomes:
            analysis = value_analysis[outcome]
            
            # Check if this outcome has positive value
            if (analysis['value_margin'] > self.min_value_threshold and 
                analysis['expected_value'] > 0 and
                analysis['expected_value'] > highest_ev):
                
                highest_ev = analysis['expected_value']
                
                # Determine outcome name
                outcome_name = outcome.replace('_', ' ').title()
                
                best_bet = {
                    'match_id': match.get('match_id', 'unknown'),
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'league': match.get('league', 'Unknown'),
                    'date': match.get('date', 'Unknown'),
                    'recommended_outcome': outcome_name,
                    'odds': analysis['odds'],
                    'ai_probability': round(analysis['ai_probability'] * 100, 1),
                    'bookmaker_probability': round(analysis['bookmaker_probability'] * 100, 1),
                    'value_margin': round(analysis['value_margin'] * 100, 1),
                    'expected_value': round(analysis['expected_value'], 3),
                    'confidence': self.calculate_confidence(analysis['value_margin'])
                }
        
        return best_bet
    
    def calculate_confidence(self, value_margin):
        """Calculate confidence level based on value margin"""
        if value_margin > 0.15:
            return "High"
        elif value_margin > 0.10:
            return "Medium"
        else:
            return "Low"
    
    def generate_value_report(self, value_bets):
        """Generate a report of found value bets"""
        if not value_bets:
            return "No value bets found in the current matches."
        
        report = "🎯 VALUE BETS REPORT\n"
        report += "=" * 50 + "\n\n"
        
        for i, bet in enumerate(value_bets, 1):
            report += f"📊 BET #{i}\n"
            report += f"Match: {bet['home_team']} vs {bet['away_team']}\n"
            report += f"League: {bet['league']}\n"
            report += f"Date: {bet['date']}\n"
            report += f"Recommendation: {bet['recommended_outcome']}\n"
            report += f"Odds: {bet['odds']}\n"
            report += f"AI Probability: {bet['ai_probability']}%\n"
            report += f"Bookmaker Probability: {bet['bookmaker_probability']}%\n"
            report += f"Value Margin: +{bet['value_margin']}%\n"
            report += f"Expected Value: {bet['expected_value']}\n"
            report += f"Confidence: {bet['confidence']}\n"
            report += "-" * 30 + "\n\n"
        
        return report

if __name__ == "__main__":
    # Test the value detector
    detector = ValueBetDetector()
    
    # Sample matches data
    sample_matches = pd.DataFrame([
        {
            'match_id': 'test_001',
            'home_team': 'Manchester United',
            'away_team': 'Arsenal',
            'league': 'Premier League',
            'date': '2024-02-03',
            'home_odds': 2.50,  # Higher odds than usual - potential value
            'draw_odds': 3.40,
            'away_odds': 2.80
        },
        {
            'match_id': 'test_002',
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'league': 'Premier League',
            'date': '2024-02-04',
            'home_odds': 1.85,
            'draw_odds': 3.60,
            'away_odds': 4.10
        }
    ])
    
    # Find value bets
    value_bets = detector.find_value_bets(sample_matches)
    
    # Generate report
    report = detector.generate_value_report(value_bets)
    print(report)
