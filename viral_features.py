"""
Viral Features for AI Betting Bot
Social sharing, referral system, and growth hacking features
"""

import json
import uuid
from datetime import datetime
import sqlite3

class ViralGrowthEngine:
    def __init__(self, db_path="viral_growth.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize viral growth database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id TEXT,
                referred_id TEXT,
                referral_code TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viral_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                platform TEXT,
                content_type TEXT,
                share_count INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                metric_type TEXT,
                metric_value REAL,
                rank_position INTEGER,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_referral_code(self, user_id):
        """Generate unique referral code for user"""
        code = f"BET{uuid.uuid4().hex[:8].upper()}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referral_code, status, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, code, 'active', datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return code
    
    def track_referral(self, referrer_id, referred_id, referral_code):
        """Track successful referral"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, referral_code, status, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (referrer_id, referred_id, referral_code, 'completed', datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def create_shareable_content(self, user_id, value_bets, platform):
        """Create platform-specific shareable content"""
        if not value_bets:
            return None
        
        top_bet = max(value_bets, key=lambda x: x['expected_value'])
        
        content_generators = {
            'twitter': self._generate_twitter_share,
            'instagram': self._generate_instagram_share,
            'facebook': self._generate_facebook_share,
            'tiktok': self._generate_tiktok_share,
            'whatsapp': self._generate_whatsapp_share
        }
        
        generator = content_generators.get(platform, self._generate_generic_share)
        return generator(user_id, top_bet)
    
    def _generate_twitter_share(self, user_id, bet):
        """Generate Twitter shareable content"""
        referral_link = self._get_referral_link(user_id)
        
        return {
            'text': f"""🤯 AI found another value bet!

{bet['home_team']} vs {bet['away_team']}
💎 {bet['recommended_outcome']} @ {bet['odds']}
📈 Value: +{bet['value_margin']}%

Get the FREE AI bot: {referral_link}

#AI #Betting #ValueBet""",
            'hashtags': ['#AI', '#Betting', '#ValueBet', '#SportsBetting'],
            'image': 'bet_result_template.png'
        }
    
    def _generate_instagram_share(self, user_id, bet):
        """Generate Instagram shareable content"""
        referral_link = self._get_referral_link(user_id)
        
        return {
            'image_text': f"""AI BETTING BOT
FREE VALUE BET!

{bet['home_team']} vs {bet['away_team']}
{bet['recommended_outcome']} @ {bet['odds']}
Value: +{bet['value_margin']}%

📥 Link in Bio for FREE Bot!""",
            'story_link': referral_link,
            'hashtags': ['#AI', '#Betting', '#SportsBetting', '#FreeBettingTips']
        }
    
    def _generate_facebook_share(self, user_id, bet):
        """Generate Facebook shareable content"""
        referral_link = self._get_referral_link(user_id)
        
        return {
            'title': 'AI Betting Bot Found Value Bet!',
            'description': f"""Our AI discovered a mathematical edge in today's matches:

{bet['home_team']} vs {bet['away_team']}
Recommendation: {bet['recommended_outcome']} @ {bet['odds']}
Value Margin: +{bet['value_margin']}%
Expected Value: {bet['expected_value']}

Get unlimited value bets with our FREE AI bot!""",
            'link': referral_link,
            'image': 'facebook_share_template.png'
        }
    
    def _generate_tiktok_share(self, user_id, bet):
        """Generate TikTok shareable content"""
        referral_link = self._get_referral_link(user_id)
        
        return {
            'video_script': f"""Scene 1: Bookmakers made a mistake...
Scene 2: Our AI found it!
Scene 3: {bet['home_team']} vs {bet['away_team']}
Scene 4: {bet['recommended_outcome']} @ {bet['odds']}
Scene 5: Value: +{bet['value_margin']}%
Scene 6: FREE AI BOT LINK IN BIO!""",
            'trending_sound': 'viral_betting_sound',
            'text_overlay': f"Value: +{bet['value_margin']}%",
            'caption': f"AI vs Bookmakers! Who wins? 🤖 {referral_link}",
            'hashtags': ['#AI', '#Betting', '#SportsBetting', '#Viral']
        }
    
    def _generate_whatsapp_share(self, user_id, bet):
        """Generate WhatsApp shareable content"""
        referral_link = self._get_referral_link(user_id)
        
        return {
            'message': f"""🤖 *AI Betting Bot - FREE Value Bet!*

*{bet['home_team']} vs {bet['away_team']}*
💎 *Pick:* {bet['recommended_outcome']} @ {bet['odds']}
📈 *Value:* +{bet['value_margin']}%
🎲 *EV:* {bet['expected_value']}

📥 *Get FREE AI Bot:* {referral_link}

Don't tell everyone about this! 😉""",
            'image': 'whatsapp_share_template.png'
        }
    
    def _generate_generic_share(self, user_id, bet):
        """Generate generic shareable content"""
        referral_link = self._get_referral_link(user_id)
        
        return {
            'title': 'AI Betting Bot - Value Bet Found!',
            'content': f"""{bet['home_team']} vs {bet['away_team']}
{bet['recommended_outcome']} @ {bet['odds']}
Value: +{bet['value_margin']}%
Get FREE AI bot: {referral_link}""",
            'link': referral_link
        }
    
    def _get_referral_link(self, user_id):
        """Get referral link for user"""
        return f"https://yourwebsite.com/download?ref={user_id}"
    
    def track_share(self, user_id, platform, content_type):
        """Track content sharing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO viral_shares (user_id, platform, content_type, share_count, created_at)
            VALUES (?, ?, ?, 1, ?)
        ''', (user_id, platform, content_type, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def track_share_click(self, user_id, platform):
        """Track clicks on shared content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE viral_shares 
            SET click_count = click_count + 1 
            WHERE user_id = ? AND platform = ?
        ''', (user_id, platform))
        conn.commit()
        conn.close()
    
    def update_leaderboard(self, user_id, metric_type, metric_value):
        """Update user leaderboard position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current rank
        cursor.execute('''
            SELECT COUNT(*) + 1 FROM leaderboards 
            WHERE metric_type = ? AND metric_value > ?
        ''', (metric_type, metric_value))
        rank = cursor.fetchone()[0]
        
        # Update or insert
        cursor.execute('''
            INSERT OR REPLACE INTO leaderboards (user_id, metric_type, metric_value, rank_position, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, metric_type, metric_value, rank, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, metric_type, limit=10):
        """Get top performers for metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, metric_value, rank_position 
            FROM leaderboards 
            WHERE metric_type = ?
            ORDER BY rank_position ASC 
            LIMIT ?
        ''', (metric_type, limit))
        results = cursor.fetchall()
        conn.close()
        
        return [
            {'user_id': row[0], 'value': row[1], 'rank': row[2]}
            for row in results
        ]
    
    def create_viral_campaign(self, campaign_name, incentive):
        """Create viral marketing campaign"""
        campaigns = {
            'referral_contest': {
                'name': 'Referral Contest',
                'description': 'Refer most friends and win KES 10,000!',
                'rules': [
                    'Share your referral link',
                    'Friends must download and use the bot',
                    'Top 3 referrers win prizes',
                    'Contest runs for 30 days'
                ],
                'prizes': {
                    1: 'KES 10,000',
                    2: 'KES 5,000',
                    3: 'KES 2,000'
                }
            },
            'value_bet_challenge': {
                'name': 'Value Bet Challenge',
                'description': 'Show your winning bets and win free premium features!',
                'rules': [
                    'Share your winning value bets',
                    'Use hashtag #AIBettingBot',
                    'Most creative posts win',
                    'Weekly winners announced'
                ],
                'prizes': {
                    'weekly': '1 month premium access',
                    'monthly': '6 months premium access'
                }
            },
            'viral_content': {
                'name': 'Viral Content Creator',
                'description': 'Create viral content about the AI bot and earn commissions!',
                'rules': [
                    'Create TikTok/YouTube videos',
                    'Must include referral link',
                    'Track views and conversions',
                    'Top creators get 50% commission'
                ],
                'prizes': {
                    '1000_views': 'KES 1,000',
                    '10000_views': 'KES 10,000',
                    '100000_views': 'KES 50,000'
                }
            }
        }
        
        return campaigns.get(campaign_name, {})
    
    def generate_viral_templates(self):
        """Generate viral content templates"""
        templates = {
            'success_story': {
                'title': 'How I Made KES 5,000 with FREE AI Bot!',
                'template': """
Just discovered this FREE AI betting bot and made KES 5,000 in my first week! 🤯

The AI finds value bets I never would have spotted:
✅ Liverpool vs Chelsea - Away Win @ 4.1 (WON!)
✅ Barcelona vs Real Madrid - Home Win @ 2.8 (WON!)
✅ Man United vs Arsenal - Draw @ 3.4 (WON!)

🤖 Get the FREE bot: [YOUR_REFERRAL_LINK]
💰 Join Betika for bonus: [BETIKA_LINK]

#AI #Betting #SuccessStory #FreeMoney
                """,
                'platforms': ['twitter', 'facebook', 'instagram']
            },
            'educational': {
                'title': 'Stop Gambling, Start Investing!',
                'template': """
🎓 BETTING 101: Value Betting Explained

Most people gamble (50% chance to win)
Smart people invest (55-60% chance to win)

Value Bet = When odds > true probability

Example:
📊 AI says Team A has 65% chance
💰 Bookmaker odds imply 40% chance
✅ That's a VALUE BET!

🤖 Get AI that finds these automatically:
[YOUR_REFERRAL_LINK]

#BettingEducation #AI #Investing
                """,
                'platforms': ['twitter', 'linkedin', 'facebook']
            },
            'comparison': {
                'title': 'AI vs Human Tipsters',
                'template': """
🤖 AI vs Human Tipsters - Who Wins?

AI Betting Bot:
✅ 55-60% accuracy
✅ Analyzes 1000s of matches
✅ No emotions, pure math
✅ 100% FREE

Human Tipsters:
❌ 45-50% accuracy
❌ Limited analysis
❌ Emotional bias
❌ Expensive subscriptions

🤖 Choose the smart option:
[YOUR_REFERRAL_LINK]

#AI #Betting #Technology
                """,
                'platforms': ['twitter', 'facebook', 'instagram']
            }
        }
        
        return templates

if __name__ == "__main__":
    # Test viral features
    viral = ViralGrowthEngine()
    
    # Generate referral code
    referral_code = viral.generate_referral_code("user123")
    print(f"Referral code: {referral_code}")
    
    # Sample value bet
    sample_bet = {
        'home_team': 'Liverpool',
        'away_team': 'Chelsea',
        'recommended_outcome': 'Away Win',
        'odds': 4.1,
        'value_margin': 12.5,
        'expected_value': 0.456
    }
    
    # Generate shareable content
    twitter_content = viral.create_shareable_content("user123", [sample_bet], 'twitter')
    print("\nTwitter Content:")
    print(twitter_content['text'])
    
    # Get viral templates
    templates = viral.generate_viral_templates()
    print("\nSuccess Story Template:")
    print(templates['success_story']['template'])
    
    print("\n✅ Viral features system ready!")
