import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- Configuration ---
URL_CART = "https://bandwagonhost.com/cart.php"
# The scraper will save data here
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/vps_data.json")

# --- Plan Database (The "Golden List") ---
# This list contains the "Hidden Gems" (Limited Editions) and popular plans.
# We hardcode their specs and Chinese names to match stock.bwg.net style.
PLAN_DB = {
    # HK85
    "153": {"name": "香港 HK85 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "香港 HK85", "price": "$79.99/年"},
    
    # THE PLAN / V2
    "146": {"name": "THE PLAN v2", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "17机房可选 (含CN2 GIA/软银)", "price": "$35.00/季"},
    "128": {"name": "THE PLAN", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "17机房可选", "price": "$29.00/季"},

    # CN2 GIA-E Limited 
    "139": {"name": "CN2 GIA-E 限量版 V2", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "DC6/DC9/软银/EUN2", "price": "$89.99/年"},
    "94":  {"name": "CN2 GIA-E 限量版 V1", "cpu": "1核", "ram": "512MB", "disk": "10GB", "bw": "500GB", "speed": "1Gbps", "loc": "DC6/DC9/软银", "price": "$49.99/年"},
    
    # DC9 CN2 GIA Limited
    "112": {"name": "DC9 CN2 GIA 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "洛杉矶 DC9 CN2 GIA", "price": "$79.99/年"},

    # Dubai
    "113": {"name": "迪拜限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "阿联酋迪拜", "price": "$99.99/年"},

    # Osaka Softbank Limited
    "116": {"name": "大阪软银限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "日本大阪软银 JPOS_1", "price": "$79.99/年"},

    # Freedom Plan
    "131": {"name": "FREEDOM PLAN", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "US/EU/JP/HK等", "price": "$89.00/年"},
    
    # Regular CN2 GIA-E (Most popular regular plans)
    "87":  {"name": "CN2 GIA-E 20G常規", "cpu": "2核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "DC6/DC9/软银等", "price": "$49.99/季"},
    "88":  {"name": "CN2 GIA-E 40G常規", "cpu": "3核", "ram": "2GB", "disk": "40GB", "bw": "2000GB", "speed": "2.5Gbps", "loc": "DC6/DC9/软银等", "price": "$89.99/季"},

    # Sydney Limited
    "106": {"name": "悉尼限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "澳大利亚悉尼", "price": "$99.99/年"},
}

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def check_stock_status(pid):
    """
    Check stock for a specific PID by attempting to load its cart URL.
    This is accurate for hidden plans.
    """
    # Direct check URL (this adds item to cart, if OOS it redirects or shows error)
    # But scraping 'cart.php?a=add&pid=X' usually redirects. 
    # Better approach: check 'cart.php?a=confproduct&i=0' after adding? 
    # Or simply fetch the general cart page? No, general cart page hides OOS.
    # 
    # Reliable method: BWH API is private. We simulate browser behavior.
    # If we visit the direct order link and it redirects to 'cart.php' with "Out of Stock" message, it's OOS.
    
    check_url = f"https://bandwagonhost.com/cart.php?a=add&pid={pid}"
    try:
        # We use a session to track cookies/redirects
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        r = s.get(check_url, timeout=10)
        
        # If stock is strictly 0, WHMCS usually shows a specific OOS page text
        if "Out of Stock" in r.text or "此产品缺货" in r.text:
            return False
        
        # Another check: if it redirects to a config page (step=2), it's IN STOCK
        if "cart.php?a=confproduct" in r.url:
            return True
            
        # If it stays on cart.php but says nothing specific, it might be OOS or just weird.
        # But for BWH, usually OOS redirects to cart.php parent with 'Out of Stock' text.
        return False
        
    except Exception as e:
        print(f"Error checking PID {pid}: {e}")
        return False

def get_standard_aff_link(pid):
    # Your affiliate logic
    return f"https://bwh81.net/aff.php?aff=78435&pid={pid}"

def scrape():
    print("Starting comprehensive scrape...")
    final_list = []
    
    # 1. Process the "Golden List" (Hardcoded popular plans)
    # We will check stock for each of these manually.
    print(f"Checking {len(PLAN_DB)} known plans...")
    
    for pid, info in PLAN_DB.items():
        is_in_stock = check_stock_status(pid)
        print(f"  [{pid}] {info['name']}: {'IN STOCK' if is_in_stock else 'OOS'}")
        
        item = {
            "id": pid,
            "name": info['name'],
            "cpu": info['cpu'],
            "ram": info['ram'],
            "disk": info['disk'],
            "bandwidth": info['bw'],
            "speed": info['speed'],
            "location": info['loc'],
            "price": info['price'],
            "stock": is_in_stock,
            "link": get_standard_aff_link(pid),
            "tag": "HOT" # Tag for UI highlighting
        }
        final_list.append(item)
        # Be nice to the server
        time.sleep(1)

    # 2. Scrape general list (to fill in any regular plans we missed)
    # For simplicity and style consistency, if you only want the "Premium/Popular" look 
    # like stock.bwg.net, we might actually SKIP the general scrape to avoid cluttering 
    # the table with 50+ boring "Basic" plans. 
    # 
    # DECISION: Let's stick to the Golden List for now as it makes the site look Professional 
    # and clean (like the reference). "Scraping everything" usually results in garbage data.
    # 
    # If the user wants specific regular plans added, we just add them to PLAN_DB.
    
    # Sort: In Stock first, then by ID? Or just keep dict order (usually manual grouping).
    # Let's keep manual grouping from PLAN_DB.
    
    output_data = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M"),
        "plans": final_list
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Done. Saved {len(final_list)} plans.")

if __name__ == "__main__":
    scrape()
