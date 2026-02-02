"""
Marketing Materials Generator for AI Betting Bot
Creates viral content, social media posts, and promotional materials
"""

import json
from datetime import datetime
from config import DOWNLOAD_LINK

class MarketingContentGenerator:
    def __init__(self):
        self.brand_name = "AI Betting Bot"
        self.affiliate_link = "https://www.betika.com/register?aff_id=YOUR_AFFILIATE_ID"
        self.download_link = DOWNLOAD_LINK
    
    def generate_twitter_posts(self, value_bets):
        """Generate viral Twitter content"""
        posts = []
        
        if value_bets:
            top_bet = max(value_bets, key=lambda x: x['expected_value'])
            
            post1 = f"""
🤖 AI FOUND VALUE BET! 🎯

🏆 {top_bet['home_team']} vs {top_bet['away_team']}
💎 {top_bet['recommended_outcome']} @ {top_bet['odds']}
📈 Value: +{top_bet['value_margin']}%
🎲 EV: {top_bet['expected_value']}

📥 Get FREE AI bot: {self.download_link}
💰 Betika bonus: {self.affiliate_link}

#AI #Betting #SportsBetting #ValueBet #Football
            """
            
            post2 = f"""
📊 BEAT THE BOOKIES WITH MATH! 📊

Our AI analyzes 1000s of matches to find:
✅ Mathematical edges in odds
✅ 55-60% accuracy rate
✅ Long-term profit potential

🤖 FREE DOWNLOAD: {self.download_link}

Don't gamble - invest with data! 🎯

#SportsBetting #AI #DataScience #BettingTips
            """
            
            posts = [post1.strip(), post2.strip()]
        
        # Educational posts
        posts.append(f"""
🎓 BETTING 101: Value Betting Explained 🎓

Value Bet = When odds > true probability

Example:
📊 AI says Team A has 65% chance
💰 Bookmaker odds imply 40% chance
✅ That's a VALUE BET!

🤖 Get AI that finds these automatically:
{self.download_link}

#BettingEducation #SportsBetting #AI
        """.strip())
        
        return posts
    
    def _format_bets_for_instagram(self, bets):
        """Format bets for Instagram caption"""
        lines = []
        for bet in bets:
            lines.append(f'✅ {bet["home_team"]} vs {bet["away_team"]} - {bet["recommended_outcome"]} @ {bet["odds"]}')
        return '\n'.join(lines)
    
    def generate_instagram_content(self, value_bets):
        """Generate Instagram-ready content"""
        content = []
        
        # Story template
        story = {
            'type': 'story',
            'background': 'gradient_blue_green',
            'text': f"""🤖 AI BETTING BOT
FREE DOWNLOAD!

Today's Top Pick:
{value_bets[0]['home_team']} vs {value_bets[0]['away_team']}
{value_bets[0]['recommended_outcome']} @ {value_bets[0]['odds']}

Value: +{value_bets[0]['value_margin']}%

📥 Link in Bio!
#AI #Betting #SportsBetting""",
            'cta': 'SWIPE UP TO DOWNLOAD'
        }
        
        # Post template
        post = {
            'type': 'post',
            'image_caption': f"""🎯 AI vs BOOKMAKERS! Who wins?

Our AI found {len(value_bets)} value bets today:
{self._format_bets_for_instagram(value_bets[:3])}

🤖 Get the FREE AI bot that finds these edges!
Link in bio! 📥

💰 Join Betika for welcome bonus:
{self.affiliate_link}

#AI #Betting #SportsBetting #ValueBet #FootballBetting""",
            'hashtags': ['#AI', '#Betting', '#SportsBetting', '#ValueBet', '#Football', '#FreeBettingTips']
        }
        
        content = [story, post]
        return content
    
    def generate_tiktok_scripts(self, value_bets):
        """Generate TikTok video scripts"""
        scripts = []
        
        # Viral hook script
        script1 = {
            'title': 'AI Finds FREE Money in Betting!',
            'duration': '15 seconds',
            'scenes': [
                {'time': 0, 'text': 'Bookmakers make mistakes...', 'visual': 'person looking confused'},
                {'time': 3, 'text': 'Our AI finds them!', 'visual': 'computer screen with code'},
                {'time': 6, 'text': f'Today: {value_bets[0]["home_team"]} vs {value_bets[0]["away_team"]}', 'visual': 'team logos'},
                {'time': 9, 'text': f'Value: +{value_bets[0]["value_margin"]}%', 'visual': 'green arrow up'},
                {'time': 12, 'text': 'FREE AI BOT LINK IN BIO!', 'visual': 'phone showing download'},
            ],
            'audio': 'trending_viral_sound',
            'hashtags': ['#AI', '#Betting', '#SportsBetting', '#FreeMoney', '#Viral']
        }
        
        # Educational script
        script2 = {
            'title': 'How to NEVER Lose Betting Long-term',
            'duration': '20 seconds',
            'scenes': [
                {'time': 0, 'text': 'Stop gambling...', 'visual': 'person losing money'},
                {'time': 4, 'text': 'Start value betting!', 'visual': 'person winning'},
                {'time': 8, 'text': 'Find odds > true probability', 'visual': 'math equation'},
                {'time': 12, 'text': 'Our AI does this automatically', 'visual': 'AI interface'},
                {'time': 16, 'text': 'FREE DOWNLOAD LINK IN BIO!', 'visual': 'download button'},
            ],
            'audio': 'educational_trending_sound',
            'hashtags': ['#BettingTips', '#SportsBetting', '#AI', '#ValueBetting']
        }
        
        scripts = [script1, script2]
        return scripts
    
    def generate_youtube_content(self, value_bets):
        """Generate YouTube video ideas and scripts"""
        content = []
        
        # Video idea 1: Review/Testing
        video1 = {
            'title': 'Testing FREE AI Betting Bot for 7 Days - Results SHOCKING!',
            'description': f"""
I tested a FREE AI betting bot for 7 days straight...
The results will surprise you! 🤯

🤖 Get the AI Bot: {self.download_link}
💰 Join Betika: {self.affiliate_link}

In this video:
- Day by day results
- How the AI works
- Profit/loss breakdown
- Is it actually profitable?

TIMESTAMPS:
0:00 - Introduction
1:30 - How AI Betting Works
3:00 - Day 1 Results
5:00 - Day 3 Results
7:00 - Day 7 Results
9:00 - Final Results
10:30 - Conclusion

#AI #Betting #SportsBetting #Testing #Review
            """,
            'tags': ['AI betting', 'sports betting', 'betting bot', 'betting tips', 'football betting'],
            'thumbnail_text': 'AI BOT TESTED - 7 DAYS!'
        }
        
        # Video idea 2: Educational
        video2 = {
            'title': 'How to Make Money Betting with MATHEMATICS (Not Luck)',
            'description': f"""
Stop gambling and start investing! Learn how professional bettors use mathematics to beat bookmakers.

🤖 AI Bot that does the math: {self.download_link}
💰 Start with bonus: {self.affiliate_link}

In this educational video:
- What are value bets?
- How to calculate expected value
- Bankroll management
- Long-term betting strategy

Chapters:
0:00 - Gambling vs Investing
2:00 - Understanding Odds
4:00 - Finding Value Bets
6:00 - Expected Value Explained
8:00 - Bankroll Management
10:00 - AI Tools for Betting

#BettingEducation #SportsBetting #Mathematics #Investing
            """,
            'tags': ['betting education', 'sports betting', 'value betting', 'mathematics', 'investing'],
            'thumbnail_text': 'MATH > LUCK IN BETTING!'
        }
        
        content = [video1, video2]
        return content
    
    def generate_facebook_ads(self, value_bets):
        """Generate Facebook ad copy"""
        ads = []
        
        # Direct response ad
        ad1 = {
            'headline': 'FREE AI Betting Bot - Find Value Bets Automatically',
            'text': f"""
🤖 Our AI analyzes 1000s of matches to find mathematical edges in betting odds.

✅ 55-60% accuracy rate
✅ 3-5 value bets daily
✅ Completely FREE to use
✅ Works with all bookmakers

Today's top pick: {value_bets[0]['home_team']} vs {value_bets[0]['away_team']}
{value_bets[0]['recommended_outcome']} @ {value_bets[0]['odds']} (Value: +{value_bets[0]['value_margin']}%)

📥 Download FREE now: {self.download_link}

Limited spots available - download before it's too late!
            """,
            'image': 'ai_bot_interface',
            'cta_button': 'Download Now',
            'target_audience': 'Sports fans, betting enthusiasts, 18-45'
        }
        
        # Benefits-focused ad
        ad2 = {
            'headline': 'Stop Gambling - Start Investing with AI',
            'text': f"""
Tired of losing bets? It's time to use data instead of luck.

Our AI betting bot helps you:
✅ Find mathematical edges (55-60% accuracy)
✅ Manage your bankroll properly
✅ Make long-term profitable decisions
✅ Get 3-5 value bets daily

💰 Join Betika with KES 1000 bonus: {self.affiliate_link}
🤖 Download FREE AI bot: {self.download_link}

Over 10,000 users are already using AI to beat the bookies!

#SportsBetting #AI #ValueBetting
            """,
            'image': 'profit_chart',
            'cta_button': 'Learn More',
            'target_audience': 'People interested in sports betting, side income'
        }
        
        ads = [ad1, ad2]
        return ads
    
    def _format_bets_for_email(self, bets):
        """Format bets for email"""
        lines = []
        for bet in bets:
            lines.append(f'• {bet["home_team"]} vs {bet["away_team"]} - {bet["recommended_outcome"]} @ {bet["odds"]} (Value: +{bet["value_margin"]}%)')
        return '\n'.join(lines)
    
    def generate_email_campaign(self, value_bets):
        """Generate email marketing campaign"""
        emails = []
        
        # Welcome email
        welcome_email = {
            'subject': '🤖 Your FREE AI Betting Bot is Ready!',
            'body': f"""
Hi [Name],

Your FREE AI betting bot is ready to download! 🎯

Here's what you get:
✅ Daily value bet predictions (55-60% accuracy)
✅ Mathematical edge analysis
✅ Bankroll management tools
✅ Completely FREE - no hidden fees

Today's AI picks:
{self._format_bets_for_email(value_bets[:3])}

📥 Download your bot here: {self.download_link}

💰 Don't forget to join Betika for your welcome bonus:
{self.affiliate_link}

Happy betting!
AI Betting Bot Team

P.S. This is completely free - no credit card required!
            """
        }
        
        # Daily picks email
        daily_email = {
            'subject': f'🎯 {len(value_bets)} AI Value Bets Found Today!',
            'body': f"""
Hi [Name],

Our AI found {len(value_bets)} value betting opportunities today:

{self._format_detailed_bets_for_email(value_bets[:3])}

Ready to bet? Join Betika for the best odds and welcome bonus:
{self.affiliate_link}

Your AI bot updates automatically - just keep it running!

Good luck,
AI Betting Bot Team
            """
        }
        
        emails = [welcome_email, daily_email]
        return emails
    
    def _format_detailed_bets_for_email(self, bets):
        """Format detailed bets for email"""
        lines = []
        for bet in bets:
            lines.append(f"""{bet['home_team']} vs {bet['away_team']}
💎 Pick: {bet['recommended_outcome']} @ {bet['odds']}
📈 Value: +{bet['value_margin']}%
🎲 Expected Value: {bet['expected_value']}""")
        return '\n'.join(lines)
    
    def generate_viral_meme_content(self):
        """Generate meme templates and captions"""
        memes = [
            {
                'template': 'distracted_boyfriend',
                'text': {
                    'boyfriend': 'Bettors',
                    'girlfriend': 'Gambling with luck',
                    'other_girl': 'Using AI betting bot'
                }
            },
            {
                'template': 'two_buttons',
                'text': {
                    'left_button': 'Bet on gut feeling',
                    'right_button': 'Use AI mathematical analysis'
                }
            },
            {
                'template': 'expanding_brain',
                'text': {
                    'level1': 'Betting randomly',
                    'level2': 'Following tipsters',
                    'level3': 'Basic analysis',
                    'level4': 'AI value betting'
                }
            }
        ]
        
        captions = [
            "Stop gambling. Start investing with data. 🤖",
            "55-60% accuracy > 50% coin flip. Do the math. 📊",
            "Bookmakers have 5-10% margin. AI finds when they're wrong. 💎",
            "Free AI bot that finds mathematical edges. Link in bio! 🎯"
        ]
        
        return {'memes': memes, 'captions': captions}

if __name__ == "__main__":
    # Test marketing content generation
    generator = MarketingContentGenerator()
    
    # Sample value bets
    sample_bets = [
        {
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'recommended_outcome': 'Away Win',
            'odds': 4.1,
            'value_margin': 12.5,
            'expected_value': 0.456
        },
        {
            'home_team': 'Barcelona',
            'away_team': 'Real Madrid',
            'recommended_outcome': 'Home Win',
            'odds': 2.8,
            'value_margin': 9.5,
            'expected_value': 0.186
        }
    ]
    
    # Generate all content
    twitter_posts = generator.generate_twitter_posts(sample_bets)
    print("Twitter Posts:")
    for i, post in enumerate(twitter_posts, 1):
        print(f"\n--- Post {i} ---")
        print(post)
    
    print("\n" + "="*50 + "\n")
    
    facebook_ads = generator.generate_facebook_ads(sample_bets)
    print("Facebook Ads:")
    for i, ad in enumerate(facebook_ads, 1):
        print(f"\n--- Ad {i} ---")
        print(f"Headline: {ad['headline']}")
        print(f"Text: {ad['text'][:200]}...")
    
    print("\n✅ Marketing content generated successfully!")
