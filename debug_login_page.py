#!/usr/bin/env python3
"""
Debug script to inspect NBA Fantasy login page structure
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Setup
options = Options()
# options.add_argument('--headless')  # Commented out to see browser
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

print("🔍 NBA Fantasy Page Inspector")
print("="*60)

driver = webdriver.Chrome(options=options)

try:
    print("\n1. Loading page...")
    driver.get('https://nbafantasy.nba.com/')
    time.sleep(3)
    
    # Handle cookie banner
    print("2. Looking for cookie banner...")
    try:
        cookie_btn = driver.find_element(By.CSS_SELECTOR, "button[id*='accept']")
        cookie_btn.click()
        print("   ✓ Dismissed cookie banner")
        time.sleep(2)
    except:
        print("   ℹ No cookie banner found")
    
    # Check for login button/link
    print("\n3. Looking for login button/link...")
    login_elements = driver.find_elements(By.XPATH, "//a[contains(text(), 'Log')] | //button[contains(text(), 'Log')] | //a[contains(text(), 'Sign')] | //button[contains(text(), 'Sign')]")
    if login_elements:
        print(f"   ✓ Found {len(login_elements)} login-related elements:")
        for elem in login_elements:
            print(f"     - {elem.tag_name}: '{elem.text}' (visible: {elem.is_displayed()})")
    else:
        print("   ⚠ No login button/link found")
    
    # Check if we're already on a login form
    print("\n4. Looking for email input...")
    email_selectors = [
        "input[type='email']",
        "input[name='email']", 
        "input[id='email']",
        "input[placeholder*='mail' i]"
    ]
    
    for selector in email_selectors:
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, selector)
            if email_field.is_displayed():
                print(f"   ✓ Found email field: {selector}")
                print(f"     ID: {email_field.get_attribute('id')}")
                print(f"     Name: {email_field.get_attribute('name')}")
                print(f"     Type: {email_field.get_attribute('type')}")
                break
        except:
            continue
    else:
        print("   ⚠ No email field found on current page")
    
    # Save screenshot
    screenshot_path = '/tmp/nba_fantasy_page_debug.png'
    driver.save_screenshot(screenshot_path)
    print(f"\n📸 Screenshot saved: {screenshot_path}")
    
    # Get page source for inspection
    page_source = driver.page_source
    if 'email' in page_source.lower():
        print("✓ Page source contains 'email'")
    if 'login' in page_source.lower():
        print("✓ Page source contains 'login'")
    if 'sign in' in page_source.lower():
        print("✓ Page source contains 'sign in'")
    
    print("\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
    print("   Check the browser window to see the actual page")
    time.sleep(30)
    
finally:
    driver.quit()
    print("\n✓ Done")
