#!/usr/bin/env python3
"""
Simple AI Betting Bot Demo - No external dependencies required
Demonstrates the core logic of value betting analysis
"""

import random
import math
from datetime import datetime

class SimpleBettingAI:
    def __init__(self):
        self.team_strengths = {
            'Manchester United': 0.75,
            'Arsenal': 0.80,
            'Liverpool': 0.85,
            'Chelsea': 0.78,
            'Barcelona': 0.88,
            'Real Madrid': 0.90,
            'Manchester City': 0.87,
            'Bayern Munich': 0.86
        }
    
    def calculate_win_probability(self, home_team, away_team):
        """Calculate win probability based on team strengths"""
        home_strength = self.team_strengths.get(home_team, 0.5)
        away_strength = self.team_strengths.get(away_team, 0.5)
        
        # Home advantage factor
        home_advantage = 1.15
        
        # Calculate probabilities
        home_adj = home_strength * home_advantage
        away_adj = away_strength
        
        total = home_adj + away_adj
        home_prob = home_adj / total
        away_prob = away_adj / total
        draw_prob = 0.25  # Base draw probability
        
        # Normalize to ensure sum = 1
        total_prob = home_prob + away_prob + draw_prob
        return {
            'home_win': home_prob / total_prob,
            'draw': draw_prob / total_prob,
            'away_win': away_prob / total_prob
        }
    
    def calculate_expected_value(self, probability, odds):
        """Calculate expected value of a bet"""
        return (probability * odds) - 1

class ValueBetDetector:
    def __init__(self):
        self.ai = SimpleBettingAI()
        self.min_value_threshold = 0.05  # 5% minimum value
    
    def analyze_match(self, home_team, away_team, home_odds, draw_odds, away_odds):
        """Analyze a match for value betting opportunities"""
        # Get AI predictions
        probabilities = self.ai.calculate_win_probability(home_team, away_team)
        
        # Calculate bookmaker implied probabilities
        home_implied = 1 / home_odds
        draw_implied = 1 / draw_odds
        away_implied = 1 / away_odds
        
        # Calculate bookmaker margin
        total_implied = home_implied + draw_implied + away_implied
        margin = total_implied - 1.0
        
        # Adjust implied probabilities for margin
        home_bookmaker = home_implied / (1 + margin)
        draw_bookmaker = draw_implied / (1 + margin)
        away_bookmaker = away_implied / (1 + margin)
        
        # Calculate expected values
        home_ev = self.ai.calculate_expected_value(probabilities['home_win'], home_odds)
        draw_ev = self.ai.calculate_expected_value(probabilities['draw'], draw_odds)
        away_ev = self.ai.calculate_expected_value(probabilities['away_win'], away_odds)
        
        # Find best value bet
        bets = [
            {
                'outcome': 'Home Win',
                'odds': home_odds,
                'ai_prob': probabilities['home_win'],
                'bookmaker_prob': home_bookmaker,
                'ev': home_ev,
                'value_margin': probabilities['home_win'] - home_bookmaker
            },
            {
                'outcome': 'Draw',
                'odds': draw_odds,
                'ai_prob': probabilities['draw'],
                'bookmaker_prob': draw_bookmaker,
                'ev': draw_ev,
                'value_margin': probabilities['draw'] - draw_bookmaker
            },
            {
                'outcome': 'Away Win',
                'odds': away_odds,
                'ai_prob': probabilities['away_win'],
                'bookmaker_prob': away_bookmaker,
                'ev': away_ev,
                'value_margin': probabilities['away_win'] - away_bookmaker
            }
        ]
        
        # Find best bet with positive value
        best_bet = None
        for bet in bets:
            if bet['value_margin'] > self.min_value_threshold and bet['ev'] > 0:
                if best_bet is None or bet['ev'] > best_bet['ev']:
                    best_bet = bet
        
        return {
            'match': f"{home_team} vs {away_team}",
            'probabilities': probabilities,
            'bookmaker_margin': margin,
            'best_bet': best_bet,
            'all_bets': bets
        }

def main():
    print("🎯 AI Betting Bot Demo")
    print("=" * 50)
    print("Finding value bets using mathematical analysis...")
    print()
    
    detector = ValueBetDetector()
    
    # Sample matches with different odds scenarios
    matches = [
        {
            'home': 'Manchester United',
            'away': 'Arsenal',
            'home_odds': 2.50,  # Higher odds - potential value
            'draw_odds': 3.40,
            'away_odds': 2.80
        },
        {
            'home': 'Liverpool',
            'away': 'Chelsea',
            'home_odds': 1.85,  # Lower odds - less likely value
            'draw_odds': 3.60,
            'away_odds': 4.10
        },
        {
            'home': 'Barcelona',
            'away': 'Real Madrid',
            'home_odds': 2.80,  # Competitive match
            'draw_odds': 3.20,
            'away_odds': 2.40
        }
    ]
    
    value_bets_found = []
    
    for i, match in enumerate(matches, 1):
        print(f"📊 Match {i}: {match['home']} vs {match['away']}")
        print("-" * 40)
        
        analysis = detector.analyze_match(
            match['home'], match['away'],
            match['home_odds'], match['draw_odds'], match['away_odds']
        )
        
        print(f"AI Probabilities:")
        print(f"  Home Win: {analysis['probabilities']['home_win']:.1%}")
        print(f"  Draw: {analysis['probabilities']['draw']:.1%}")
        print(f"  Away Win: {analysis['probabilities']['away_win']:.1%}")
        print(f"Bookmaker Margin: {analysis['bookmaker_margin']:.1%}")
        
        if analysis['best_bet']:
            bet = analysis['best_bet']
            print(f"\n💎 VALUE BET DETECTED!")
            print(f"  Recommendation: {bet['outcome']}")
            print(f"  Odds: {bet['odds']}")
            print(f"  AI Probability: {bet['ai_prob']:.1%}")
            print(f"  Bookmaker Probability: {bet['bookmaker_prob']:.1%}")
            print(f"  Value Margin: +{bet['value_margin']:.1%}")
            print(f"  Expected Value: {bet['ev']:.3f}")
            
            value_bets_found.append({
                'match': analysis['match'],
                'bet': bet
            })
        else:
            print("\n❌ No value detected in current odds")
        
        print("\n" + "=" * 50 + "\n")
    
    # Summary
    print("📈 SUMMARY")
    print("=" * 50)
    print(f"Total matches analyzed: {len(matches)}")
    print(f"Value bets found: {len(value_bets_found)}")
    
    if value_bets_found:
        print("\n🏆 TOP VALUE BETS:")
        for i, vb in enumerate(value_bets_found, 1):
            bet = vb['bet']
            print(f"{i}. {vb['match']}")
            print(f"   {bet['outcome']} @ {bet['odds']} (EV: {bet['ev']:.3f})")
    
    print("\n💡 KEY INSIGHTS:")
    print("• Value bets occur when bookmaker odds underestimate true probability")
    print("• Expected Value (EV) > 0 indicates long-term profitability")
    print("• Bookmaker margin (vig) is typically 5-10%")
    print("• Professional bettors target 55-60% accuracy with value betting")
    
    print("\n⚠️  IMPORTANT DISCLAIMER:")
    print("This is educational software, not financial advice.")
    print("Sports betting involves risk. Never bet more than you can afford to lose.")
    print("Even the best models lose - focus on long-term edge, not short-term results.")

if __name__ == "__main__":
    main()
