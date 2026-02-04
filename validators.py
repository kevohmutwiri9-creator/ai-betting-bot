"""
Input validation and sanitization utilities for AI Betting Bot
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Centralized input validation and sanitization"""
    
    @staticmethod
    def validate_team_name(team_name: str) -> str:
        """Validate and sanitize team name"""
        if not team_name or not isinstance(team_name, str):
            raise ValidationError("Team name is required and must be a string")
        
        # Remove HTML tags and special characters
        sanitized = re.sub(r'<[^>]+>', '', team_name.strip())
        sanitized = re.sub(r'[<>"\';]', '', sanitized)
        
        if len(sanitized) < 2 or len(sanitized) > 50:
            raise ValidationError("Team name must be between 2 and 50 characters")
        
        return sanitized
    
    @staticmethod
    def validate_league_name(league: str) -> str:
        """Validate and sanitize league name"""
        if not league or not isinstance(league, str):
            raise ValidationError("League name is required and must be a string")
        
        sanitized = re.sub(r'<[^>]+>', '', league.strip())
        sanitized = re.sub(r'[<>"\';]', '', sanitized)
        
        valid_leagues = [
            'premier_league', 'la_liga', 'serie_a', 'bundesliga', 'ligue_1',
            'champions_league', 'europa_league', 'eredivisie',
            'casino_games', 'slot_games', 'poker_games', 'virtual_sports', 'esports'
        ]
        
        if sanitized.lower() not in valid_leagues:
            raise ValidationError(f"Invalid league. Must be one of: {', '.join(valid_leagues)}")
        
        return sanitized.lower()
    
    @staticmethod
    def validate_odds(odds_value: Any) -> float:
        """Validate betting odds"""
        try:
            odds = float(odds_value)
        except (ValueError, TypeError):
            raise ValidationError("Odds must be a valid number")
        
        if odds <= 1.01 or odds > 1000:
            raise ValidationError("Odds must be between 1.01 and 1000")
        
        return round(odds, 2)
    
    @staticmethod
    def validate_stake(stake_value: Any) -> float:
        """Validate betting stake"""
        try:
            stake = float(stake_value)
        except (ValueError, TypeError):
            raise ValidationError("Stake must be a valid number")
        
        if stake <= 0 or stake > 10000:
            raise ValidationError("Stake must be between 0 and 10000")
        
        return round(stake, 2)
    
    @staticmethod
    def validate_date(date_string: str) -> str:
        """Validate and format date"""
        if not date_string:
            raise ValidationError("Date is required")
        
        try:
            # Try to parse date in various formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    parsed_date = datetime.strptime(date_string.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        except Exception:
            raise ValidationError("Invalid date format")
    
    @staticmethod
    def validate_match_id(match_id: str) -> str:
        """Validate match ID"""
        if not match_id or not isinstance(match_id, str):
            raise ValidationError("Match ID is required")
        
        # Remove any special characters except underscores and hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', match_id.strip())
        
        if len(sanitized) < 3 or len(sanitized) > 50:
            raise ValidationError("Match ID must be between 3 and 50 characters")
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")
        
        email = email.strip().lower()
        
        # Basic email validation regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
        
        return email
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username"""
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required")
        
        username = username.strip()
        
        # Remove special characters
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', username)
        
        if len(sanitized) < 3 or len(sanitized) > 20:
            raise ValidationError("Username must be between 3 and 20 characters")
        
        return sanitized
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password"""
        if not password or not isinstance(password, str):
            raise ValidationError("Password is required")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Check for at least one number and one letter
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number")
        
        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError("Password must contain at least one letter")
        
        return password
    
    @staticmethod
    def validate_api_key(api_key: str) -> str:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key is required")
        
        api_key = api_key.strip()
        
        # Basic API key validation (alphanumeric, length between 10 and 100)
        if not re.match(r'^[a-zA-Z0-9_-]{10,100}$', api_key):
            raise ValidationError("Invalid API key format")
        
        return api_key
    
    @staticmethod
    def validate_pagination(page: int, limit: int) -> tuple:
        """Validate pagination parameters"""
        if page < 1:
            raise ValidationError("Page must be at least 1")
        
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")
        
        return page, limit
    
    @staticmethod
    def sanitize_string(input_string: str, max_length: int = 255) -> str:
        """General string sanitization"""
        if not input_string:
            return ""
        
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]+>', '', str(input_string))
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';&]', '', sanitized)
        
        # Trim and limit length
        sanitized = sanitized.strip()[:max_length]
        
        return sanitized

def validate_match_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate match analysis request data"""
    required_fields = ['home_team', 'away_team', 'home_odds', 'draw_odds', 'away_odds']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate each field
    validated_data = {
        'home_team': InputValidator.validate_team_name(data['home_team']),
        'away_team': InputValidator.validate_team_name(data['away_team']),
        'home_odds': InputValidator.validate_odds(data['home_odds']),
        'draw_odds': InputValidator.validate_odds(data['draw_odds']),
        'away_odds': InputValidator.validate_odds(data['away_odds']),
        'league': InputValidator.validate_league_name(data.get('league', 'premier_league')),
        'date': InputValidator.validate_date(data.get('date', datetime.now().strftime('%Y-%m-%d')))
    }
    
    return validated_data

def validate_auto_bet_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate auto-bet request data"""
    validated_data = {
        'stake': InputValidator.validate_stake(data.get('stake', 100)),
        'max_odds': InputValidator.validate_odds(data.get('max_odds', 10.0)),
        'min_value': InputValidator.validate_stake(data.get('min_value', 5.0)),
        'auto_confirm': bool(data.get('auto_confirm', False))
    }
    
    if validated_data['max_odds'] < 1.5:
        raise ValidationError("Maximum odds cannot be less than 1.5")
    
    if validated_data['min_value'] < 0:
        raise ValidationError("Minimum value cannot be negative")
    
    return validated_data

def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user registration data"""
    required_fields = ['username', 'email', 'password']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    validated_data = {
        'username': InputValidator.validate_username(data['username']),
        'email': InputValidator.validate_email(data['email']),
        'password': InputValidator.validate_password(data['password'])
    }
    
    return validated_data

def validate_user_login(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user login data"""
    if 'username' not in data or 'password' not in data:
        raise ValidationError("Username and password are required")
    
    return {
        'username': InputValidator.sanitize_string(data['username']),
        'password': data['password']  # Don't sanitize password
    }
