import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- Configuration ---
URL_CART = "https://bandwagonhost.com/cart.php"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/vps_data.json")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- The "Golden List" (Limited/Hidden Plans) ---
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

def clean_text(text):
    return text.strip() if text else ""

def get_standard_aff_link(pid):
    return f"https://bwh81.net/aff.php?aff=78435&pid={pid}"

def check_stock_status(pid):
    check_url = f"https://bandwagonhost.com/cart.php?a=add&pid={pid}"
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": USER_AGENT})
        r = s.get(check_url, timeout=10)
        
        if "Out of Stock" in r.text or "此产品缺货" in r.text:
            return False
        if "cart.php?a=confproduct" in r.url:
            return True
        return False # Default to false if unsure
    except Exception as e:
        print(f"Error checking PID {pid}: {e}")
        return False

def parse_specs_from_cart(desc_text):
    specs = {"cpu": "N/A", "ram": "N/A", "disk": "N/A", "bw": "N/A", "speed": "N/A", "loc": "多机房"}
    lines = desc_text.split('\n')
    for line in lines:
        line = line.strip()
        if "CPU" in line: specs['cpu'] = line.replace("CPU:", "").strip()
        elif "RAM" in line: specs['ram'] = line.replace("RAM:", "").strip()
        elif "SSD" in line: specs['disk'] = line.replace("SSD:", "").strip()
        elif "Transfer" in line: specs['bw'] = line.replace("Transfer:", "").strip()
        elif "Link speed" in line: specs['speed'] = line.replace("Link speed:", "").strip()
        # Location heuristic
        if "Location" in line and "routed" not in line:
            specs['loc'] = line.replace("Location:", "").strip()
    return specs

def parse_numeric(text, unit_map={'gb': 1, 'mb': 0.001, 'tb': 1000}):
    """Extract numeric value from string like '1024 MB', '1 TB', '$49.99'"""
    if not text: return 0.0
    text = text.lower().replace(',', '')
    match = re.search(r'([\d\.]+)\s*([a-z]+)?', text)
    if not match: return 0.0
    val = float(match.group(1))
    unit = match.group(2)
    if unit and unit in unit_map:
        val *= unit_map[unit]
    return val

def calculate_score(item):
    """
    Calculate a Value Score (0-10+) based on specs/price ratio.
    Formula: (Hardware_Score * Route_Multiplier) / Annual_Price
    """
    try:
        # 1. Parse Cost
        price_str = item['price'].replace('$', '').replace('/年', '').replace('/季', '')
        price = float(price_str)
        if price <= 0: return 0
        
        # Normalize to Yearly Price if quarterly
        if '/季' in item['price']:
            price *= 4
            
        # 2. Parse Specs
        ram = parse_numeric(item['ram'], {'gb': 1, 'mb': 0.00097}) # GB as base
        disk = parse_numeric(item['disk'], {'gb': 1, 'tb': 1000})
        # Bandwidth: '500GB' -> 0.5 TB
        bw = parse_numeric(item['bandwidth'], {'gb': 0.001, 'tb': 1})
        
        # 3. Hardware Score (Base Performance)
        # Weights: RAM (x10), Bandwidth (x25 - TRAFFIC IS KING), Disk (x0.3)
        hw_score = (ram * 10) + (bw * 25) + (disk * 0.3)
        
        # 4. Route Multiplier (The "Premium" Factor)
        multiplier = 1.0
        name = item['name'].upper()
        if "HK85" in name or "HONG KONG" in name: multiplier = 3.5 
        elif "GIA" in name or "PLAN" in name or "SOFTBANK" in name or "GIA-E" in name: multiplier = 1.8
        elif "LIMITED" in name or "限量" in name: multiplier = 1.6
        # Special boost for the "MiniChicken" style non-GIA but super cheap plans handled naturally by price formula
        
        # 5. Final Calculation
        # Use Price^1.3 to heavily favor sub-$50 plans
        raw_score = (hw_score * multiplier) / (price ** 1.3)
        
        # Scale to a 0-10 range (approx, max point is around 19$-1T plan)
        final_score = round(raw_score * 20, 1) # Scaling factor adjusted for new formula
        
        return final_score
    except:
        return 0

def scrape():
    print("Starting Hybrid Scrape (Golden List + Public Cart)...")
    final_list = []
    seen_pids = set()

    # 1. First, process the Golden List (Priority items)
    print("--- Phase 1: Checking Limited Editions ---")
    for pid, info in PLAN_DB.items():
        is_in_stock = check_stock_status(pid)
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
            "type": "Limited"
        }
        item['score'] = calculate_score(item) # Calc Score
        final_list.append(item)
        seen_pids.add(pid)
        print(f"[{pid}] {info['name']}: {is_in_stock} (Score: {item['score']})")
        time.sleep(0.5)

    # 2. Second, scrape the public Cart.php for EVERYTHING else
    print("--- Phase 2: Scraping Public Cart ---")
    try:
        resp = requests.get(URL_CART, headers={"User-Agent": USER_AGENT}, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        cart_boxes = soup.find_all('div', class_='cartbox')
        
        print(f"Found {len(cart_boxes)} public plans.")
        
        for box in cart_boxes:
            # Extract PID from onclick or link
            # window.location='cart.php?a=add&pid=44'
            button = box.find('input', attrs={'type': 'button'})
            pid = None
            
            if button:
                onclick = button.get('onclick', '')
                match = re.search(r'pid=(\d+)', onclick)
                if match:
                    pid = match.group(1)
            
            # If we already have this PID from Golden List, SKIP IT (Golden List has better Chinese names)
            if pid and pid in seen_pids:
                continue

            # Extract details
            name = box.find('strong').get_text(strip=True) if box.find('strong') else "Unknown Plan"
            
            # Translate common English names to Chinese roughly
            if "Basic VPS - Self-managed" in name:
                name = name.replace("Basic VPS - Self-managed - ", "").replace("KVM", "常规 KVM")
            
            full_price = box.find('td', class_='pricing').get_text(strip=True) if box.find('td', class_='pricing') else "N/A"
            price = re.search(r'\$[\d\.]+', full_price).group(0) + "/年" if "$" in full_price else full_price
            if "Quarterly" in full_price: price = price.replace("/年", "/季")

            specs_node = box.find('td')
            specs = parse_specs_from_cart(specs_node.get_text(separator="\n"))
            
            # Public list items are usually IN STOCK if they appear here
            # But double check "Order Now" button text
            stock = True
            if button and "Out of Stock" in button.get('value', ''):
                stock = False

            item = {
                "id": pid if pid else "unknown",
                "name": name,
                "cpu": specs['cpu'],
                "ram": specs['ram'],
                "disk": specs['disk'],
                "bandwidth": specs['bw'],
                "speed": specs['speed'],
                "location": specs['loc'],
                "price": price,
                "stock": stock,
                "link": get_standard_aff_link(pid) if pid else URL_CART,
                "type": "General"
            }
            item['score'] = calculate_score(item) # Calc Score
            final_list.append(item)
    
    except Exception as e:
        print(f"Error scraping public cart: {e}")

    # Sort: Limited first, then General
    # Or Sort by Price? Let's keep Limited at top as they are more important.
    
    output_data = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M"),
        "plans": final_list
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Done. Saved {len(final_list)} total plans.")

if __name__ == "__main__":
    scrape()
