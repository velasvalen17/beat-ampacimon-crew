#!/usr/bin/env python3
"""
Manual test - allows you to handle 2FA/CAPTCHA interactively
Then proceeds to scrape Jokic's salary
"""

from salary_scraper import NBAFantasySalaryScraper
import time

print("🏀 NBA FANTASY SALARY TEST - NIKOLA JOKIĆ (Interactive)")
print("="*60)

scraper = NBAFantasySalaryScraper(headless=False)

try:
    print("\n[1/5] Starting browser...")
    scraper.start_browser()
    
    print("\n[2/5] Logging in...")
    scraper.login()
    
    print("\n[3/5] Waiting for you to complete any 2FA/CAPTCHA...")
    print("      Check the browser window and complete authentication if needed.")
    print("      Press ENTER when you're logged in and ready to continue...")
    input()
    
    print("\n[4/5] Scraping salary data...")
    print("      This may take 30-60 seconds...")
    salaries = scraper.scrape_salaries()
    
    print(f"\n[5/5] Results:")
    print(f"✓ Successfully scraped {len(salaries)} players\n")
    
    # Find Jokic
    jokic_data = [s for s in salaries if 'jokic' in s[0].lower()]
    
    print("="*60)
    if jokic_data:
        print("✅ NIKOLA JOKIĆ FOUND!")
        print("="*60)
        for name, salary in jokic_data:
            print(f"📊 Player: {name}")
            print(f"💰 Salary: ${salary}M")
        print("="*60)
    else:
        print("⚠️  NIKOLA JOKIĆ NOT FOUND IN RESULTS")
        print("="*60)
        print("\nFirst 10 players found:")
        for name, salary in salaries[:10]:
            print(f"  • {name}: ${salary}M")
    
    print("\n✓ Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nClosing browser in 5 seconds...")
    time.sleep(5)
    scraper.close()
    print("✓ Done")
