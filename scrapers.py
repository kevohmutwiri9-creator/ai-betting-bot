"""
Kenyan Betting Platform Scrapers
Scrapes odds from Betika, SportPesa, and Odibet
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for betting scrapers"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page and return HTML content"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_odds(self, odds_str: str) -> Optional[float]:
        """Parse odds string to float"""
        try:
            cleaned = re.sub(r'[^\d.]', '', odds_str)
            return float(cleaned) if cleaned else None
        except:
            return None
    
    def extract_match_teams(self, text: str) -> tuple:
        """Extract home and away teams from match text"""
        vs_pattern = r'(.+?)\s+(?:vs\.?|vs|-)\s+(.+?)$'
        match = re.search(vs_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, None


class BetikaScraper(BaseScraper):
    """Scraper for Betika Kenya"""
    
    def __init__(self):
        super().__init__("Betika", "https://www.betika.com")
        self.live_url = "https://www.betika.com/ke/events/live"
        self.upcoming_url = "https://www.betika.com/ke/events/upcoming"
    
    def get_live_matches(self) -> List[Dict]:
        """Get live betting matches from Betika"""
        matches = []
        html = self.fetch_page(self.live_url)
        if html:
            matches = self._parse_html(html, "live")
        return matches
    
    def get_upcoming_matches(self) -> List[Dict]:
        """Get upcoming betting matches from Betika"""
        matches = []
        html = self.fetch_page(self.upcoming_url)
        if html:
            matches = self._parse_html(html, "upcoming")
        return matches
    
    def _parse_html(self, html: str, match_type: str) -> List[Dict]:
        """Parse HTML for matches"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for JSON data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.string or ''
            if 'events' in script_text.lower():
                json_data = self._extract_json(script_text)
                if json_data:
                    parsed = self._parse_events(json_data, match_type)
                    matches.extend(parsed)
        
        return matches
    
    def _extract_json(self, script_text: str) -> Optional[dict]:
        """Extract JSON from script"""
        try:
            patterns = [
                r'window\.(\w+)\s*=\s*(\{[^;]+\})',
                r'data\s*=\s*(\{[^;]+\})',
                r'events\s*:\s*(\[[^\]]+\])',
            ]
            for pattern in patterns:
                match = re.search(pattern, script_text)
                if match:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    return json.loads(json_str)
        except:
            pass
        return None
    
    def _parse_events(self, data: dict, match_type: str) -> List[Dict]:
        """Parse events from JSON"""
        matches = []
        events = data.get('data', data.get('events', []))
        for event in events:
            try:
                home = event.get('home_team', event.get('home', ''))
                away = event.get('away_team', event.get('away', ''))
                odds = event.get('odds', event.get('markets', {}))
                
                match = {
                    'platform': 'Betika',
                    'home_team': home,
                    'away_team': away,
                    'match_type': match_type,
                    'home_odds': self._get_odds(odds, '1', 'home'),
                    'draw_odds': self._get_odds(odds, 'X', 'draw'),
                    'away_odds': self._get_odds(odds, '2', 'away'),
                    'timestamp': datetime.now().isoformat(),
                    'league': event.get('league', 'Unknown'),
                }
                matches.append(match)
            except Exception as e:
                logger.debug(f"Error: {e}")
        return matches
    
    def _get_odds(self, odds: dict, *keys) -> Optional[float]:
        """Get odds from dict"""
        for key in keys:
            if key in odds:
                val = odds[key]
                if isinstance(val, (int, float)):
                    return float(val)
        return None


class SportPesaScraper(BaseScraper):
    """Scraper for SportPesa Kenya"""
    
    def __init__(self):
        super().__init__("SportPesa", "https://www.sportpesa.co.ke")
        self.live_url = "https://www.sportpesa.co.ke/live"
        self.upcoming_url = "https://www.sportpesa.co.ke/upcoming"
    
    def get_live_matches(self) -> List[Dict]:
        """Get live betting matches from SportPesa"""
        matches = []
        html = self.fetch_page(self.live_url)
        if html:
            matches = self._parse_html(html, "live")
        return matches
    
    def get_upcoming_matches(self) -> List[Dict]:
        """Get upcoming betting matches from SportPesa"""
        matches = []
        html = self.fetch_page(self.upcoming_url)
        if html:
            matches = self._parse_html(html, "upcoming")
        return matches
    
    def _parse_html(self, html: str, match_type: str) -> List[Dict]:
        """Parse HTML for matches"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.string or ''
            if '__INITIAL_STATE__' in script_text or 'events' in script_text.lower():
                json_data = self._extract_json(script_text)
                if json_data:
                    parsed = self._parse_events(json_data, match_type)
                    matches.extend(parsed)
        
        return matches
    
    def _extract_json(self, script_text: str) -> Optional[dict]:
        """Extract JSON from script"""
        try:
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', script_text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        return None
    
    def _parse_events(self, data: dict, match_type: str) -> List[Dict]:
        """Parse events from JSON"""
        matches = []
        
        def extract(events):
            for event in events or []:
                try:
                    home = event.get('homeTeam', event.get('home', ''))
                    away = event.get('awayTeam', event.get('away', ''))
                    
                    markets = event.get('markets', [])
                    home_odds, draw_odds, away_odds = None, None, None
                    
                    for market in markets:
                        for sel in market.get('selections', []):
                            name = sel.get('type', '').lower()
                            odd = sel.get('odd', sel.get('odds', 0))
                            if 'home' in name:
                                home_odds = float(odd)
                            elif 'draw' in name:
                                draw_odds = float(odd)
                            elif 'away' in name:
                                away_odds = float(odd)
                    
                    matches.append({
                        'platform': 'SportPesa',
                        'home_team': home,
                        'away_team': away,
                        'match_type': match_type,
                        'home_odds': home_odds,
                        'draw_odds': draw_odds,
                        'away_odds': away_odds,
                        'timestamp': datetime.now().isoformat(),
                        'league': event.get('competition', 'Unknown'),
                    })
                except Exception as e:
                    logger.debug(f"Error: {e}")
        
        if isinstance(data, dict):
            if 'events' in data:
                extract(data['events'])
            elif 'data' in data:
                extract(data['data'].get('events', []))
        
        return matches


class OdibetScraper(BaseScraper):
    """Scraper for Odibet Kenya"""
    
    def __init__(self):
        super().__init__("Odibet", "https://www.odibet.com")
        self.live_url = "https://www.odibet.com/en/live"
        self.upcoming_url = "https://www.odibet.com/en/upcoming"
    
    def get_live_matches(self) -> List[Dict]:
        """Get live betting matches from Odibet"""
        matches = []
        html = self.fetch_page(self.live_url)
        if html:
            matches = self._parse_html(html, "live")
        return matches
    
    def get_upcoming_matches(self) -> List[Dict]:
        """Get upcoming betting matches from Odibet"""
        matches = []
        html = self.fetch_page(self.upcoming_url)
        if html:
            matches = self._parse_html(html, "upcoming")
        return matches
    
    def _parse_html(self, html: str, match_type: str) -> List[Dict]:
        """Parse HTML for matches"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.string or ''
            if 'events' in script_text.lower() or 'fixtures' in script_text.lower():
                json_data = self._extract_json(script_text)
                if json_data:
                    parsed = self._parse_events(json_data, match_type)
                    matches.extend(parsed)
        
        return matches
    
    def _extract_json(self, script_text: str) -> Optional[dict]:
        """Extract JSON from script"""
        try:
            patterns = [
                r'data-events\s*=\s*(\[[^\]]+\])',
                r'events\s*:\s*(\[[^\]]+\])',
            ]
            for pattern in patterns:
                match = re.search(pattern, script_text)
                if match:
                    return json.loads(match.group(1))
        except:
            pass
        return None
    
    def _parse_events(self, data: list, match_type: str) -> List[Dict]:
        """Parse events from JSON"""
        matches = []
        for event in data or []:
            try:
                home = event.get('home', event.get('home_team', ''))
                away = event.get('away', event.get('away_team', ''))
                odds = event.get('odds', event.get('markets', []))
                
                matches.append({
                    'platform': 'Odibet',
                    'home_team': home,
                    'away_team': away,
                    'match_type': match_type,
                    'home_odds': float(odds[0]) if odds and len(odds) > 0 else None,
                    'draw_odds': float(odds[1]) if odds and len(odds) > 1 else None,
                    'away_odds': float(odds[2]) if odds and len(odds) > 2 else None,
                    'timestamp': datetime.now().isoformat(),
                    'league': event.get('league', 'Unknown'),
                })
            except Exception as e:
                logger.debug(f"Error: {e}")
        return matches


class KenyanOddsAggregator:
    """Aggregates odds from all Kenyan betting platforms"""
    
    def __init__(self):
        self.betika = BetikaScraper()
        self.sportpesa = SportPesaScraper()
        self.odibet = OdibetScraper()
    
    def get_all_odds(self) -> List[Dict]:
        """Get all odds from all platforms"""
        all_matches = []
        
        for scraper, name in [
            (self.betika, "Betika"),
            (self.sportpesa, "SportPesa"),
            (self.odibet, "Odibet"),
        ]:
            try:
                live = scraper.get_live_matches()
                upcoming = scraper.get_upcoming_matches()
                all_matches.extend(live + upcoming)
                logger.info(f"{name}: {len(live)} live, {len(upcoming)} upcoming")
            except Exception as e:
                logger.error(f"Error fetching from {name}: {e}")
        
        return all_matches
    
    def compare_odds(self) -> List[Dict]:
        """Compare odds across platforms"""
        all_odds = self.get_all_odds()
        
        matches = {}
        for match in all_odds:
            key = f"{match['home_team'].lower()}|{match['away_team'].lower()}"
            if key not in matches:
                matches[key] = {
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'platforms': [],
                }
            matches[key]['platforms'].append({
                'name': match['platform'],
                'home_odds': match['home_odds'],
                'draw_odds': match['draw_odds'],
                'away_odds': match['away_odds'],
            })
        
        return list(matches.values())


def test_scrapers():
    """Test the scrapers"""
    print("Testing Kenyan Betting Scrapers...")
    print("=" * 50)
    
    aggregator = KenyanOddsAggregator()
    
    for name, scraper in [
        ("Betika", aggregator.betika),
        ("SportPesa", aggregator.sportpesa),
        ("Odibet", aggregator.odibet),
    ]:
        print(f"\n{name}:")
        try:
            live = scraper.get_live_matches()
            upcoming = scraper.get_upcoming_matches()
            print(f"  Live: {len(live)}, Upcoming: {len(upcoming)}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    test_scrapers()
