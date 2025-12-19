import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

# Configuration
URL = "https://bandwagonhost.com/cart.php"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../data/vps_data.json")

def clean_text(text):
    if not text:
        return ""
    return text.strip()

def parse_specs(description_html):
    specs = {
        "cpu": None,
        "ram": None,
        "disk": None,
        "bandwidth": None,
        "speed": None,
        "location": "Multiple datacenter locations" # Default
    }
    
    desc_text = description_html.get_text(separator="\n")
    lines = desc_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if "CPU" in line:
            specs['cpu'] = line.replace("CPU:", "").strip()
        elif "RAM" in line:
            specs['ram'] = line.replace("RAM:", "").strip()
        elif "SSD" in line:
            specs['disk'] = line.replace("SSD:", "").strip()
        elif "Transfer" in line:
            specs['bandwidth'] = line.replace("Transfer:", "").strip()
        elif "Link speed" in line:
            specs['speed'] = line.replace("Link speed:", "").strip()
        elif ("Location" in line or "datacenter" in line.lower() or "route" in line.lower()) and "routed" not in line.lower():
             # Basic heuristic to capture location info if it's a distinct line
             if len(line) < 100: # Avoid capturing long paragraphs
                 specs['location'] = line.strip()

    return specs

def scrape():
    print(f"Fetching {URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    cart_boxes = soup.find_all('div', class_='cartbox')
    
    products = []
    
    print(f"Found {len(cart_boxes)} products.")
    
    for box in cart_boxes:
        try:
            # Name
            name_el = box.find('strong')
            name = name_el.get_text(strip=True) if name_el else "Unknown Plan"
            
            # Specs column (first td)
            first_td = box.find('td')
            specs = parse_specs(first_td)
            
            # Price
            price_el = box.find('td', class_='pricing')
            price_full = price_el.get_text(separator=" ").strip() if price_el else "N/A"
            # Extract just the price part (e.g. from "$49.99 USD Annually")
            price_match = re.search(r'\$[\d\.]+', price_full)
            price = price_match.group(0) if price_match else price_full
            
            # Button / Link / Stock
            button = box.find('input', attrs={'type': 'button'})
            stock = False
            link = ""
            
            if button:
                onclick = button.get('onclick', '')
                # extract simple link
                # window.location='/cart.php?a=add&pid=44'
                match = re.search(r"window\.location='([^']+)'", onclick)
                if match:
                    rel_link = match.group(1)
                    if rel_link.startswith('/'):
                        link = "https://bandwagonhost.com" + rel_link
                    else:
                        link = rel_link
                
                if "Order Now" in button.get('value', ''):
                    stock = True
                    
                # Append affiliate ID if link exists
                if link:
                    aff_id = "78435"
                    separator = "&" if "?" in link else "?"
                    link = f"{link}{separator}aff={aff_id}"
            
            # If no stock, link might be missing or different
            if not link and not stock:
                # Try to find pid in form or other elements if button is missing (Out of stock)
                # But typically WHMCS hides the order button if OOS or shows "Out of Stock"
                pass
                
            product = {
                "name": name,
                "cpu": specs['cpu'] or "N/A",
                "ram": specs['ram'] or "N/A",
                "disk": specs['disk'] or "N/A",
                "bandwidth": specs['bandwidth'] or "N/A",
                "speed": specs['speed'] or "N/A",
                "location": specs['location'],
                "price": price,
                "stock": stock,
                "link": link or URL # Fallback to main URL
            }
            
            products.append(product)
            
        except Exception as e:
            print(f"Error parsing product: {e}")
            continue

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    output_data = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M"),
        "plans": products
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(products)} products to {OUTPUT_FILE} with timestamp.")

if __name__ == "__main__":
    scrape()
