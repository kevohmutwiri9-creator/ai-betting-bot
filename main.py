#!/usr/bin/env python3
"""
AI Betting Bot - Main Application
A legitimate betting assistant that analyzes matches and finds value bets.
"""

import argparse
import sys
import os
from data_collector import FootballDataCollector
from ai_model import BettingAIModel
from value_detector import ValueBetDetector
from web_dashboard import app
from telegram_bot import BettingTelegramBot

def train_ai_model():
    """Train the AI model with sample data"""
    print("🧠 Training AI Betting Model...")
    print("=" * 50)
    
    # Initialize components
    ai_model = BettingAIModel()
    
    # Generate training data
    print("📊 Generating training data...")
    training_data = ai_model.generate_sample_training_data(500)
    print(f"Generated {len(training_data)} training samples")
    
    # Prepare data
    print("🔧 Preparing features and labels...")
    features, labels = ai_model.prepare_training_data(training_data)
    
    # Train model
    print("🎯 Training RandomForest model...")
    accuracy = ai_model.train_model(features, labels)
    
    print(f"\n✅ Model training completed!")
    print(f"📈 Accuracy: {accuracy:.2%}")
    print(f"💾 Model saved to: {ai_model.model_path}")
    
    return accuracy

def analyze_value_bets():
    """Analyze current matches for value bets"""
    print("🔍 Analyzing matches for value bets...")
    print("=" * 50)
    
    # Initialize components
    data_collector = FootballDataCollector()
    value_detector = ValueBetDetector()
    
    # Get match data
    print("📋 Fetching match data...")
    matches_data = data_collector.get_sample_data()
    print(f"Found {len(matches_data)} matches to analyze")
    
    # Find value bets
    print("💎 Searching for value bets...")
    value_bets = value_detector.find_value_bets(matches_data)
    
    # Generate report
    report = value_detector.generate_value_report(value_bets)
    print("\n" + report)
    
    return value_bets

def run_web_dashboard():
    """Run the web dashboard"""
    print("🌐 Starting Web Dashboard...")
    print("=" * 50)
    print("Dashboard will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")

def run_telegram_bot(token, username):
    """Run the Telegram bot"""
    print("🤖 Starting Telegram Bot...")
    print("=" * 50)
    print(f"Bot username: @{username}")
    print("Press Ctrl+C to stop the bot")
    print("=" * 50)
    
    bot = BettingTelegramBot(token, username)
    bot.run()

def demo_mode():
    """Run a demo of the AI betting system"""
    print("🎯 AI Betting Bot Demo")
    print("=" * 50)
    
    # Step 1: Train model
    print("\n📚 Step 1: Training AI Model")
    accuracy = train_ai_model()
    
    # Step 2: Analyze value bets
    print("\n💎 Step 2: Finding Value Bets")
    value_bets = analyze_value_bets()
    
    # Step 3: Show results
    print("\n📊 Step 3: Demo Results")
    print(f"✅ Model trained with {accuracy:.1%} accuracy")
    print(f"🎯 Found {len(value_bets)} value bets")
    
    if value_bets:
        print("\n🏆 Top Value Bet:")
        top_bet = max(value_bets, key=lambda x: x['expected_value'])
        print(f"   Match: {top_bet['home_team']} vs {top_bet['away_team']}")
        print(f"   Pick: {top_bet['recommended_outcome']} @ {top_bet['odds']}")
        print(f"   Value: +{top_bet['value_margin']}%")
        print(f"   Expected Value: {top_bet['expected_value']}")
    
    print("\n🚀 Ready to start your betting assistant!")
    print("\nNext steps:")
    print("1. Run 'python main.py --web' for dashboard")
    print("2. Run 'python main.py --telegram TOKEN USERNAME' for Telegram bot")
    print("3. Customize with real data sources")

def main():
    parser = argparse.ArgumentParser(
        description="AI Betting Bot - Find value bets using machine learning"
    )
    
    parser.add_argument(
        '--train', 
        action='store_true',
        help='Train the AI model'
    )
    
    parser.add_argument(
        '--analyze', 
        action='store_true',
        help='Analyze current matches for value bets'
    )
    
    parser.add_argument(
        '--web', 
        action='store_true',
        help='Run web dashboard'
    )
    
    parser.add_argument(
        '--telegram', 
        nargs=2,
        metavar=('TOKEN', 'USERNAME'),
        help='Run Telegram bot (requires token and username)'
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Run demo mode'
    )
    
    args = parser.parse_args()
    
    if args.demo:
        demo_mode()
    elif args.train:
        train_ai_model()
    elif args.analyze:
        analyze_value_bets()
    elif args.web:
        run_web_dashboard()
    elif args.telegram:
        token, username = args.telegram
        run_telegram_bot(token, username)
    else:
        print("🎯 AI Betting Bot")
        print("=" * 30)
        print("A legitimate betting assistant that analyzes matches and finds value bets.")
        print("\nUsage:")
        print("  python main.py --demo          Run demo")
        print("  python main.py --train         Train AI model")
        print("  python main.py --analyze       Analyze value bets")
        print("  python main.py --web           Start web dashboard")
        print("  python main.py --telegram TOKEN USERNAME  Start Telegram bot")
        print("\n⚠️  Disclaimer: This is for analysis purposes only. Bet responsibly.")

if __name__ == "__main__":
    main()
