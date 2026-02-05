"""
Selenium Browser Automation for Real Betting
WARNING: Automated betting may violate bookmaker Terms of Service
Use at your own risk
"""

import os
import sys
import json
import time
import logging
import getpass
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

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
    bet_type: str
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


def get_secure_input(prompt: str, is_password: bool = False) -> str:
    """Get secure input from user"""
    if is_password:
        return getpass.getpass(prompt)
    else:
        return input(prompt)


class BaseBrowserBot:
    """Base class for browser automation on betting sites"""
    
    def __init__(self, username: str = None, password: str = None, headless: bool = True):
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
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        
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
            
            username_field = self.driver.find_element(By.NAME, "username")
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
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
    
    def __init__(self, username: str = None, password: str = None, headless: bool = True):
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
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on Betika"""
        if not self.logged_in:
            if not self.login():
                return BetResult(success=False, error="Not logged in")
        
        try:
            self.navigate_to_match(bet.match_id)
            time.sleep(2)
            
            team_name = bet.home_team if bet.bet_type == "home" else bet.away_team if bet.bet_type == "away" else "Draw"
            
            selectors = [
                f"//button[contains(., '{team_name}')]",
                f"//div[contains(@class, 'selection') and contains(., '{team_name}')]",
            ]
            
            button = None
            for selector in selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if not button:
                return BetResult(success=False, error="Could not find selection")
            
            button.click()
            time.sleep(1)
            
            stake_input = self.driver.find_element(By.NAME, "stake")
            stake_input.clear()
            stake_input.send_keys(str(bet.stake))
            
            place_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Place Bet')]")
            place_button.click()
            
            time.sleep(2)
            
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
    
    def __init__(self, username: str = None, password: str = None, headless: bool = True):
        super().__init__(username, password, headless)
        self.base_url = "https://www.sportpesa.co.ke"
        self.login_url = f"{self.base_url}/login"
    
    def login(self) -> bool:
        """Login to SportPesa"""
        return super().login(self.login_url)
    
    def place_bet(self, bet: BetRequest) -> BetResult:
        """Place a bet on SportPesa"""
        if not self.logged_in:
            if not self.login():
                return BetResult(success=False, error="Not logged in")
        
        try:
            self.driver.get(f"{self.base_url}/events/{bet.match_id}")
            time.sleep(2)
            
            stake_input = self.driver.find_element(By.ID, "bet-amount")
            stake_input.clear()
            stake_input.send_keys(str(bet.stake))
            
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
    
    def __init__(self, username: str = None, password: str = None, headless: bool = True):
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
        self.credentials_file = config_file
        self.credentials = {}
        self.load_credentials()
    
    def _initialize_bots(self):
        """Initialize bots with loaded credentials"""
        for platform, creds in self.credentials.items():
            if platform == 'betika':
                self.bots['betika'] = BetikaBrowserBot(creds['username'], creds['password'])
            elif platform == 'sportpesa':
                self.bots['sportpesa'] = SportPesaBrowserBot(creds['username'], creds['password'])
            elif platform == 'odibet':
                self.bots['odibet'] = OdibetBrowserBot(creds['username'], creds['password'])
    
    def load_credentials(self):
        """Load credentials from file or prompt user"""
        if self.credentials_file and os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    self.credentials = json.load(f)
                logger.info("Credentials loaded from file")
                self._initialize_bots()
                return
            except Exception as e:
                logger.warning(f"Could not load credentials file: {e}")
        
        if sys.stdin.isatty():
            self._prompt_credentials()
        else:
            print("\n" + "=" * 60)
            print("INTERACTIVE MODE REQUIRED")
            print("=" * 60)
            print("Run in interactive terminal to enter credentials.")
            print("=" * 60 + "\n")
            self._initialize_bots()
    
    def _prompt_credentials(self):
        """Prompt user for credentials securely"""
        print("\n" + "=" * 60)
        print("SECURE CREDENTIALS INPUT")
        print("=" * 60)
        print("Enter your betting site credentials (hidden for security)")
        print("=" * 60 + "\n")
        
        # Betika
        print("[1/3] Betika")
        betika_user = get_secure_input("  Username: ")
        betika_pass = get_secure_input("  Password: ", is_password=True)
        if betika_user and betika_pass:
            self.credentials['betika'] = {'username': betika_user, 'password': betika_pass}
        
        # SportPesa
        print("\n[2/3] SportPesa")
        sportpesa_user = get_secure_input("  Username: ")
        sportpesa_pass = get_secure_input("  Password: ", is_password=True)
        if sportpesa_user and sportpesa_pass:
            self.credentials['sportpesa'] = {'username': sportpesa_user, 'password': sportpesa_pass}
        
        # Odibet
        print("\n[3/3] Odibet")
        odibet_user = get_secure_input("  Username: ")
        odibet_pass = get_secure_input("  Password: ", is_password=True)
        if odibet_user and odibet_pass:
            self.credentials['odibet'] = {'username': odibet_user, 'password': odibet_pass}
        
        self._initialize_bots()
        
        print("\n" + "=" * 60)
        print("Credentials secured!")
        print("=" * 60)
    
    def save_credentials(self, filepath: str = "credentials.enc"):
        """Save credentials to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.credentials, f)
            logger.info(f"Credentials saved to {filepath}")
        except Exception as e:
            logger.error(f"Could not save credentials: {e}")
    
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


def main():
    """Main entry point - run with secure credential input"""
    print("=" * 60)
    print("AI BETTING BOT - BROWSER AUTOMATION")
    print("=" * 60)
    print("\nWARNING: Automated betting may violate Terms of Service")
    print("Use at your own risk\n")
    print("=" * 60)
    
    if not SELENIUM_AVAILABLE:
        print("ERROR: Selenium not installed")
        print("Run: pip install selenium webdriver-manager")
        return
    
    system = AutoBettingSystem()
    
    save = input("\nSave credentials for next time? (y/n): ").lower()
    if save == 'y':
        system.save_credentials()
    
    print("\n" + "=" * 60)
    print("System ready! Use system.place_bet() to place bets.")
    print("=" * 60)


if __name__ == "__main__":
    main()
