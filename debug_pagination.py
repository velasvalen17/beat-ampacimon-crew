#!/usr/bin/env python3
"""
Debug script to find pagination button on NBA Fantasy statistics page
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
# options.add_argument('--headless')  # Commented to see browser
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    print("Loading page...")
    driver.get('https://nbafantasy.nba.com/statistics')
    time.sleep(3)
    
    # Dismiss cookie
    try:
        cookie_btn = driver.find_element(By.CSS_SELECTOR, "button[id*='accept']")
        cookie_btn.click()
        time.sleep(2)
    except:
        pass
    
    time.sleep(3)
    
    # Count initial rows
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"\nInitial rows: {len(rows)}")
    
    # Look for any buttons below the table
    print("\nLooking for buttons...")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"Found {len(buttons)} buttons on page")
    
    for i, btn in enumerate(buttons):
        try:
            text = btn.text.strip()
            is_displayed = btn.is_displayed()
            classes = btn.get_attribute('class')
            if is_displayed and text:
                print(f"  Button {i+1}: '{text}' (class: {classes})")
        except:
            pass
    
    # Scroll to bottom to trigger lazy loading
    print("\nScrolling to bottom...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Check for new rows
    rows_after = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"Rows after scroll: {len(rows_after)}")
    
    # Take screenshot
    driver.save_screenshot('/tmp/pagination_debug.png')
    print(f"\nScreenshot: /tmp/pagination_debug.png")
    
    print("\nBrowser will stay open for 15 seconds...")
    time.sleep(15)
    
finally:
    driver.quit()
