#!/usr/bin/env python3
"""
Simple test - no login needed, directly scrape statistics page
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("🏀 NBA FANTASY SALARY TEST - DIRECT ACCESS")
print("="*60)

options = Options()
# options.add_argument('--headless')  # Comment out to see browser
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    print("\n1. Navigating directly to statistics page...")
    driver.get('https://nbafantasy.nba.com/statistics')
    time.sleep(3)
    
    print("2. Handling cookie banner...")
    try:
        cookie_btn = driver.find_element(By.CSS_SELECTOR, "button[id*='accept']")
        cookie_btn.click()
        print("   ✓ Dismissed cookie banner")
        time.sleep(2)
    except:
        print("   ℹ No cookie banner")
    
    print("\n3. Looking for salary data table...")
    time.sleep(3)  # Wait for data to load
    
    # Find table rows
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"   ✓ Found {len(rows)} players in table")
    
    if len(rows) == 0:
        print("\n⚠️  No table rows found. Let me try alternative selectors...")
        # Try other common table structures
        rows = driver.find_elements(By.CSS_SELECTOR, "tr[role='row']")
        print(f"   Found {len(rows)} rows with role='row'")
    
    print("\n4. Searching for Jokic...")
    jokic_found = False
    
    for i, row in enumerate(rows):
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            
            # Get all cell text
            row_text = " ".join([cell.text for cell in cells]).lower()
            
            if "jokic" in row_text:
                print(f"\n✅ FOUND JOKIC IN ROW {i+1}!")
                print("="*60)
                
                # Print all cell values to see the structure
                for j, cell in enumerate(cells):
                    text = cell.text.strip()
                    if text:
                        print(f"   Column {j+1}: {text}")
                
                print("="*60)
                jokic_found = True
                break
                
        except Exception as e:
            continue
    
    if not jokic_found:
        print("\n⚠️  Jokic not found. Showing first 3 rows for debugging:")
        for i, row in enumerate(rows[:3]):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                print(f"\n   Row {i+1}:")
                for j, cell in enumerate(cells[:8]):  # First 8 columns
                    print(f"      Col {j+1}: {cell.text[:30]}")
            except:
                pass
    
    # Save screenshot
    driver.save_screenshot('/tmp/nba_statistics_page.png')
    print(f"\n📸 Screenshot saved: /tmp/nba_statistics_page.png")
    
    print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
    time.sleep(10)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    driver.save_screenshot('/tmp/statistics_error.png')
    
finally:
    driver.quit()
    print("\n✓ Done")
