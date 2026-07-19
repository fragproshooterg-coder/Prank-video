from flask import Flask, request, render_template_string
import requests
from datetime import datetime
import ipaddress
import re
import os
import html

app = Flask(__name__)


# =====================================================
# GET VISITOR IP
# =====================================================

def get_real_ip():

    # Render/proxy header
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
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
# GEOLOCATION USING IP-API
# =====================================================

def get_geo_info(ip):

    # Private/local IP
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


    try:

        response = requests.get(

            f"http://ip-api.com/json/{ip}",

            params={
                "fields": (
                    "status,message,query,city,regionName,"
                    "country,countryCode,isp,org,as,"
                    "timezone,lat,lon,zip"
                )
            },

            timeout=10

        )


        data = response.json()


        print("IP-API DATA:", data)


        if data.get("status") == "success":

            return {

                "ip": data.get(
                    "query",
                    ip
                ),

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

                "postal": data.get(
                    "zip",
                    "N/A"
                ),

                "hostname": "N/A",

                "asn": data.get(
                    "as",
                    "N/A"
                )

            }


        print(
            "IP-API ERROR:",
            data.get(
                "message",
                "Unknown error"
            )
        )


    except Exception as error:

        print(
            "GEOLOCATION ERROR:",
            error
        )


    # If API fails

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
# BROWSER AND DEVICE INFORMATION
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


    elif "opr" in ua or "opera" in ua:

        browser = "Opera"

        match = re.search(
            r"opr/([\d.]+)",
            ua
        )


    elif "whatsapp" in ua:

        browser = "WhatsApp Browser"

        match = None


    elif "telegram" in ua:

        browser = "Telegram Browser"

        match = None


    elif "instagram" in ua:

        browser = "Instagram Browser"

        match = None


    elif "facebook" in ua:

        browser = "Facebook Browser"

        match = None


    elif "chrome" in ua:

        browser = "Google Chrome"

        match = re.search(
            r"chrome/([\d.]+)",
            ua
        )


    elif "firefox" in ua:

        browser = "Mozilla Firefox"

        match = re.search(
            r"firefox/([\d.]+)",
            ua
        )


    elif "safari" in ua:

        browser = "Apple Safari"

        match = re.search(
            r"version/([\d.]+)",
            ua
        )


    else:

        browser = "Unknown Browser"

        match = None


    if match:

        browser_version = match.group(1)

    else:

        browser_version = "Unknown"


    # -------------------------
    # OPERATING SYSTEM
    # -------------------------

    if "android" in ua:

        match = re.search(
            r"android ([\d.]+)",
            ua
        )

        if match:

            operating_system = (
                "Android "
                + match.group(1)
            )

        else:

            operating_system = "Android"


    elif "iphone" in ua:

        operating_system = "iOS (iPhone)"


    elif "ipad" in ua:

        operating_system = "iOS (iPad)"


    elif "windows" in ua:

        operating_system = "Windows"


    elif "mac os" in ua:

        operating_system = "macOS"


    elif "linux" in ua:

        operating_system = "Linux"


    else:

        operating_system = "Unknown OS"


    # -------------------------
    # DEVICE TYPE
    # -------------------------

    if (
        "iphone" in ua
        or "mobile" in ua
    ):

        device_type = "Mobile Phone"


    elif (
        "ipad" in ua
        or "tablet" in ua
    ):

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

    if (
        "samsung" in ua
        or "sm-" in ua
    ):

        match = re.search(
            r"sm-([a-z0-9]+)",
            ua
        )

        if match:

            device_model = (
                "Samsung Galaxy "
                + match.group(1).upper()
            )

        else:

            device_model = "Samsung Galaxy"


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

        "browser_version": browser_version,

        "os": operating_system,

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
# HOME ROUTE
# =====================================================

@app.route("/")
def index():


    # Get IP

    ip = get_real_ip()


    print("\n")
    print("=" * 70)
    print("NEW VISITOR DETECTED")
    print("=" * 70)


    print(
        "DETECTED IP:",
        ip
    )


    # Get location

    geo = get_geo_info(ip)


    # Get user agent

    user_agent = request.headers.get(

        "User-Agent",

        "Unknown"

    )


    # Get browser/device

    browser = get_browser_info(

        user_agent

    )


    # Timestamp

    timestamp = datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S"

    )


    # -------------------------
    # PRINT NETWORK
    # -------------------------

    print("\nNETWORK INFORMATION")
    print("-" * 50)


    print(
        "IP:",
        ip
    )


    print(
        "ASN:",
        geo["asn"]
    )


    print(
        "Hostname:",
        geo["hostname"]
    )


    # -------------------------
    # PRINT LOCATION
    # -------------------------

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


    # -------------------------
    # PRINT ISP
    # -------------------------

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


    # -------------------------
    # PRINT DEVICE
    # -------------------------

    print("\nDEVICE INFORMATION")
    print("-" * 50)


    print(
        "Device Type:",
        browser["device_type"]
    )


    print(
        "Device Model:",
        browser["device_model"]
    )


    print(
        "Operating System:",
        browser["os"]
    )


    # -------------------------
    # PRINT BROWSER
    # -------------------------

    print("\nBROWSER INFORMATION")
    print("-" * 50)


    print(
        "Browser:",
        browser["browser"]
    )


    print(
        "Browser Version:",
        browser["browser_version"]
    )


    # -------------------------
    # USER AGENT
    # -------------------------

    print("\nUSER-AGENT")
    print("-" * 50)


    print(user_agent)


    # -------------------------
    # TIME
    # -------------------------

    print("\nTIME")
    print("-" * 50)


    print(timestamp)


    print("\n")
    print("=" * 70)


    # =================================================
    # SAVE LOG
    # =================================================

    with open(

        "visitors_log.txt",

        "a",

        encoding="utf-8"

    ) as file:


        file.write("\n")

        file.write(
            "=" * 70
        )

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
            f"DEVICE TYPE: "
            f"{browser['device_type']}\n"
        )


        file.write(
            f"DEVICE MODEL: "
            f"{browser['device_model']}\n"
        )


        file.write(
            f"OS: {browser['os']}\n"
        )


        file.write(
            f"BROWSER: "
            f"{browser['browser']} "
            f"{browser['browser_version']}\n"
        )


        file.write(
            f"USER-AGENT: "
            f"{user_agent}\n"
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


        # Escape HTML so log text is displayed safely

        safe_content = html.escape(
            content
        )


        return f"""

        <!DOCTYPE html>

        <html>

        <head>

            <title>Visitor Logs</title>

        </head>

        <body>

            <h1>Visitor Logs</h1>

            <pre>{safe_content}</pre>

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
