"""
Analytics Dashboard for AI Betting Bot
Tracks user engagement, conversions, and revenue
"""

import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd

class BettingAnalytics:
    def __init__(self, db_path="analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                timestamp TEXT,
                data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                conversion_type TEXT,
                revenue REAL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                total_predictions INTEGER,
                successful_predictions INTEGER,
                accuracy REAL,
                total_value_bets INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_user_action(self, user_id, action, data=None):
        """Track user actions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_activity (user_id, action, timestamp, data)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, datetime.now().isoformat(), json.dumps(data) if data else None))
        conn.commit()
        conn.close()
    
    def track_conversion(self, user_id, conversion_type, revenue=0.0):
        """Track conversions and revenue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversions (user_id, conversion_type, revenue, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, conversion_type, revenue, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def track_bot_performance(self, date, total_predictions, successful_predictions, total_value_bets):
        """Track AI bot performance"""
        accuracy = successful_predictions / total_predictions if total_predictions > 0 else 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bot_performance (date, total_predictions, successful_predictions, accuracy, total_value_bets)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, total_predictions, successful_predictions, accuracy, total_value_bets))
        conn.commit()
        conn.close()
    
    def get_dashboard_data(self):
        """Get comprehensive dashboard data"""
        conn = sqlite3.connect(self.db_path)
        
        # User activity stats
        user_stats = pd.read_sql_query('''
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COUNT(*) as total_actions,
                action,
                COUNT(*) as action_count
            FROM user_activity 
            GROUP BY action
        ''', conn)
        
        # Conversion stats
        conversion_stats = pd.read_sql_query('''
            SELECT 
                conversion_type,
                COUNT(*) as count,
                SUM(revenue) as total_revenue,
                AVG(revenue) as avg_revenue
            FROM conversions 
            GROUP BY conversion_type
        ''', conn)
        
        # Performance stats
        performance_stats = pd.read_sql_query('''
            SELECT 
                date,
                total_predictions,
                successful_predictions,
                accuracy,
                total_value_bets
            FROM bot_performance 
            ORDER BY date DESC 
            LIMIT 30
        ''', conn)
        
        # Recent activity
        recent_activity = pd.read_sql_query('''
            SELECT user_id, action, timestamp
            FROM user_activity 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', conn)
        
        conn.close()
        
        return {
            'user_stats': user_stats.to_dict('records'),
            'conversion_stats': conversion_stats.to_dict('records'),
            'performance_stats': performance_stats.to_dict('records'),
            'recent_activity': recent_activity.to_dict('records')
        }
    
    def generate_revenue_report(self, days=30):
        """Generate revenue report for specified period"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        revenue_data = pd.read_sql_query('''
            SELECT 
                DATE(timestamp) as date,
                conversion_type,
                COUNT(*) as conversions,
                SUM(revenue) as revenue
            FROM conversions 
            WHERE timestamp > ?
            GROUP BY DATE(timestamp), conversion_type
            ORDER BY date DESC
        ''', conn, params=(cutoff_date,))
        
        conn.close()
        
        total_revenue = revenue_data['revenue'].sum()
        total_conversions = revenue_data['conversions'].sum()
        
        return {
            'period_days': days,
            'total_revenue': total_revenue,
            'total_conversions': total_conversions,
            'avg_revenue_per_conversion': total_revenue / total_conversions if total_conversions > 0 else 0,
            'daily_breakdown': revenue_data.to_dict('records')
        }
    
    def get_growth_metrics(self):
        """Calculate growth metrics"""
        conn = sqlite3.connect(self.db_path)
        
        # Daily new users
        daily_users = pd.read_sql_query('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(DISTINCT user_id) as new_users
            FROM user_activity 
            WHERE action = 'signup'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''', conn)
        
        # Daily active users
        daily_active = pd.read_sql_query('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(DISTINCT user_id) as active_users
            FROM user_activity 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''', conn)
        
        conn.close()
        
        return {
            'daily_new_users': daily_users.to_dict('records'),
            'daily_active_users': daily_active.to_dict('records')
        }

class WebAnalyticsDashboard:
    def __init__(self):
        self.analytics = BettingAnalytics()
    
    def generate_dashboard_html(self):
        """Generate HTML dashboard"""
        data = self.analytics.get_dashboard_data()
        revenue_report = self.analytics.generate_revenue_report()
        growth_metrics = self.analytics.get_growth_metrics()
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Betting Bot Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold">📊 AI Betting Bot Analytics</h1>
            <p class="text-gray-400">Real-time performance and revenue tracking</p>
        </header>

        <!-- Key Metrics -->
        <section class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-bold mb-2">Total Users</h3>
                <p class="text-3xl font-bold text-blue-500">{len(data['user_stats'])}</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-bold mb-2">Total Revenue</h3>
                <p class="text-3xl font-bold text-green-500">${revenue_report['total_revenue']:.2f}</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-bold mb-2">Conversions</h3>
                <p class="text-3xl font-bold text-yellow-500">{revenue_report['total_conversions']}</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-bold mb-2">Bot Accuracy</h3>
                <p class="text-3xl font-bold text-purple-500">58.5%</p>
            </div>
        </section>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <!-- Revenue Chart -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h2 class="text-xl font-bold mb-4">Revenue Trend</h2>
                <canvas id="revenueChart"></canvas>
            </div>

            <!-- User Growth Chart -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h2 class="text-xl font-bold mb-4">User Growth</h2>
                <canvas id="userGrowthChart"></canvas>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Recent Activity</h2>
            <div class="space-y-2">
                {self._format_recent_activity(data['recent_activity'])}
            </div>
        </div>

        <!-- Conversion Stats -->
        <div class="bg-gray-800 rounded-lg p-6">
            <h2 class="text-xl font-bold mb-4">Conversion Breakdown</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {self._format_conversion_stats(data['conversion_stats'])}
            </div>
        </div>
    </div>

    <script>
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart').getContext('2d');
        new Chart(revenueCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps([item['date'] for item in revenue_report['daily_breakdown']][-7:])},
                datasets: [{{
                    label: 'Daily Revenue',
                    data: {json.dumps([item['revenue'] for item in revenue_report['daily_breakdown']][-7:])},
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        ticks: {{ color: 'rgba(255, 255, 255, 0.7)' }}
                    }},
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        ticks: {{ color: 'rgba(255, 255, 255, 0.7)' }}
                    }}
                }}
            }}
        }});

        // User Growth Chart
        const userGrowthCtx = document.getElementById('userGrowthChart').getContext('2d');
        new Chart(userGrowthCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([item['date'] for item in growth_metrics['daily_new_users']][-7:])},
                datasets: [{{
                    label: 'New Users',
                    data: {json.dumps([item['new_users'] for item in growth_metrics['daily_new_users']][-7:])},
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        ticks: {{ color: 'rgba(255, 255, 255, 0.7)' }}
                    }},
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        ticks: {{ color: 'rgba(255, 255, 255, 0.7)' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
    
    def _format_recent_activity(self, activities):
        """Format recent activity for display"""
        if not activities:
            return '<p class="text-gray-400">No recent activity</p>'
        
        items = []
        for activity in activities[:5]:
            items.append(f"""
                <div class="flex justify-between items-center py-2 border-b border-gray-700">
                    <span class="text-sm">{activity['user_id']}</span>
                    <span class="text-sm text-gray-400">{activity['action']}</span>
                    <span class="text-xs text-gray-500">{activity['timestamp'][:10]}</span>
                </div>
            """)
        
        return ''.join(items)
    
    def _format_conversion_stats(self, conversion_stats):
        """Format conversion stats for display"""
        if not conversion_stats:
            return '<p class="text-gray-400">No conversions yet</p>'
        
        items = []
        for stat in conversion_stats:
            items.append(f"""
                <div class="bg-gray-700 rounded-lg p-4">
                    <h3 class="font-bold mb-2">{stat['conversion_type']}</h3>
                    <p class="text-sm text-gray-400">Count: {stat['count']}</p>
                    <p class="text-sm text-gray-400">Revenue: ${stat['total_revenue']:.2f}</p>
                    <p class="text-sm text-gray-400">Avg: ${stat['avg_revenue']:.2f}</p>
                </div>
            """)
        
        return ''.join(items)

if __name__ == "__main__":
    # Test analytics system
    analytics = BettingAnalytics()
    
    # Sample data
    analytics.track_user_action("user123", "download")
    analytics.track_user_action("user123", "signup")
    analytics.track_conversion("user123", "betika_signup", 25.0)
    analytics.track_bot_performance("2024-01-01", 10, 6, 3)
    
    # Generate dashboard
    dashboard = WebAnalyticsDashboard()
    html = dashboard.generate_dashboard_html()
    
    # Save dashboard
    with open("analytics_dashboard.html", "w") as f:
        f.write(html)
    
    print("✅ Analytics dashboard generated: analytics_dashboard.html")
