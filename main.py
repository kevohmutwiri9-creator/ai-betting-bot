"""
Main entry point for AI Betting Bot
Provides command-line interface for different modes
"""

import argparse
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collector import FootballDataCollector
from ai_model import BettingAIModel
from value_detector import ValueBetDetector
from web_dashboard import app
from telegram_bot import BettingTelegramBot
from config import *

def run_demo():
    """Run demonstration of all features"""
    print("🎯 AI Betting Bot - Demo Mode")
    print("=" * 50)
    
    # Initialize components
    print("\n📊 Initializing components...")
    collector = FootballDataCollector()
    ai_model = BettingAIModel()
    detector = ValueBetDetector()
    
    # Generate and train model
    print("\n🧠 Training AI model...")
    training_data = ai_model.generate_sample_training_data(200)
    features, labels = ai_model.prepare_training_data(training_data)
    accuracy = ai_model.train_model(features, labels)
    print(f"✅ Model trained with {accuracy:.2%} accuracy")
    
    # Get sample matches
    print("\n⚽ Fetching match data...")
    matches = collector.get_sample_data()
    print(f"✅ Found {len(matches)} matches")
    
    # Find value bets
    print("\n💎 Analyzing for value bets...")
    value_bets = detector.find_value_bets(matches)
    
    if value_bets:
        print(f"✅ Found {len(value_bets)} value bets:")
        for i, bet in enumerate(value_bets, 1):
            print(f"\n📊 Bet #{i}:")
            print(f"   Match: {bet['home_team']} vs {bet['away_team']}")
            print(f"   Recommendation: {bet['recommended_outcome']} @ {bet['odds']}")
            print(f"   Value Margin: +{bet['value_margin']}%")
            print(f"   Expected Value: {bet['expected_value']}")
            print(f"   Confidence: {bet['confidence']}")
    else:
        print("❌ No value bets found in current matches")
    
    print("\n🎉 Demo completed successfully!")
    print("\n💡 Next steps:")
    print("   • Run 'python main.py --web' for dashboard")
    print("   • Run 'python main.py --telegram TOKEN USERNAME' for bot")
    print("   • Configure your .env file with real API keys")

def run_web():
    """Start web dashboard"""
    print("🌐 Starting AI Betting Dashboard...")
    print(f"📍 Dashboard will be available at: http://localhost:5000")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        app.run(debug=DEBUG_MODE, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def run_telegram(token, username):
    """Start Telegram bot"""
    # Try to get token/username from environment variables if not provided
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not username:
        username = os.environ.get("TELEGRAM_BOT_USERNAME", "")
    
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ Please provide a valid Telegram bot token")
        print("💡 Get your token from @BotFather on Telegram")
        print("💡 Or set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    if not username:
        print("❌ Please provide your bot username")
        print("💡 Or set TELEGRAM_BOT_USERNAME environment variable")
        return
    
    print(f"🤖 Starting Telegram Bot @{username}...")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        bot = BettingTelegramBot(token, username)
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

def run_api_test():
    """Test API endpoints"""
    print("🧪 Testing API endpoints...")
    
    # Test data collection
    collector = FootballDataCollector()
    matches = collector.get_sample_data()
    print(f"✅ Data collection: {len(matches)} matches retrieved")
    
    # Test AI model
    ai_model = BettingAIModel()
    try:
        ai_model.load_model()
        print("✅ AI model: Loaded successfully")
    except:
        print("⚠️  AI model: Not trained, training now...")
        training_data = ai_model.generate_sample_training_data(100)
        features, labels = ai_model.prepare_training_data(training_data)
        ai_model.train_model(features, labels)
        print("✅ AI model: Trained successfully")
    
    # Test value detection
    detector = ValueBetDetector()
    value_bets = detector.find_value_bets(matches)
    print(f"✅ Value detection: {len(value_bets)} value bets found")
    
    print("\n🎉 All API tests passed!")

def check_environment():
    """Check environment configuration"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'FOOTBALL_DATA_API_KEY',
        'API_FOOTBALL_KEY'
    ]
    
    optional_vars = [
        'API_SECRET_KEY',
        'SESSION_SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    print("\n📋 Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"YOUR_{var}":
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing or placeholder")
    
    print("\n📋 Optional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}":
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ⚠️  {var}: Using default")
    
    print(f"\n📁 Database path: {DATABASE_PATH}")
    print(f"🌍 Environment: {ENVIRONMENT}")
    print(f"🐛 Debug mode: {DEBUG_MODE}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Betting Bot - Find value bets using machine learning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo                    # Run demo
  python main.py --web                     # Start web dashboard
  python main.py --telegram TOKEN USERNAME # Start Telegram bot
  python main.py --test                    # Test APIs
  python main.py --check                   # Check environment
        """
    )
    
    parser.add_argument('--demo', action='store_true', 
                       help='Run demonstration of all features')
    parser.add_argument('--web', action='store_true',
                       help='Start web dashboard server')
    parser.add_argument('--telegram', nargs=2, metavar=('TOKEN', 'USERNAME'),
                       help='Start Telegram bot with token and username')
    parser.add_argument('--test', action='store_true',
                       help='Test all API components')
    parser.add_argument('--check', action='store_true',
                       help='Check environment configuration')
    
    args = parser.parse_args()
    
    # Show banner
    print("🎯 AI Betting Bot")
    print("=" * 50)
    print("⚠️  Educational purposes only - Bet responsibly!")
    print("=" * 50)
    
    if args.demo:
        run_demo()
    elif args.web:
        run_web()
    elif args.telegram:
        run_telegram(args.telegram[0], args.telegram[1])
    elif args.test:
        run_api_test()
    elif args.check:
        check_environment()
    else:
        parser.print_help()
        print("\n💡 Quick start: python main.py --demo")

if __name__ == "__main__":
    main()
