#!/usr/bin/env python3
"""Debug script to find all pagination buttons"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    driver.get('https://nbafantasy.nba.com/statistics')
    time.sleep(3)
    
    # Dismiss cookie
    try:
        cookie_btn = driver.find_element(By.CSS_SELECTOR, "button[id*='accept']")
        cookie_btn.click()
        time.sleep(2)
    except:
        pass
    
    time.sleep(2)
    
    # Count initial rows
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"Initial rows: {len(rows)}\n")
    
    # Find all buttons with the class
    buttons = driver.find_elements(By.CSS_SELECTOR, "button.sc-jrVwZP.gHULxL")
    print(f"Found {len(buttons)} buttons with class 'sc-jrVwZP gHULxL'\n")
    
    for i, btn in enumerate(buttons):
        try:
            location = btn.location
            size = btn.size
            is_displayed = btn.is_displayed()
            parent = btn.find_element(By.XPATH, "..")
            parent_tag = parent.tag_name
            parent_class = parent.get_attribute('class')
            
            print(f"Button {i+1}:")
            print(f"  Location: x={location['x']}, y={location['y']}")
            print(f"  Size: {size['width']}x{size['height']}")
            print(f"  Displayed: {is_displayed}")
            print(f"  Parent: <{parent_tag} class='{parent_class}'>")
            print()
        except:
            pass
    
    # Scroll to bottom
    print("Scrolling to bottom...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    # Look for button at bottom
    buttons_bottom = driver.find_elements(By.CSS_SELECTOR, "button.sc-jrVwZP.gHULxL")
    print(f"\nButtons after scroll: {len(buttons_bottom)}")
    
    # Find button that's likely pagination (near bottom of page)
    page_height = driver.execute_script("return document.body.scrollHeight")
    print(f"Page height: {page_height}px\n")
    
    for i, btn in enumerate(buttons_bottom):
        try:
            location = btn.location
            if location['y'] > page_height * 0.7:  # In bottom 30% of page
                print(f"Bottom button {i+1}: y={location['y']} (likely pagination)")
        except:
            pass
    
    driver.save_screenshot('/tmp/buttons_debug.png')
    print(f"\nScreenshot: /tmp/buttons_debug.png")
    print("Browser will stay open for 20 seconds...")
    time.sleep(20)
    
finally:
    driver.quit()
