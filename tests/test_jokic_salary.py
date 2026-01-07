#!/usr/bin/env python3
"""
Quick test to retrieve Nikola Jokic's fantasy salary - IMPROVED VERSION
Handles cookie banners and multiple page structures
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from salary_scraper import NBAFantasySalaryScraper

load_dotenv()

def test_jokic_salary():
    """Test scraping Jokic's salary with improved cookie handling."""
    print("🏀 NBA FANTASY SALARY TEST - NIKOLA JOKIĆ")
    print("="*60)
    print("ℹ️  Using IMPROVED scraper with cookie banner handling")
    print("="*60)
    
    # Create scraper (visible browser for debugging)
    scraper = NBAFantasySalaryScraper(headless=False)
    
    try:
        print("\n[1/4] Starting browser...")
        scraper.start_browser()
        
        print("\n[2/4] Logging in...")
        print("ℹ️  Cookie banners will be handled automatically")
        print("ℹ️  If you see 2FA/CAPTCHA, please complete it manually")
        scraper.login()
        
        print("\n[3/4] Scraping salary data...")
        print("ℹ️  This may take 30-60 seconds...")
        salaries = scraper.scrape_salaries()
        
        print(f"\n[4/4] Processing results...")
        print(f"✓ Successfully scraped {len(salaries)} players")
        
        # Find Jokic
        jokic_data = [s for s in salaries if 'jokic' in s[0].lower()]
        
        print("\n" + "="*60)
        if jokic_data:
            print("✅ NIKOLA JOKIĆ FOUND!")
            print("="*60)
            for name, salary in jokic_data:
                print(f"📊 Player: {name}")
                print(f"💰 Salary: ${salary}M")
            print("="*60)
        else:
            print("⚠️  NIKOLA JOKIĆ NOT FOUND")
            print("="*60)
            print("\nSample of scraped players:")
            for name, salary in salaries[:10]:
                print(f"  • {name}: ${salary}M")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check screenshot: /tmp/login_error.png (if login failed)")
        print("2. Verify credentials in .env file")
        print("3. Try running with manual intervention for CAPTCHA")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n\n🔄 Closing browser...")
        scraper.close()
        print("✓ Done")

if __name__ == '__main__':
    success = test_jokic_salary()
    sys.exit(0 if success else 1)
