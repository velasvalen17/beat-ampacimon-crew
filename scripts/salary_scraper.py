#!/usr/bin/env python3
"""
NBA Fantasy Salary Scraper
Fetches player salary data from nbafantasy.nba.com using Selenium
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.database import get_connection

class NBAFantasySalaryScraper:
    """Scraper for NBA Fantasy salary data."""
    
    def __init__(self, email=None, password=None, headless=True):
        """Initialize the scraper."""
        self.email = email or os.getenv('NBA_FANTASY_EMAIL')
        self.password = password or os.getenv('NBA_FANTASY_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError(
                "Email and password required. Set NBA_FANTASY_EMAIL and "
                "NBA_FANTASY_PASSWORD environment variables or pass as arguments."
            )
        
        # Configure Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = None
        self.wait = None
    
    def start_browser(self):
        """Start the Chrome browser."""
        print("Starting browser...")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        print("✓ Browser started")
    
    def login(self):
        """Log in to NBA Fantasy."""
        print("\nLogging in to NBA Fantasy...")
        self.driver.get('https://nbafantasy.nba.com/')
        
        time.sleep(3)  # Wait for page load
        
        # Handle cookie banner on landing page
        self.handle_cookie_banner()
        
        try:
            # Try multiple selectors for login button - using both XPath and CSS
            login_button = None
            login_selectors = [
                ("xpath", "//button[contains(text(), 'Login')]"),  # Exact match from debug
                ("xpath", "//button[text()='Login']"),
                ("xpath", "//a[contains(text(), 'Log In')]"),
                ("xpath", "//button[contains(text(), 'Log In')]"),
                ("xpath", "//a[contains(text(), 'Sign In')]"),
                ("xpath", "//button[contains(text(), 'Sign In')]"),
                ("css", "button:contains('Login')"),
                ("css", "a[href*='login']"),
                ("css", "button[class*='login']")
            ]
            
            for selector_type, selector in login_selectors:
                try:
                    if selector_type == "xpath":
                        login_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        login_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if login_button and login_button.is_displayed():
                        print(f"✓ Found login button: {selector}")
                        login_button.click()
                        print("✓ Clicked login button")
                        time.sleep(3)  # Wait for login form to appear
                        break
                except Exception as e:
                    continue
            
            if not login_button:
                print("⚠️  No login button found, assuming already on login page")
            
            # Enter email - try specific IDs first, then fallback
            email_selectors = [
                "input[id='loginEmail']",  # Specific ID found in debug
                "input[type='email']",
                "input[name='email']",
                "input[id='email']",
                "input[placeholder*='mail' i]"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_field and email_field.is_displayed():
                        print(f"✓ Found email field: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                raise Exception("Could not find email field")
            
            email_field.clear()
            email_field.send_keys(self.email)
            print("✓ Entered email")
            
            time.sleep(1)
            
            # Enter password
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[id='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                raise Exception("Could not find password field")
            
            password_field.clear()
            password_field.send_keys(self.password)
            print("✓ Entered password")
            
            time.sleep(1)
            
            # Click submit
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[class*='submit']",
                "button[class*='login']",
                "//button[contains(text(), 'Log In')]",
                "//button[contains(text(), 'Sign In')]"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if selector.startswith('//'):
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                raise Exception("Could not find submit button")
            
            submit_button.click()
            print("✓ Clicked submit")
            
            # Wait for successful login
            time.sleep(7)
            
            # Handle cookie banner if it appears after login
            self.handle_cookie_banner()
            
            print("✓ Logged in successfully")
            
        except Exception as e:
            print(f"✗ Login failed: {e}")
            self.save_screenshot('login_error.png')
            raise
    
    def handle_cookie_banner(self):
        """Handle cookie consent banner if it appears."""
        try:
            # Common cookie banner button selectors
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[id*='cookie']",
                "button[class*='cookie']",
                ".onetrust-close-btn-handler",
                "#onetrust-accept-btn-handler",
                "button:contains('Accept')",
                "button:contains('I Accept')",
                "button:contains('Accept All')",
                "button:contains('Got it')",
                "[aria-label*='Accept']",
                "[aria-label*='Close']"
            ]
            
            for selector in cookie_selectors:
                try:
                    # Wait briefly for cookie banner
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    print(f"✓ Dismissed cookie banner using: {selector}")
                    time.sleep(1)
                    return True
                except:
                    continue
            
            print("ℹ No cookie banner found (or already dismissed)")
            return False
        except Exception as e:
            print(f"ℹ Cookie banner handling: {e}")
            return False
    
    def scrape_salaries(self):
        """Scrape salary data from the statistics page."""
        print("\nNavigating to statistics page...")
        self.driver.get('https://nbafantasy.nba.com/statistics')
        
        time.sleep(3)  # Initial page load
        
        # Handle cookie banner if present
        self.handle_cookie_banner()
        
        time.sleep(2)  # Wait for page and data to load
        
        print("Scraping salary data...")
        
        try:
            # Wait for table to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .table, [role='table']"))
            )
            
            salary_data = []
            
            # Try multiple selectors for player rows
            row_selectors = [
                "table tbody tr",
                ".table tbody tr",
                "[role='table'] [role='row']",
                "table tr:has(td)"
            ]
            
            rows = []
            for selector in row_selectors:
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rows:
                        print(f"✓ Found {len(rows)} rows using selector: {selector}")
                        break
                except:
                    continue
            
            if not rows:
                raise Exception("Could not find player table rows")
            
            # Parse each row
            for idx, row in enumerate(rows[:10]):  # Test with first 10
                try:
                    # Get all cells in the row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 2:
                        continue
                    
                    # Extract player name and salary
                    # This will need adjustment based on actual HTML structure
                    player_name = cells[0].text.strip() if cells else ""
                    
                    # Salary is usually in a specific column (adjust index as needed)
                    salary_text = ""
                    for cell in cells:
                        text = cell.text.strip()
                        if '$' in text and 'M' in text.upper():
                            salary_text = text
                            break
                    
                    if player_name and salary_text:
                        # Parse salary (e.g., "$15.5M" -> 15.5)
                        salary = float(salary_text.replace('$', '').replace('M', '').replace('m', '').strip())
                        
                        salary_data.append({
                            'player_name': player_name,
                            'salary': salary
                        })
                        
                        if idx < 5:  # Print first 5 for verification
                            print(f"  {player_name}: ${salary}M")
                
                except Exception as e:
                    continue
            
            print(f"\n✓ Scraped {len(salary_data)} player salaries")
            return salary_data
            
        except Exception as e:
            print(f"✗ Scraping failed: {e}")
            self.save_screenshot('scrape_error.png')
            
            # Print page source snippet for debugging
            print("\nPage source snippet:")
            print(self.driver.page_source[:1000])
            
            raise
    
    def save_screenshot(self, filename):
        """Save screenshot for debugging."""
        try:
            filepath = f"/tmp/{filename}"
            self.driver.save_screenshot(filepath)
            print(f"Screenshot saved: {filepath}")
        except:
            pass
    
    def update_database(self, salary_data):
        """Update player salaries in the database."""
        print("\nUpdating database...")
        
        conn = get_connection()
        cur = conn.cursor()
        
        updated_count = 0
        not_found = []
        
        for item in salary_data:
            player_name = item['player_name']
            salary = item['salary']
            
            # Try to find player (fuzzy matching might be needed)
            cur.execute("""
                SELECT player_id FROM players 
                WHERE player_name LIKE ? OR player_name LIKE ?
            """, (f"%{player_name}%", player_name))
            
            result = cur.fetchone()
            
            if result:
                player_id = result[0]
                cur.execute("""
                    UPDATE players 
                    SET salary = ?, salary_updated_at = ?
                    WHERE player_id = ?
                """, (salary, datetime.now().isoformat(), player_id))
                updated_count += 1
            else:
                not_found.append(player_name)
        
        conn.commit()
        conn.close()
        
        print(f"✓ Updated {updated_count} players")
        
        if not_found:
            print(f"\n⚠ Could not match {len(not_found)} players:")
            for name in not_found[:10]:
                print(f"  • {name}")
            if len(not_found) > 10:
                print(f"  ... and {len(not_found) - 10} more")
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")


def main():
    """Main function to run the scraper."""
    scraper = NBAFantasySalaryScraper(headless=False)  # Set to True for production
    
    try:
        scraper.start_browser()
        scraper.login()
        
        # Give user time to handle any 2FA or captcha
        print("\n⏸ Pausing for 10 seconds (handle any 2FA/captcha if needed)...")
        time.sleep(10)
        
        salary_data = scraper.scrape_salaries()
        
        if salary_data:
            scraper.update_database(salary_data)
        else:
            print("\n✗ No salary data scraped")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
