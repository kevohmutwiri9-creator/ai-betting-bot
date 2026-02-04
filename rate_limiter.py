"""
Rate limiting utilities for AI Betting Bot API
"""

import time
import json
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Any, Optional
import threading

class RateLimiter:
    """Thread-safe rate limiter using sliding window algorithm"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = defaultdict(lambda: deque())
        self.limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'api': {'requests': 1000, 'window': 3600},     # 1000 requests per hour
            'auth': {'requests': 10, 'window': 300},       # 10 requests per 5 minutes
            'premium': {'requests': 5000, 'window': 3600}   # 5000 requests per hour
        }
    
    def is_allowed(self, key: str, limit_type: str = 'default') -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed based on rate limit"""
        with self.lock:
            now = time.time()
            limit_config = self.limits.get(limit_type, self.limits['default'])
            
            # Clean old requests
            window_start = now - limit_config['window']
            while self.requests[key] and self.requests[key][0] < window_start:
                self.requests[key].popleft()
            
            # Check if under limit
            if len(self.requests[key]) < limit_config['requests']:
                self.requests[key].append(now)
                return True, {
                    'remaining': limit_config['requests'] - len(self.requests[key]),
                    'reset_time': int(window_start + limit_config['window']),
                    'limit': limit_config['requests']
                }
            else:
                # Find when the oldest request expires
                oldest_request = self.requests[key][0]
                reset_time = int(oldest_request + limit_config['window'])
                
                return False, {
                    'remaining': 0,
                    'reset_time': reset_time,
                    'limit': limit_config['requests']
                }
    
    def get_client_key(self, request_obj) -> str:
        """Generate client key for rate limiting"""
        # Try to get user ID from authenticated request
        if hasattr(g, 'user_id'):
            return f"user:{g.user_id}"
        
        # Fall back to IP address
        forwarded_for = request_obj.headers.get('X-Forwarded-For')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request_obj.remote_addr or 'unknown'
        
        return f"ip:{ip}"

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit_type: str = 'default'):
    """Decorator to apply rate limiting to Flask routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client key
            client_key = rate_limiter.get_client_key(request)
            
            # Check rate limit
            allowed, info = rate_limiter.is_allowed(client_key, limit_type)
            
            # Add rate limit headers
            response_headers = {
                'X-RateLimit-Limit': str(info['limit']),
                'X-RateLimit-Remaining': str(info['remaining']),
                'X-RateLimit-Reset': str(info['reset_time'])
            }
            
            if not allowed:
                # Return rate limit exceeded response
                response = jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again after {info["reset_time"] - int(time.time())} seconds.',
                    'retry_after': info['reset_time'] - int(time.time())
                })
                response.status_code = 429
                
                # Add headers to response
                for header, value in response_headers.items():
                    response.headers[header] = value
                
                return response
            
            # Store rate limit info for later use
            g.rate_limit_info = info
            
            # Execute the original function
            response = f(*args, **kwargs)
            
            # Add headers to successful responses
            if hasattr(response, 'headers'):
                for header, value in response_headers.items():
                    response.headers[header] = value
            
            return response
        
        return decorated_function
    return decorator

class APIKeyRateLimiter:
    """Rate limiter for API key based requests"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.api_requests = defaultdict(lambda: deque())
        self.api_limits = {
            'free': {'requests': 100, 'window': 3600},      # 100 requests per hour
            'basic': {'requests': 1000, 'window': 3600},    # 1000 requests per hour
            'premium': {'requests': 10000, 'window': 3600},  # 10000 requests per hour
            'enterprise': {'requests': 100000, 'window': 3600}  # 100k requests per hour
        }
    
    def is_allowed(self, api_key: str, tier: str = 'free') -> tuple[bool, Dict[str, Any]]:
        """Check if API key request is allowed"""
        with self.lock:
            now = time.time()
            limit_config = self.api_limits.get(tier, self.api_limits['free'])
            
            # Clean old requests
            window_start = now - limit_config['window']
            while self.api_requests[api_key] and self.api_requests[api_key][0] < window_start:
                self.api_requests[api_key].popleft()
            
            # Check if under limit
            if len(self.api_requests[api_key]) < limit_config['requests']:
                self.api_requests[api_key].append(now)
                return True, {
                    'remaining': limit_config['requests'] - len(self.api_requests[api_key]),
                    'reset_time': int(window_start + limit_config['window']),
                    'limit': limit_config['requests']
                }
            else:
                oldest_request = self.api_requests[api_key][0]
                reset_time = int(oldest_request + limit_config['window'])
                
                return False, {
                    'remaining': 0,
                    'reset_time': reset_time,
                    'limit': limit_config['requests']
                }

# Global API key rate limiter
api_rate_limiter = APIKeyRateLimiter()

def api_rate_limit():
    """Decorator for API key based rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from request
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                api_key = request.args.get('api_key')
            
            if not api_key:
                response = jsonify({
                    'success': False,
                    'error': 'API key required',
                    'message': 'Please provide an API key in X-API-Key header or api_key parameter'
                })
                response.status_code = 401
                return response
            
            # Determine user tier (this would typically come from database)
            # For now, we'll use a simple mapping
            user_tier = 'free'  # Default tier
            if hasattr(g, 'user_tier'):
                user_tier = g.user_tier
            
            # Check rate limit
            allowed, info = api_rate_limiter.is_allowed(api_key, user_tier)
            
            # Add rate limit headers
            response_headers = {
                'X-RateLimit-Limit': str(info['limit']),
                'X-RateLimit-Remaining': str(info['remaining']),
                'X-RateLimit-Reset': str(info['reset_time']),
                'X-API-Tier': user_tier
            }
            
            if not allowed:
                response = jsonify({
                    'success': False,
                    'error': 'API rate limit exceeded',
                    'message': f'API rate limit exceeded for {user_tier} tier. Try again later.',
                    'retry_after': info['reset_time'] - int(time.time()),
                    'tier': user_tier
                })
                response.status_code = 429
                
                for header, value in response_headers.items():
                    response.headers[header] = value
                
                return response
            
            # Store info for later use
            g.api_rate_limit_info = info
            
            # Execute original function
            response = f(*args, **kwargs)
            
            # Add headers to successful responses
            if hasattr(response, 'headers'):
                for header, value in response_headers.items():
                    response.headers[header] = value
            
            return response
        
        return decorated_function
    return decorator

class TokenBucketRateLimiter:
    """Token bucket algorithm for more sophisticated rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = {}
        self.last_refill = {}
        self.lock = threading.Lock()
    
    def consume(self, key: str, tokens: int = 1) -> bool:
        """Consume tokens from bucket"""
        with self.lock:
            now = time.time()
            
            # Initialize bucket if not exists
            if key not in self.tokens:
                self.tokens[key] = self.capacity
                self.last_refill[key] = now
            
            # Refill tokens
            time_passed = now - self.last_refill[key]
            self.tokens[key] = min(self.capacity, self.tokens[key] + time_passed * self.refill_rate)
            self.last_refill[key] = now
            
            # Check if enough tokens
            if self.tokens[key] >= tokens:
                self.tokens[key] -= tokens
                return True
            
            return False

# Specialized rate limiters for different use cases
auth_rate_limiter = TokenBucketRateLimiter(capacity=5, refill_rate=0.033)  # 5 requests, refill 1 per 30 seconds
premium_rate_limiter = TokenBucketRateLimiter(capacity=100, refill_rate=0.028)  # 100 requests, refill 1 per 35 seconds

def auth_rate_limit():
    """Rate limiting for authentication endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_key = rate_limiter.get_client_key(request)
            
            if not auth_rate_limiter.consume(client_key):
                response = jsonify({
                    'success': False,
                    'error': 'Too many authentication attempts',
                    'message': 'Please wait before trying again'
                })
                response.status_code = 429
                response.headers['Retry-After'] = '30'
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def premium_rate_limit():
    """Rate limiting for premium features"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(g, 'user_id'):
                client_key = f"user:{g.user_id}"
            else:
                client_key = rate_limiter.get_client_key(request)
            
            if not premium_rate_limiter.consume(client_key):
                response = jsonify({
                    'success': False,
                    'error': 'Premium rate limit exceeded',
                    'message': 'You have exceeded your premium request limit'
                })
                response.status_code = 429
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
