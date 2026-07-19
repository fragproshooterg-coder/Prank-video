from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Preview</title>
</head>
<body style="font-family: Arial, sans-serif; background:#f5f5f5;">

<div style="max-width:600px; margin:40px auto; background:white; padding:30px; border-radius:10px;">

    <h1 style="text-align:center;">Your Logo</h1>

    <hr>

    <h2 style="text-align:center;">
        Verify Your Account
    </h2>

    <p>Hello DMG YT,</p>

    <p>Please verify your account by clicking the button below.</p>

    <div style="text-align:center;">
        <a href="#"
        style="
        background:#2563eb;
        color:white;
        text-decoration:none;
        padding:12px 25px;
        border-radius:6px;
        display:inline-block;">
        Verify Account
        </a>
    </div>

</div>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

app.run(host="0.0.0.0", port=5003, debug=True)
