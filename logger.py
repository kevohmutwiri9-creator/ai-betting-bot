"""
Logging and monitoring utilities for AI Betting Bot
"""

import logging
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, g
import sqlite3
from pathlib import Path

class BettingLogger:
    """Centralized logging system for the betting bot"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure different loggers
        self.setup_loggers()
        
        # Initialize database for monitoring
        self.init_monitoring_db()
    
    def setup_loggers(self):
        """Setup different loggers for various components"""
        
        # Main application logger
        self.app_logger = logging.getLogger('betting_app')
        self.app_logger.setLevel(logging.INFO)
        
        # API request logger
        self.api_logger = logging.getLogger('betting_api')
        self.api_logger.setLevel(logging.INFO)
        
        # Security logger
        self.security_logger = logging.getLogger('betting_security')
        self.security_logger.setLevel(logging.WARNING)
        
        # Performance logger
        self.perf_logger = logging.getLogger('betting_performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('betting_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Create handlers
        self.create_file_handlers()
        
        # Prevent propagation to root logger
        for logger in [self.app_logger, self.api_logger, self.security_logger, 
                      self.perf_logger, self.error_logger]:
            logger.propagate = False
    
    def create_file_handlers(self):
        """Create file handlers for different log types"""
        
        # Application logs
        app_handler = logging.FileHandler(self.log_dir / 'app.log')
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.app_logger.addHandler(app_handler)
        
        # API logs
        api_handler = logging.FileHandler(self.log_dir / 'api.log')
        api_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(method)s - %(endpoint)s - %(user_id)s - %(ip)s - %(response_time)s - %(status)s'
        ))
        self.api_logger.addHandler(api_handler)
        
        # Security logs
        security_handler = logging.FileHandler(self.log_dir / 'security.log')
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(event_type)s - %(user_id)s - %(ip)s - %(details)s'
        ))
        self.security_logger.addHandler(security_handler)
        
        # Performance logs
        perf_handler = logging.FileHandler(self.log_dir / 'performance.log')
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(operation)s - %(duration)s - %(memory_mb)s - %(details)s'
        ))
        self.perf_logger.addHandler(perf_handler)
        
        # Error logs
        error_handler = logging.FileHandler(self.log_dir / 'errors.log')
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
        ))
        self.error_logger.addHandler(error_handler)
        
        # Console handler for development
        if os.getenv('DEBUG_MODE', 'False').lower() == 'true':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.app_logger.addHandler(console_handler)
    
    def init_monitoring_db(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                endpoint TEXT,
                method TEXT,
                user_id TEXT,
                ip_address TEXT,
                response_time REAL,
                status_code INTEGER,
                user_agent TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS betting_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id TEXT,
                operation TEXT,
                league TEXT,
                matches_analyzed INTEGER,
                value_bets_found INTEGER,
                success_rate REAL,
                processing_time REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                active_users INTEGER,
                total_requests INTEGER
            )
        ''')
        
        # Add indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_timestamp ON api_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_betting_timestamp ON betting_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)')
        
        conn.commit()
        conn.close()
    
    def log_api_request(self, endpoint: str, method: str, user_id: Optional[str], 
                       ip_address: str, response_time: float, status_code: int):
        """Log API request metrics"""
        self.api_logger.info(
            f"{method} {endpoint} - User: {user_id} - IP: {ip_address} - "
            f"Time: {response_time:.3f}s - Status: {status_code}",
            extra={
                'method': method,
                'endpoint': endpoint,
                'user_id': user_id,
                'ip': ip_address,
                'response_time': f"{response_time:.3f}",
                'status': status_code
            }
        )
        
        # Store in database
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO api_metrics 
            (timestamp, endpoint, method, user_id, ip_address, response_time, status_code, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            endpoint,
            method,
            user_id,
            ip_address,
            response_time,
            status_code,
            request.headers.get('User-Agent', '')[:255] if request else ''
        ))
        conn.commit()
        conn.close()
    
    def log_security_event(self, event_type: str, user_id: Optional[str], 
                          ip_address: str, details: str):
        """Log security events"""
        self.security_logger.warning(
            f"{event_type} - User: {user_id} - IP: {ip_address} - {details}",
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'ip': ip_address,
                'details': details
            }
        )
    
    def log_performance(self, operation: str, duration: float, 
                       memory_mb: float, details: str = ""):
        """Log performance metrics"""
        self.perf_logger.info(
            f"{operation} - {duration:.3f}s - {memory_mb:.1f}MB - {details}",
            extra={
                'operation': operation,
                'duration': f"{duration:.3f}",
                'memory_mb': f"{memory_mb:.1f}",
                'details': details
            }
        )
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with full context"""
        self.error_logger.error(
            f"{context}: {str(error)}",
            exc_info=True,
            extra={
                'context': context,
                'error_type': type(error).__name__
            }
        )
    
    def log_betting_operation(self, user_id: str, operation: str, league: str,
                             matches_analyzed: int, value_bets_found: int,
                             success_rate: float, processing_time: float):
        """Log betting operation metrics"""
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO betting_metrics 
            (timestamp, user_id, operation, league, matches_analyzed, value_bets_found, success_rate, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            user_id,
            operation,
            league,
            matches_analyzed,
            value_bets_found,
            success_rate,
            processing_time
        ))
        conn.commit()
        conn.close()

# Global logger instance
logger = BettingLogger()

def monitor_performance(operation_name: str = ""):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Get initial memory usage
                import psutil
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate metrics
                duration = time.time() - start_time
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = final_memory - initial_memory
                
                # Log performance
                logger.log_performance(
                    operation=operation_name or func.__name__,
                    duration=duration,
                    memory_mb=memory_delta,
                    details=f"Args: {len(args)}, Kwargs: {len(kwargs)}"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.log_error(e, f"Performance monitoring failed for {func.__name__}")
                logger.log_performance(
                    operation=operation_name or func.__name__,
                    duration=duration,
                    memory_mb=0,
                    details=f"Failed after {duration:.3f}s"
                )
                raise
        
        return wrapper
    return decorator

def log_api_call():
    """Decorator to log API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Get request info
            endpoint = request.endpoint or request.path
            method = request.method
            user_id = getattr(g, 'user_id', None)
            
            # Get IP address
            forwarded_for = request.headers.get('X-Forwarded-For')
            ip_address = forwarded_for.split(',')[0].strip() if forwarded_for else request.remote_addr
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Get status code
                status_code = 200
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                
                # Log the API call
                logger.log_api_request(
                    endpoint=endpoint,
                    method=method,
                    user_id=user_id,
                    ip_address=ip_address,
                    response_time=response_time,
                    status_code=status_code
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                logger.log_error(e, f"API call failed: {method} {endpoint}")
                logger.log_api_request(
                    endpoint=endpoint,
                    method=method,
                    user_id=user_id,
                    ip_address=ip_address,
                    response_time=response_time,
                    status_code=500
                )
                raise
        
        return wrapper
    return decorator

def log_security_event(event_type: str, details: str = ""):
    """Decorator to log security events"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user info
            user_id = getattr(g, 'user_id', None)
            
            # Get IP address
            forwarded_for = request.headers.get('X-Forwarded-For')
            ip_address = forwarded_for.split(',')[0].strip() if forwarded_for else request.remote_addr
            
            # Log the security event
            logger.log_security_event(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                details=details
            )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class MetricsCollector:
    """Collect and analyze system metrics"""
    
    @staticmethod
    def get_api_metrics(hours: int = 24) -> Dict[str, Any]:
        """Get API metrics for the last N hours"""
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                AVG(response_time) as avg_response_time,
                MAX(response_time) as max_response_time,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM api_metrics 
            WHERE timestamp > ?
        ''', (since,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'total_requests': result[0],
                'avg_response_time': round(result[1], 3) if result[1] else 0,
                'max_response_time': round(result[2], 3) if result[2] else 0,
                'error_count': result[3],
                'unique_users': result[4],
                'error_rate': round(result[3] / result[0] * 100, 2) if result[0] > 0 else 0
            }
        
        return {}
    
    @staticmethod
    def get_betting_metrics(hours: int = 24) -> Dict[str, Any]:
        """Get betting metrics for the last N hours"""
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_operations,
                SUM(matches_analyzed) as total_matches,
                SUM(value_bets_found) as total_value_bets,
                AVG(success_rate) as avg_success_rate,
                AVG(processing_time) as avg_processing_time
            FROM betting_metrics 
            WHERE timestamp > ?
        ''', (since,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'total_operations': result[0],
                'total_matches': result[1],
                'total_value_bets': result[2],
                'avg_success_rate': round(result[3], 2) if result[3] else 0,
                'avg_processing_time': round(result[4], 3) if result[4] else 0
            }
        
        return {}
    
    @staticmethod
    def cleanup_old_logs(days: int = 30):
        """Clean up old log entries"""
        conn = sqlite3.connect('monitoring.db')
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('DELETE FROM api_metrics WHERE timestamp < ?', (cutoff,))
        cursor.execute('DELETE FROM betting_metrics WHERE timestamp < ?', (cutoff,))
        cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff,))
        
        conn.commit()
        conn.close()
        
        logger.app_logger.info(f"Cleaned up logs older than {days} days")
