"""Tests for Kenyan Betting Scrapers"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers import (
    BetikaScraper,
    SportPesaScraper,
    OdibetScraper,
    KenyanOddsAggregator,
    BaseScraper,
)


class TestBaseScraper:
    """Test cases for BaseScraper"""
    
    @pytest.fixture
    def scraper(self):
        return BaseScraper("TestScraper", "https://test.com")
    
    def test_parse_odds_valid(self, scraper):
        assert scraper.parse_odds("2.50") == 2.50
        assert scraper.parse_odds("3.0") == 3.0
        assert scraper.parse_odds("1.75") == 1.75
    
    def test_parse_odds_invalid(self, scraper):
        assert scraper.parse_odds("N/A") is None
        assert scraper.parse_odds("") is None
    
    def test_extract_match_teams_vs(self, scraper):
        home, away = scraper.extract_match_teams("Arsenal vs Chelsea")
        assert home == "Arsenal"
        assert away == "Chelsea"
    
    def test_extract_match_teams_dash(self, scraper):
        home, away = scraper.extract_match_teams("Man Utd - Liverpool")
        assert home == "Man Utd"
        assert away == "Liverpool"
    
    def test_fetch_page_success(self, scraper):
        with patch('scrapers.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.text = '<html>test</html>'
            mock_get.return_value = mock_response
            
            result = scraper.fetch_page("https://test.com")
            assert result == '<html>test</html>'
    
    def test_fetch_page_error(self, scraper):
        with patch('scrapers.requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            result = scraper.fetch_page("https://test.com")
            assert result is None


class TestBetikaScraper:
    """Test cases for BetikaScraper"""
    
    @pytest.fixture
    def scraper(self):
        return BetikaScraper()
    
    def test_initialization(self, scraper):
        assert scraper.name == "Betika"
        assert "betika" in scraper.base_url.lower()
    
    @patch('scrapers.BetikaScraper.fetch_page')
    def test_get_live_matches_empty(self, mock_fetch, scraper):
        mock_fetch.return_value = '<html></html>'
        matches = scraper.get_live_matches()
        assert isinstance(matches, list)


class TestSportPesaScraper:
    """Test cases for SportPesaScraper"""
    
    @pytest.fixture
    def scraper(self):
        return SportPesaScraper()
    
    def test_initialization(self, scraper):
        assert scraper.name == "SportPesa"
        assert "sportpesa" in scraper.base_url.lower()
    
    @patch('scrapers.SportPesaScraper.fetch_page')
    def test_get_upcoming_matches_empty(self, mock_fetch, scraper):
        mock_fetch.return_value = '<html></html>'
        matches = scraper.get_upcoming_matches()
        assert isinstance(matches, list)


class TestOdibetScraper:
    """Test cases for OdibetScraper"""
    
    @pytest.fixture
    def scraper(self):
        return OdibetScraper()
    
    def test_initialization(self, scraper):
        assert scraper.name == "Odibet"
        assert "odibet" in scraper.base_url.lower()
    
    @patch('scrapers.OdibetScraper.fetch_page')
    def test_get_live_matches_empty(self, mock_fetch, scraper):
        mock_fetch.return_value = '<html></html>'
        matches = scraper.get_live_matches()
        assert isinstance(matches, list)


class TestKenyanOddsAggregator:
    """Test cases for KenyanOddsAggregator"""
    
    @pytest.fixture
    def aggregator(self):
        return KenyanOddsAggregator()
    
    def test_initialization(self, aggregator):
        assert hasattr(aggregator, 'betika')
        assert hasattr(aggregator, 'sportpesa')
        assert hasattr(aggregator, 'odibet')
    
    @patch('scrapers.BetikaScraper.get_live_matches')
    @patch('scrapers.BetikaScraper.get_upcoming_matches')
    @patch('scrapers.SportPesaScraper.get_live_matches')
    @patch('scrapers.SportPesaScraper.get_upcoming_matches')
    @patch('scrapers.OdibetScraper.get_live_matches')
    @patch('scrapers.OdibetScraper.get_upcoming_matches')
    def test_get_all_odds(
        self, mock_odi_live, mock_odi_up, 
        mock_sp_live, mock_sp_up,
        mock_bet_live, mock_bet_up,
        aggregator
    ):
        # Setup mocks
        mock_bet_live.return_value = [
            {'platform': 'Betika', 'home_team': 'A', 'away_team': 'B', 'home_odds': 2.0}
        ]
        mock_bet_up.return_value = []
        mock_sp_live.return_value = []
        mock_sp_up.return_value = []
        mock_odi_live.return_value = []
        mock_odi_up.return_value = []
        
        odds = aggregator.get_all_odds()
        assert len(odds) == 1
        assert odds[0]['platform'] == 'Betika'
    
    def test_compare_odds_structure(self, aggregator):
        """Test that compare_odds returns properly structured data"""
        with patch.object(aggregator, 'get_all_odds') as mock_get:
            mock_get.return_value = [
                {'platform': 'A', 'home_team': 'X', 'away_team': 'Y', 'home_odds': 2.0, 
                 'draw_odds': 3.0, 'away_odds': 4.0},
                {'platform': 'B', 'home_team': 'X', 'away_team': 'Y', 'home_odds': 2.1,
                 'draw_odds': 3.1, 'away_odds': 4.1},
            ]
            result = aggregator.compare_odds()
            assert len(result) == 1
            assert 'platforms' in result[0]
            assert len(result[0]['platforms']) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
