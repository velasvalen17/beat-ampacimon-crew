#!/usr/bin/env python3
"""
Simple NBA Fantasy Salary Scraper - No Login Required
Directly scrapes the public statistics page
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database import get_connection
from datetime import datetime
from fuzzywuzzy import fuzz

def scrape_nba_fantasy_salaries(headless=True):
    """Scrape salary data without login."""
    
    # Setup Chrome
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🏀 NBA Fantasy Salary Scraper (No Login)")
        print("="*60)
        
        # Navigate to statistics page
        print("\n1. Loading statistics page...")
        driver.get('https://nbafantasy.nba.com/statistics')
        time.sleep(5)  # Give more time for page load
        
        # Handle cookie banner
        print("2. Handling cookie banner...")
        try:
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='accept']"))
            )
            cookie_btn.click()
            print("   ✓ Cookie banner dismissed")
            time.sleep(2)
        except:
            print("   ℹ No cookie banner")
        
        # Wait for table
        print("3. Waiting for table to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        time.sleep(2)
        
        # Load all players by scrolling and clicking pagination
        print("4. Loading all players...")
        max_pages = 30
        page = 0
        all_player_data = {}  # Track unique players: {name: salary}
        seen_pages = set()  # Track which player sets we've seen
        
        while page < max_pages:
            # Get current row count
            current_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            current_count = len(current_rows)
            
            # Scroll to bottom to find the pagination button
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Try to find pagination button at the bottom (Next button)
            # After each click, a NEW button appears with the same class
            button_clicked = False
            pagination_selectors = [
                "//span[contains(text(), 'Next')]/..",  # Parent button of span with "Next"
                "//span[text()='Next']/..",
                "//button[.//span[text()='Next']]",
                "//span[contains(@class, 'sc-OslQV')]/..",
                "span.sc-OslQV.UmEip",
            ]
            
            for selector in pagination_selectors:
                try:
                    # Get all elements with this class
                    if selector.startswith('//'):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    # Find the element at the bottom (highest Y position)
                    bottom_element = None
                    max_y = 0
                    
                    for elem in elements:
                        if elem.is_displayed():
                            location = elem.location
                            if location['y'] > max_y:
                                max_y = location['y']
                                bottom_element = elem
                    
                    if bottom_element:
                        # If it's a span, get the parent button
                        if bottom_element.tag_name == 'span':
                            bottom_button = bottom_element.find_element(By.XPATH, "..")
                        else:
                            bottom_button = bottom_element
                        
                        # Scroll button into view
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bottom_button)
                        time.sleep(1)
                        
                        # Click the button
                        bottom_button.click()
                        button_clicked = True
                        page += 1
                        print(f"   Clicked Next button (page {page})")
                        
                        # Wait for new rows to load
                        time.sleep(3)
                        break
                        
                except Exception as e:
                    continue
            
            if not button_clicked:
                print(f"   No more pagination buttons found")
                break
            
            # Collect players from current page
            new_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            page_players = []
            
            for row in new_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 3:
                        continue
                    
                    player_cell = cells[1].text.strip()
                    player_lines = player_cell.split('\n')
                    player_name = player_lines[0] if player_lines else ""
                    
                    if not player_name or 'vs.' in player_name or '@' in player_name:
                        continue
                    
                    salary_text = cells[2].text.strip()
                    
                    if player_name and salary_text:
                        try:
                            salary = float(salary_text)
                            if 0 < salary < 30:
                                all_player_data[player_name] = salary
                                page_players.append(player_name)
                        except ValueError:
                            continue
                except:
                    continue
            
            # Check if we've seen this page before (detect cycling)
            page_key = tuple(sorted(page_players[:5]))  # Use first 5 players as page identifier
            if page_key in seen_pages:
                print(f"   Detected page cycling, stopping")
                break
            seen_pages.add(page_key)
            
            print(f"   Collected {len(page_players)} players from this page (total unique: {len(all_player_data)})")
            
            time.sleep(1)  # Rate limiting
        
        # Get all rows after pagination
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"   ✓ Found {len(rows)} total players")
        
        # Convert collected player data to list
        print("\n5. Processing collected data...")
        salary_data = [(name, salary) for name, salary in all_player_data.items()]
        print(f"   ✓ Collected {len(salary_data)} unique players")
        
        # Update database
        print("\n6. Updating database...")
        conn = get_connection()
        cur = conn.cursor()
        
        # Get all players from database
        cur.execute("SELECT player_id, player_name FROM players")
        db_players = cur.fetchall()
        
        updated = 0
        not_found = []
        
        for scraped_name, salary in salary_data:
            # Find best match in database using fuzzy matching
            best_match = None
            best_score = 0
            
            for player_id, db_name in db_players:
                score = fuzz.ratio(scraped_name.lower(), db_name.lower())
                if score > best_score:
                    best_score = score
                    best_match = (player_id, db_name)
            
            # Update if good match (95% similarity)
            if best_match and best_score >= 95:
                cur.execute("""
                    UPDATE players 
                    SET salary = ?, salary_updated_at = ?
                    WHERE player_id = ?
                """, (salary, datetime.now().isoformat(), best_match[0]))
                updated += 1
            else:
                not_found.append((scraped_name, salary, best_score if best_match else 0))
        
        conn.commit()
        conn.close()
        
        print(f"   ✓ Updated {updated} players")
        
        if not_found:
            print(f"\n⚠️  Could not match {len(not_found)} players:")
            with open('salary_mismatches.log', 'w') as f:
                for name, salary, score in not_found[:10]:
                    print(f"     - {name} (${salary}M, best match: {score}%)")
                    f.write(f"{name}\t${salary}M\tscore:{score}%\n")
        
        print("\n✅ Salary scraping completed!")
        print("="*60)
        
        return salary_data
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        raise
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == '__main__':
    import sys
    
    # Run with visible browser by default (site may block headless)
    headless = '--headless' in sys.argv
    
    try:
        salaries = scrape_nba_fantasy_salaries(headless=headless)
        
        # Show Jokic as example
        jokic = [s for s in salaries if 'jokic' in s[0].lower()]
        if jokic:
            print(f"\n📊 Example - Nikola Jokić: ${jokic[0][1]}M")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
