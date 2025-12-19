import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- Configuration ---
URL_CART = "https://bandwagonhost.com/cart.php"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/vps_data.json")

# --- The "Golden List" (Extracted from Competitor Source) ---
# Format: PID -> Details
PLAN_DB = {
    # Japan Tokyo
    "162": {"name": "日本东京限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "2.5Gbps", "loc": "日本东京 DC39v2，三网直连", "price": "$79/年"},
    "163": {"name": "日本东京限量版 v2", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "1000GB", "speed": "5Gbps", "loc": "日本东京 DC39v2，三网直连", "price": "$99/年"},
    
    # Amsterdam
    "159": {"name": "荷兰阿姆斯特丹限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "荷兰阿姆斯特丹，三网回程 CN2 GIA", "price": "$39/年"},
    
    # Fremont / US
    "158": {"name": "MINICHICKEN 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "1Gbps", "loc": "美国弗里蒙特 HE 线路", "price": "$19/年"},
    "130": {"name": "THE CHICKEN 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "弗里蒙特 FMT8（联通 AS4837）", "price": "$39.99/年"},
    
    # Los Angeles DC1 / CMIN2
    "157": {"name": "MegaBox Pro 限量版", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "2000GB", "speed": "2.5Gbps", "loc": "美国洛杉矶 DC1（CN2 GIA/CMIN2/9929）", "price": "$49/年"},
    "156": {"name": "BiggerBox Pro 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "美国洛杉矶 DC1（CN2 GIA/CMIN2/9929）", "price": "$39/年"},
    "153": {"name": "POWERBOX 限量版", "cpu": "1核", "ram": "1536 MB", "disk": "30GB", "bw": "1500GB", "speed": "2.5Gbps", "loc": "美国洛杉矶 DC1", "price": "$45/年"},

    # Japan Regular/Limited
    "154": {"name": "SAKURABOX 限量版", "cpu": "1核", "ram": "1GB", "disk": "30GB", "bw": "500GB", "speed": "1Gbps", "loc": "日本东京 DC39（三网 CMI）", "price": "$79/年"},
    "104": {"name": "日本大阪软银 10G 限量版", "cpu": "1核", "ram": "512MB", "disk": "10GB", "bw": "500GB", "speed": "1Gbps", "loc": "日本大阪软银 JPOS_1", "price": "$69.99/年"},
    "146": {"name": "日本大阪软银 40G 限量版", "cpu": "1核", "ram": "2GB", "disk": "40GB", "bw": "2000GB", "speed": "2.5Gbps", "loc": "日本大阪软银 JPOS_1", "price": "$79.99/年"},

    # THE PLAN Series
    "149": {"name": "THE DC6 PLAN 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "DC6 CN2 GIA-E", "price": "$53/年"},
    "147": {"name": "THE PLAN 限量版", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "19机房可选 (含GIA/软银/HK85)", "price": "$99/年"},
    "131": {"name": "THE PLAN v2 限量版", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "2000GB", "speed": "2.5Gbps", "loc": "19机房可选 (含GIA/软银/HK85)", "price": "$119/年"},
    "133": {"name": "FREEDOM PLAN 限量版", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "2000GB", "speed": "2.5Gbps", "loc": "DC2 AO (Coresite)", "price": "$89/年"},

    # DC9 / CN2 GIA Limited
    "145": {"name": "DC9 CN2 GIA 限量版 (Lite)", "cpu": "1核", "ram": "768MB", "disk": "15GB", "bw": "750GB", "speed": "1.5Gbps", "loc": "DC9 CN2 GIA", "price": "$38/年"},
    "112": {"name": "DC9 CN2 GIA 限量版 (V1)", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "DC9 CN2 GIA", "price": "$79.99/年"},
    "143": {"name": "DC9 CN2 GIA 限量版 (V2)", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "1000GB", "speed": "1Gbps", "loc": "DC9 CN2 GIA", "price": "$79.99/年"},
    
    # CN2 GIA-E Series
    "94":  {"name": "CN2 GIA-E 10G 限量版", "cpu": "1核", "ram": "512MB", "disk": "10GB", "bw": "500GB", "speed": "1Gbps", "loc": "DC6/DC9/软银等 15 机房", "price": "$49.99/年"},
    "105": {"name": "CN2 GIA-E 20G 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "DC6/DC9/软银等 15 机房", "price": "$89.99/年"},
    "132": {"name": "CN2 GIA-E 40G 限量版", "cpu": "2核", "ram": "2GB", "disk": "40GB", "bw": "1000GB", "speed": "2.5Gbps", "loc": "DC6/DC9/软银等 15 机房", "price": "$89.90/年"},

    # Hong Kong & Others
    "121": {"name": "中国香港 HK85 限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "中国香港 HK85（移动 CMI）", "price": "$79.99/年"},
    "126": {"name": "悉尼限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "500GB", "speed": "1Gbps", "loc": "悉尼机房（联通 AS9929）", "price": "$99.99/年"},
    "113": {"name": "迪拜限量版", "cpu": "1核", "ram": "1GB", "disk": "20GB", "bw": "250GB", "speed": "1Gbps", "loc": "迪拜 (含CN2 GIA/软银等)", "price": "$99.99/年"},
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def check_stock_status(pid):
    """
    Check stock for a specific PID.
    """
    check_url = f"https://bandwagonhost.com/cart.php?a=add&pid={pid}"
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        r = s.get(check_url, timeout=10)
        
        # Logic: If redirection to 'confproduct' happens, it's alive.
        # If text contains "Out of Stock" or redirects to main cart with message, it's dead.
        
        if "Out of Stock" in r.text or "此产品缺货" in r.text:
            return False
            
        if "cart.php?a=confproduct" in r.url:
            return True
            
        return False
        
    except Exception as e:
        print(f"Error checking PID {pid}: {e}")
        return False

def get_standard_aff_link(pid):
    # Using bwh81.net consistent with competitor
    return f"https://bwh81.net/aff.php?aff=78435&pid={pid}"

def scrape():
    print("Starting Comprehensive Limited Edition Scrape...")
    final_list = []
    
    # Iterate through our manually curated Golden List
    for pid, info in PLAN_DB.items():
        is_in_stock = check_stock_status(pid)
        print(f"[{pid}] {info['name']}: {'YES' if is_in_stock else 'NO'}")
        
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
            "link": get_standard_aff_link(pid)
        }
        final_list.append(item)
        time.sleep(1) # Gentle delay

    # Save
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
