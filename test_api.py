#!/usr/bin/env python3
"""
API Connection Test Script for AI Betting Bot
Tests API keys and connections
"""

import sys
import os

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from data_collector import FootballDataCollector

def test_api_connections():
    """Test all configured API connections"""
    print("=" * 60)
    print("API Connection Test")
    print("=" * 60)
    
    collector = FootballDataCollector()
    
    # Test Football-Data API
    print("\n1. Testing Football-Data.org API...")
    print("   API Key: {}...".format(collector.api_keys['football_data'][:10]))
    
    try:
        # Test fetching competitions
        response = collector.fetch_from_football_data_api('competitions')
        if response:
            print("   [OK] SUCCESS: Connected to Football-Data.org")
            print("   Info: Found {} competitions".format(len(response.get('competitions', []))))
        else:
            print("   [WARN] No response from Football-Data.org")
    except Exception as e:
        print("   [FAIL] FAILED: {}".format(e))
    
    # Test API-Football
    print("\n2. Testing API-Football...")
    print("   API Key: {}...".format(collector.api_keys['api_football'][:10]))
    
    try:
        # Test fetching leagues
        response = collector.fetch_from_api_football('leagues')
        if response and 'response' in response:
            print("   [OK] SUCCESS: Connected to API-Football")
            leagues = response.get('response', [])
            print("   Info: Found {} leagues".format(len(leagues)))
            # Show first few leagues
            for league in leagues[:3]:
                name = league.get('league', {}).get('name', 'Unknown')
                country = league.get('country', {}).get('name', 'Unknown')
                print("      - {} ({})".format(name, country))
        else:
            print("   [WARN] No response from API-Football")
    except Exception as e:
        print("   [FAIL] FAILED: {}".format(e))
    
    # Test match data retrieval
    print("\n3. Testing Match Data Retrieval...")
    
    try:
        # Get upcoming matches
        matches = collector.get_upcoming_matches(days_ahead=1)
        print("   [OK] Retrieved {} upcoming matches".format(len(matches)))
        
        if matches:
            print("\n   Sample matches:")
            for match in matches[:3]:
                print("   Match: {} vs {}".format(match['home_team'], match['away_team']))
                print("      League: {}".format(match['league']))
                print("      Date: {}".format(match['date']))
    except Exception as e:
        print("   [FAIL] FAILED: {}".format(e))
    
    # Test live matches
    print("\n4. Testing Live Matches...")
    
    try:
        live = collector.get_live_matches()
        print("   [OK] Found {} live matches".format(len(live)))
        
        if not live:
            print("   [INFO] No live matches at the moment")
    except Exception as e:
        print("   [FAIL] FAILED: {}".format(e))
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_api_connections()
