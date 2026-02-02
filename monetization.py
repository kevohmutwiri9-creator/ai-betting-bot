"""
Monetization Module for AI Betting Bot
Handles affiliate links, tracking, and revenue generation
"""

import json
import uuid
from datetime import datetime
import hashlib
import sqlite3
from config import BETIKA_AFFILIATE_ID, BETIKA_BASE_URL, DOWNLOAD_LINK

class BetikaAffiliateManager:
    def __init__(self, db_path="affiliate_data.db"):
        self.db_path = db_path
        self.affiliate_id = BETIKA_AFFILIATE_ID
        self.betika_base_url = BETIKA_BASE_URL
        self.init_database()
    
    def init_database(self):
        """Initialize affiliate tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                affiliate_link TEXT,
                created_at TEXT,
                clicks INTEGER DEFAULT 0,
                signups INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                referral_id TEXT,
                conversion_type TEXT,
                revenue REAL,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_affiliate_link(self, user_id):
        """Generate unique affiliate link for user"""
        # Create unique tracking code
        tracking_code = hashlib.md5(f"{user_id}_{datetime.now()}".encode()).hexdigest()[:8]
        
        affiliate_url = f"{self.betika_base_url}/register?aff_id={self.affiliate_id}&track={tracking_code}"
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, affiliate_link, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, affiliate_url, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return affiliate_url
    
    def track_click(self, user_id):
        """Track affiliate link click"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET clicks = clicks + 1 WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def track_signup(self, user_id, referral_id, revenue=0.0):
        """Track successful signup and revenue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update user stats
        cursor.execute('''
            UPDATE users SET signups = signups + 1, revenue = revenue + revenue WHERE user_id = ?
        ''', (user_id,))
        
        # Record conversion
        cursor.execute('''
            INSERT INTO conversions (user_id, referral_id, conversion_type, revenue, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, referral_id, "signup", revenue, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        """Get user's affiliate statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT clicks, signups, revenue FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'clicks': result[0],
                'signups': result[1],
                'revenue': result[2]
            }
        return {'clicks': 0, 'signups': 0, 'revenue': 0.0}
    
    def get_total_stats(self):
        """Get overall affiliate statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(clicks), SUM(signups), SUM(revenue), COUNT(*) FROM users
        ''')
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_clicks': result[0] or 0,
            'total_signups': result[1] or 0,
            'total_revenue': result[2] or 0.0,
            'total_users': result[3] or 0
        }

class MarketingManager:
    def __init__(self):
        self.affiliate_manager = BetikaAffiliateManager()
    
    def generate_marketing_message(self, user_id, value_bets):
        """Generate marketing message with affiliate links"""
        affiliate_link = self.affiliate_manager.generate_affiliate_link(user_id)
        
        message = f"""
🎯 **FREE AI Betting Bot - Daily Value Bets!**

Found {len(value_bets)} value bets today:

"""
        
        for i, bet in enumerate(value_bets[:3], 1):
            message += f"""
{i}. **{bet['home_team']} vs {bet['away_team']}**
   💎 {bet['recommended_outcome']} @ {bet['odds']}
   📈 Value: +{bet['value_margin']}%
   🎲 EV: {bet['expected_value']}
"""
        
        message += f"""
🚀 **Get More Bets + Sign Up Bonus:**
{affiliate_link}

💰 **Why Join Betika:**
• Welcome bonus up to KES 1000
• Live betting on all matches
• Fast withdrawals
• Mobile app available

⚠️ *18+ only. Bet responsibly.*
"""
        
        return message
    
    def generate_landing_page_content(self):
        """Generate landing page content"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Free AI Betting Bot - Beat the Bookies!</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-12">
            <h1 class="text-4xl font-bold mb-4">🤖 Free AI Betting Bot</h1>
            <p class="text-xl text-gray-400">Find value bets using artificial intelligence</p>
        </header>

        <section class="max-w-4xl mx-auto">
            <div class="bg-gray-800 rounded-lg p-8 mb-8">
                <h2 class="text-2xl font-bold mb-4">🎯 Today's Value Bets</h2>
                <div id="valueBets" class="space-y-4">
                    <!-- Value bets will be loaded here -->
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <div class="bg-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-bold mb-4">🤖 How It Works</h3>
                    <ul class="space-y-2">
                        <li>✅ AI analyzes thousands of matches</li>
                        <li>✅ Finds mathematical edges in odds</li>
                        <li>✅ Identifies value betting opportunities</li>
                        <li>✅ Provides data-driven predictions</li>
                    </ul>
                </div>
                <div class="bg-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-bold mb-4">💰 Why Join Betika</h3>
                    <ul class="space-y-2">
                        <li>✅ Welcome bonus up to KES 1000</li>
                        <li>✅ Live betting on all sports</li>
                        <li>✅ Fast & secure payments</li>
                        <li>✅ Mobile app for betting anywhere</li>
                    </ul>
                </div>
            </div>

            <div class="text-center">
                <a href="https://www.betika.com/register?aff_id=YOUR_AFFILIATE_ID" 
                   class="bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-8 rounded-lg text-xl transition">
                    🚀 Join Betika & Get Bonus
                </a>
                <p class="text-gray-400 mt-4">18+ only. Please bet responsibly.</p>
            </div>
        </section>
    </div>
</body>
</html>
"""
    
    def create_viral_content(self, value_bets):
        """Create shareable content for social media"""
        if not value_bets:
            return None
        
        top_bet = max(value_bets, key=lambda x: x['expected_value'])
        
        content = f"""
🎯 **AI Found Value Bet!**

🏆 {top_bet['home_team']} vs {top_bet['away_team']}
💎 {top_bet['recommended_outcome']} @ {top_bet['odds']}
📈 Value: +{top_bet['value_margin']}%
🎲 Expected Value: {top_bet['expected_value']}

🤖 Get FREE AI betting bot:
[Your Download Link]

💰 Join Betika for bonus:
[Affiliate Link]

#AI #Betting #SportsBetting #ValueBet
"""
        
        return content

class RevenueTracker:
    def __init__(self):
        self.affiliate_manager = BetikaAffiliateManager()
    
    def calculate_potential_revenue(self, users_count, conversion_rate=0.1, avg_revenue=25.0):
        """Calculate potential revenue projections"""
        projected_signups = users_count * conversion_rate
        projected_revenue = projected_signups * avg_revenue
        
        return {
            'users': users_count,
            'conversion_rate': conversion_rate,
            'projected_signups': int(projected_signups),
            'avg_revenue_per_user': avg_revenue,
            'projected_revenue': projected_revenue,
            'monthly_revenue': projected_revenue / 12
        }
    
    def generate_revenue_report(self):
        """Generate comprehensive revenue report"""
        stats = self.affiliate_manager.get_total_stats()
        
        # Calculate projections
        projections = self.calculate_potential_revenue(
            stats['total_users'] * 10,  # Assume 10x growth
            0.1,  # 10% conversion
            25.0  # $25 avg revenue per signup
        )
        
        report = f"""
📊 **Revenue Report**

**Current Stats:**
• Total Users: {stats['total_users']}
• Total Clicks: {stats['total_clicks']}
• Total Signups: {stats['total_signups']}
• Total Revenue: ${stats['total_revenue']:.2f}

**Projections (12 months):**
• Projected Users: {projections['users']}
• Projected Signups: {projections['projected_signups']}
• Projected Revenue: ${projections['projected_revenue']:.2f}
• Monthly Revenue: ${projections['monthly_revenue']:.2f}

**Growth Strategy:**
• Scale user acquisition through viral marketing
• Optimize conversion rate with better landing pages
• Increase average revenue with premium features
"""
        
        return report

if __name__ == "__main__":
    # Test monetization system
    marketing = MarketingManager()
    revenue_tracker = RevenueTracker()
    
    # Sample value bets
    sample_bets = [
        {
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'recommended_outcome': 'Away Win',
            'odds': 4.1,
            'value_margin': 12.5,
            'expected_value': 0.456
        }
    ]
    
    # Generate marketing message
    message = marketing.generate_marketing_message("test_user", sample_bets)
    print("Marketing Message:")
    print(message)
    
    # Generate revenue report
    report = revenue_tracker.generate_revenue_report()
    print("\n" + report)
