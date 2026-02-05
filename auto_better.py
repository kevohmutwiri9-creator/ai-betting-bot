"""
Selenium Browser Automation for Real Betting
WARNING: Automated betting may violate bookmaker Terms of Service
Use at your own risk
"""

import os
import json
import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Try to import selenium, provide helpful error if not installed
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed. Run: pip install selenium webdriver-manager")


@dataclass
class BetRequest:
    """Request to place a bet"""
    platform: str
    home_team: str
    away_team: str
    bet_type: str  # home, draw, away
    odds: float
    stake: float
    match_id: str = ""


@dataclass  
class BetResult:
    """Result of a bet placement"""
    success: bool
    bet_id: Optional[str] = None
    odds: Optional[float] = None
    stake: Optional[float] = None
    error: Optional[str] = None
    timestamp: str = ""


class BaseBrowserBot:
    """Base class for browser automation on betting sites"""
    
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self.logged_in = False
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not installed")
        
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        
        # User agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable webdriver flag
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        
        # Execute anti-detection script
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    def login(self, login_url: str) -> bool:
        """Login to the betting site"""
        if not self.driver:
            self.setup_driver()
        
        try:
            self.driver.get(login_url)
            time.sleep(3)
            
            # Find and fill username
            username_field = self.driver.find_element(By.NAME, "username")
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find and fill password
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login
            time.sleep(5)
            
            self.logged_in = True
            logger.info(f"Logged in to betting site")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def navigate_to_match(self, match_id: str):
        """Navigate to a specific match"""
        raise NotImplementedError
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on a selection"""
        raise NotImplementedError
    
    def get_balance(self) -> Optional[float]:
        """Get current account balance"""
        try:
            balance_elem = self.driver.find_element(By.CLASS_NAME, "balance")
            balance_text = balance_elem.text.replace("KES", "").replace(",", "").strip()
            return float(balance_text)
        except:
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


class BetikaBrowserBot(BaseBrowserBot):
    """Browser automation for Betika Kenya"""
    
    def __init__(self, username: str, password: str, headless: bool = True):
        super().__init__(username, password, headless)
        self.base_url = "https://www.betika.com"
        self.login_url = f"{self.base_url}/login"
    
    def login(self) -> bool:
        """Login to Betika"""
        return super().login(self.login_url)
    
    def navigate_to_match(self, match_id: str):
        """Navigate to a match by ID"""
        match_url = f"{self.base_url}/en/ke/match/{match_id}"
        self.driver.get(match_url)
        time.sleep(3)
    
    def _find_odds_button(self, team_name: str, bet_type: str):
        """Find the odds button for a selection"""
        try:
            # Try different selectors
            selectors = [
                f"//button[contains(., '{team_name}')]",
                f"//div[contains(@class, 'selection') and contains(., '{team_name}')]",
                f"//span[contains(., '{team_name}')]/following-sibling::span[@class='odds']",
            ]
            
            for selector in selectors:
                try:
                    elem = self.driver.find_element(By.XPATH, selector)
                    return elem
                except:
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"Error finding odds button: {e}")
            return None
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on Betika"""
        if not self.logged_in:
            if not self.login():
                return BetResult(success=False, error="Not logged in")
        
        try:
            # Navigate to match
            self.navigate_to_match(bet.match_id)
            time.sleep(2)
            
            # Find and click the odds button
            button = self._find_odds_button(
                bet.home_team if bet.bet_type == "home" else 
                bet.away_team if bet.bet_type == "away" else "Draw",
                bet.bet_type
            )
            
            if not button:
                return BetResult(success=False, error="Could not find selection")
            
            button.click()
            time.sleep(1)
            
            # Enter stake
            stake_input = self.driver.find_element(By.NAME, "stake")
            stake_input.clear()
            stake_input.send_keys(str(bet.stake))
            
            # Click place bet button
            place_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Place Bet')]")
            place_button.click()
            
            time.sleep(2)
            
            # Get confirmation
            bet_id = self.driver.current_url.split("/")[-1]
            
            return BetResult(
                success=True,
                bet_id=bet_id,
                odds=bet.odds,
                stake=bet.stake,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return BetResult(success=False, error=str(e))


class SportPesaBrowserBot(BaseBrowserBot):
    """Browser automation for SportPesa Kenya"""
    
    def __init__(self, username: str, password: str, headless: bool = True):
        super().__init__(username, password, headless)
        self.base_url = "https://www.sportpesa.co.ke"
        self.login_url = f"{self.base_url}/login"
    
    def login(self) -> bool:
        """Login to SportPesa"""
        return super().login(self.login_url)
    
    def navigate_to_match(self, match_id: str):
        """Navigate to a match"""
        match_url = f"{self.base_url}/events/{match_id}"
        self.driver.get(match_url)
        time.sleep(3)
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on SportPesa"""
        if not self.logged_in:
            if not self.login():
                return BetResult(success=False, error="Not logged in")
        
        try:
            self.navigate_to_match(bet.match_id)
            time.sleep(2)
            
            # SportPesa specific selectors
            team_selectors = [
                f"//div[contains(@class, 'event-team') and contains(., '{bet.home_team}')]",
                f"//button[@data-team='{bet.home_team}']",
            ]
            
            for selector in team_selectors:
                try:
                    elem = self.driver.find_element(By.XPATH, selector)
                    elem.click()
                    break
                except:
                    continue
            
            time.sleep(1)
            
            # Enter stake
            stake_input = self.driver.find_element(By.ID, "bet-amount")
            stake_input.clear()
            stake_input.send_keys(str(bet.stake))
            
            # Place bet
            place_button = self.driver.find_element(By.ID, "place-bet")
            place_button.click()
            
            return BetResult(
                success=True,
                bet_id=str(int(time.time())),
                odds=bet.odds,
                stake=bet.stake,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return BetResult(success=False, error=str(e))


class OdibetBrowserBot(BaseBrowserBot):
    """Browser automation for Odibet"""
    
    def __init__(self, username: str, password: str, headless: bool = True):
        super().__init__(username, password, headless)
        self.base_url = "https://www.odibet.com"
        self.login_url = f"{self.base_url}/login"
    
    def login(self) -> bool:
        """Login to Odibet"""
        return super().login(self.login_url)
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on Odibet"""
        if not self.logged_in:
            if not self.login():
                return BetResult(success=False, error="Not logged in")
        
        try:
            self.driver.get(f"{self.base_url}/en/betting")
            time.sleep(3)
            
            # Odibet specific
            selection = self.driver.find_element(
                By.XPATH, f"//div[contains(., '{bet.home_team}')]"
            )
            selection.click()
            
            time.sleep(1)
            
            stake_input = self.driver.find_element(By.NAME, "stake")
            stake_input.clear()
            stake_input.send_keys(str(bet.stake))
            
            bet_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Bet')]")
            bet_button.click()
            
            return BetResult(
                success=True,
                bet_id=f"ODB-{int(time.time())}",
                odds=bet.odds,
                stake=bet.stake,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return BetResult(success=False, error=str(e))


class AutoBettingSystem:
    """Automated betting system that coordinates multiple platforms"""
    
    def __init__(self, config_file: str = None):
        self.bots = {}
        self.bet_history = []
        self.load_config(config_file)
    
    def load_config(self, config_file: str = None):
        """Load credentials from config or environment"""
        load_dotenv()
        
        # Betika credentials
        betika_user = os.getenv("BETIKA_USERNAME")
        betika_pass = os.getenv("BETIKA_PASSWORD")
        if betika_user and betika_pass:
            self.bots["betika"] = BetikaBrowserBot(betika_user, betika_pass)
        
        # SportPesa credentials
        sportpesa_user = os.getenv("SPORTPESA_USERNAME")
        sportpesa_pass = os.getenv("SPORTPESA_PASSWORD")
        if sportpesa_user and sportpesa_pass:
            self.bots["sportpesa"] = SportPesaBrowserBot(sportpesa_user, sportpesa_pass)
        
        # Odibet credentials
        odibet_user = os.getenv("ODIBET_USERNAME")
        odibet_pass = os.getenv("ODIBET_PASSWORD")
        if odibet_user and odibet_pass:
            self.bots["odibet"] = OdibetBrowserBot(odibet_user, odibet_pass)
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on the specified platform"""
        if bet.platform not in self.bots:
            return BetResult(success=False, error=f"Unknown platform: {bet.platform}")
        
        bot = self.bots[bet.platform]
        result = bot.place_bet(bet)
        
        self.bet_history.append({
            'bet': bet,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def close_all(self):
        """Close all browser sessions"""
        for bot in self.bots.values():
            bot.close()
    
    def get_bet_history(self) -> List[Dict]:
        """Get history of all placed bets"""
        return self.bet_history


def test_browser_automation():
    """Test browser automation setup"""
    print("=" * 60)
    print("Browser Automation Test")
    print("=" * 60)
    
    if not SELENIUM_AVAILABLE:
        print("ERROR: Selenium not installed")
        print("Run: pip install selenium webdriver-manager")
        return
    
    print("\nSelenium is available!")
    print("\nTo use browser automation:")
    print("1. Add credentials to .env file:")
    print("   BETIKA_USERNAME=your_username")
    print("   BETIKA_PASSWORD=your_password")
    print("   SPORTPESA_USERNAME=your_username")
    print("   SPORTPESA_PASSWORD=your_password")
    print("   ODIBET_USERNAME=your_username")
    print("   ODIBET_PASSWORD=your_password")
    print("\n2. Usage example:")
    print("""
from auto_better import AutoBettingSystem, BetRequest

# Create betting system
system = AutoBettingSystem()

# Create a bet request
bet = BetRequest(
    platform="betika",
    home_team="Arsenal",
    away_team="Chelsea",
    bet_type="home",
    odds=2.0,
    stake=100,
    match_id="12345"
)

# Place the bet
result = system.place_bet(bet)
print(f"Bet placed: {result.success}")
    """)
    
    print("\n" + "=" * 60)
    print("WARNING: Automated betting may violate Terms of Service")
    print("Use at your own risk")
    print("=" * 60)


if __name__ == "__main__":
    test_browser_automation()
