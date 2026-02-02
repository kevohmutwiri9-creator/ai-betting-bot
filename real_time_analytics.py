"""
Real-time Analytics Dashboard for AI Betting Bot
Provides live statistics and performance tracking
"""

import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict

class RealTimeAnalytics:
    def __init__(self, db_path="analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize real-time analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS real_time_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TEXT,
                user_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                total_bets INTEGER,
                winning_bets INTEGER,
                total_stake REAL,
                total_returns REAL,
                roi REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_user_action(self, user_id, action, details=None):
        """Track user activity in real-time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_activity (user_id, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, json.dumps(details) if details else None, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def update_metric(self, metric_name, value, user_id=None):
        """Update real-time metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO real_time_stats (metric_name, metric_value, timestamp, user_id)
            VALUES (?, ?, ?, ?)
        ''', (metric_name, value, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def get_live_stats(self):
        """Get current live statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active users in last 5 minutes
        five_minutes_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM user_activity 
            WHERE timestamp > ?
        ''', (five_minutes_ago,))
        active_users = cursor.fetchone()[0]
        
        # Get today's activity
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM user_activity 
            WHERE DATE(timestamp) = ?
        ''', (today,))
        today_actions = cursor.fetchone()[0]
        
        # Get total users
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_activity')
        total_users = cursor.fetchone()[0]
        
        # Get recent metrics
        cursor.execute('''
            SELECT metric_name, AVG(metric_value) as avg_value
            FROM real_time_stats 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY metric_name
        ''')
        recent_metrics = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'active_users': active_users,
            'today_actions': today_actions,
            'total_users': total_users,
            'recent_metrics': recent_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_user_activity_heatmap(self, hours=24):
        """Get user activity heatmap data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cursor.execute('''
            SELECT DATE(timestamp) as date, 
                   strftime('%H', timestamp) as hour,
                   COUNT(*) as actions
            FROM user_activity 
            WHERE timestamp > ?
            GROUP BY date, hour
            ORDER BY date, hour
        ''', (since,))
        
        heatmap_data = defaultdict(lambda: defaultdict(int))
        for date, hour, actions in cursor.fetchall():
            heatmap_data[date][int(hour)] = actions
        
        conn.close()
        return dict(heatmap_data)
    
    def get_performance_trends(self, days=30):
        """Get performance trends over time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('''
            SELECT date, 
                   SUM(total_bets) as bets,
                   SUM(winning_bets) as wins,
                   SUM(total_stake) as stake,
                   SUM(total_returns) as returns,
                   AVG(roi) as avg_roi
            FROM performance_metrics 
            WHERE date >= ?
            GROUP BY date
            ORDER BY date
        ''', (since.split('T')[0],))
        
        trends = []
        for row in cursor.fetchall():
            trends.append({
                'date': row[0],
                'bets': row[1],
                'wins': row[2],
                'stake': row[3],
                'returns': row[4],
                'roi': row[5],
                'win_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0
            })
        
        conn.close()
        return trends
    
    def get_top_performers(self, limit=10):
        """Get top performing users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, 
                   COUNT(*) as actions,
                   COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM user_activity 
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY user_id
            ORDER BY actions DESC
            LIMIT ?
        ''', (limit,))
        
        performers = []
        for user_id, actions, active_days in cursor.fetchall():
            performers.append({
                'user_id': user_id,
                'actions': actions,
                'active_days': active_days,
                'avg_actions_per_day': actions / active_days if active_days > 0 else 0
            })
        
        conn.close()
        return performers
    
    def generate_real_time_report(self):
        """Generate comprehensive real-time analytics report"""
        live_stats = self.get_live_stats()
        heatmap = self.get_user_activity_heatmap()
        trends = self.get_performance_trends()
        performers = self.get_top_performers()
        
        return {
            'live_stats': live_stats,
            'activity_heatmap': heatmap,
            'performance_trends': trends,
            'top_performers': performers,
            'generated_at': datetime.now().isoformat()
        }

# Flask integration
from flask import Blueprint, jsonify
from auth import require_auth

analytics_bp = Blueprint('analytics', __name__)
real_time_analytics = RealTimeAnalytics()

@analytics_bp.route('/api/analytics/live')
@require_auth
def get_live_analytics():
    """Get real-time analytics data"""
    try:
        report = real_time_analytics.generate_real_time_report()
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/api/analytics/track', methods=['POST'])
@require_auth
def track_analytics():
    """Track user analytics event"""
    try:
        data = request.get_json()
        user_id = g.current_user['user_id']
        action = data.get('action')
        details = data.get('details')
        
        real_time_analytics.track_user_action(user_id, action, details)
        
        return jsonify({
            'success': True,
            'message': 'Analytics tracked successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
