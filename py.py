from flask import Flask, request, render_template_string
import requests
from datetime import datetime
import ipaddress
import re

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
    except Exception:
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
        res = requests.get(
            f"https://ipinfo.io/{ip}/json",
            timeout=5
        )

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

        org = data.get('org', 'Unknown')
        asn = org.split()[0] if org else 'N/A'

        return {
            'ip': data.get('ip', ip),
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'isp': org,
            'org': org,
            'timezone': data.get('timezone', 'Unknown'),
            'loc': data.get('loc', '0,0'),
            'postal': data.get('postal', 'N/A'),
            'hostname': data.get('hostname', 'N/A'),
            'asn': asn
        }

    except Exception as e:

        print(f"[!] ipinfo.io error: {e}")

        # Fallback to ip-api.com
        try:

            res = requests.get(
                f"http://ip-api.com/json/{ip}"
                "?fields=status,message,city,regionName,country,"
                "isp,org,timezone,lat,lon,as",
                timeout=5
            )

            data = res.json()

            if data.get('status') == 'success':

                return {
                    'ip': ip,
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'org': data.get('org', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown'),
                    'loc': f"{data.get('lat', 0)},{data.get('lon', 0)}",
                    'postal': 'N/A',
                    'hostname': 'N/A',
                    'asn': data.get('as', 'N/A')
                }

        except Exception:
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

    if 'edg' in ua:
        browser = 'Microsoft Edge'
        match = re.search(r'edg/(\d+\.\d+\.\d+\.\d+)', ua)
        browser_version = match.group(1) if match else 'Unknown'

    elif 'opr' in ua or 'opera' in ua:
        browser = 'Opera'
        match = re.search(r'opr/(\d+\.\d+\.\d+\.\d+)', ua)
        browser_version = match.group(1) if match else 'Unknown'

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

    elif 'chrome' in ua:
        browser = 'Google Chrome'
        match = re.search(r'chrome/(\d+\.\d+\.\d+\.\d+)', ua)
        browser_version = match.group(1) if match else 'Unknown'

    elif 'firefox' in ua:
        browser = 'Mozilla Firefox'
        match = re.search(r'firefox/(\d+\.\d+)', ua)
        browser_version = match.group(1) if match else 'Unknown'

    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Apple Safari'
        match = re.search(r'version/(\d+\.\d+\.\d+)', ua)
        browser_version = match.group(1) if match else 'Unknown'

    elif 'bot' in ua or 'crawler' in ua or 'spider' in ua:
        browser = 'Bot/Crawler'
        browser_version = 'Unknown'

    else:
        browser = 'Unknown Browser'
        browser_version = 'Unknown'


    # ========== OS DETECTION ==========

    if 'windows 11' in ua:
        os_name = 'Windows 11'

    elif 'windows 10' in ua:
        os_name = 'Windows 10'

    elif 'windows' in ua:
        os_name = 'Windows'

    elif 'android' in ua:
        match = re.search(r'android (\d+(?:\.\d+)?)', ua)
        os_name = f"Android {match.group(1)}" if match else 'Android'

    elif 'iphone' in ua:
        os_name = 'iOS (iPhone)'

    elif 'ipad' in ua:
        os_name = 'iOS (iPad)'

    elif 'mac os' in ua:
        os_name = 'macOS'

    elif 'linux' in ua:
        os_name = 'Linux'

    else:
        os_name = 'Unknown OS'


    # ========== DEVICE TYPE ==========

    if 'iphone' in ua or 'mobile' in ua:
        device_type = 'Mobile Phone'

    elif 'ipad' in ua or 'tablet' in ua:
        device_type = 'Tablet'

    elif 'windows' in ua or 'mac' in ua or 'linux' in ua:
        device_type = 'Desktop Computer'

    else:
        device_type = 'Unknown Device'


    # ========== DEVICE MODEL ==========

    device_model = 'Unknown'

    if 'iphone' in ua:
        device_model = 'iPhone'

    elif 'samsung' in ua or 'sm-' in ua:
        match = re.search(r'sm-([a-z0-9]+)', ua)
        device_model = (
            f"Samsung Galaxy {match.group(1).upper()}"
            if match else
            "Samsung Galaxy"
        )

    elif 'pixel' in ua:
        device_model = 'Google Pixel'

    elif 'oneplus' in ua:
        device_model = 'OnePlus'

    elif 'xiaomi' in ua or 'mi ' in ua:
        device_model = 'Xiaomi'

    elif 'huawei' in ua:
        device_model = 'Huawei'


    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'device_type': device_type,
        'device_model': device_model,
        'full_ua': user_agent
    }


# ============ SUCCESS PAGE ============

SUCCESS_PAGE = """
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
"""


# ============ ROUTES ============

@app.route('/')
def index():

    ip = get_real_ip()

    geo = get_geo_info(ip)

    user_agent = request.headers.get(
        'User-Agent',
        'Unknown'
    )

    browser_info = get_browser_info(user_agent)

    private = is_private_ip(ip)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ============ PRINT TO CONSOLE ============

    print("\n" + "=" * 70)
    print("🔐 NEW VISITOR DETECTED")
    print("=" * 70)

    print("\n🌐 NETWORK INFORMATION:")
    print(f"IP Address      : {ip}")
    print(f"Hostname        : {geo['hostname']}")
    print(f"ASN             : {geo['asn']}")
    print(f"Private IP      : {private}")

    print("\n📍 LOCATION INFORMATION:")
    print(f"City            : {geo['city']}")
    print(f"Region          : {geo['region']}")
    print(f"Country         : {geo['country']}")
    print(f"Postal Code     : {geo['postal']}")
    print(f"Timezone        : {geo['timezone']}")
    print(f"Coordinates     : {geo['loc']}")

    print("\n🏢 ISP INFORMATION:")
    print(f"ISP             : {geo['isp']}")
    print(f"Organization    : {geo['org']}")

    print("\n💻 DEVICE INFORMATION:")
    print(f"Device Type     : {browser_info['device_type']}")
    print(f"Device Model    : {browser_info['device_model']}")
    print(f"Operating System: {browser_info['os']}")

    print("\n🌐 BROWSER INFORMATION:")
    print(f"Browser         : {browser_info['browser']}")
    print(f"Browser Version : {browser_info['browser_version']}")

    print("\n📱 USER-AGENT:")
    print(user_agent)

    print("\n⏰ TIMESTAMP:")
    print(timestamp)

    print("\n" + "=" * 70)
    print("✅ VISITOR LOGGED SUCCESSFULLY")
    print("=" * 70)


    # ============ SAVE LOG ============

    with open('visitors_log.txt', 'a', encoding='utf-8') as f:

        f.write("\n" + "=" * 70 + "\n")
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
        f.write(
            f"BROWSER: {browser_info['browser']} "
            f"{browser_info['browser_version']}\n"
        )
        f.write(f"PRIVATE IP: {private}\n")
        f.write(f"USER-AGENT: {user_agent}\n")
        f.write("=" * 70 + "\n")


    return render_template_string(SUCCESS_PAGE)


@app.route('/view')
def view():

    try:

        with open(
            'visitors_log.txt',
            'r',
            encoding='utf-8'
        ) as f:

            content = f.read()

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visitor Logs</title>
        </head>
        <body>
            <h1>Visitor Logs</h1>
            <pre>{content}</pre>
        </body>
        </html>
        """

    except FileNotFoundError:

        return "No logs yet."


@app.route('/stats')
def stats():

    try:

        with open(
            'visitors_log.txt',
            'r',
            encoding='utf-8'
        ) as f:

            content = f.read()

        visitor_count = content.count('TIME:')

        ips = re.findall(
            r'IP: (.*?)\n',
            content
        )

        unique_ips = len(set(ips))

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Statistics</title>
        </head>
        <body>
            <h1>Statistics</h1>

            <h2>Total Visitors: {visitor_count}</h2>
            <h2>Unique IPs: {unique_ips}</h2>

        </body>
        </html>
        """

    except FileNotFoundError:

        return "No data yet."


# ============ RUN SERVER ============

if __name__ == '__main__':

    print("=" * 70)
    print("📍 IP GEOLOCATION LOGGER")
    print("=" * 70)

    print("[+] Server: http://localhost:5000")
    print("[+] View Logs: http://localhost:5000/view")
    print("[+] Stats: http://localhost:5000/stats")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
