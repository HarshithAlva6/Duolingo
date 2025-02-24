from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import os
import redis
#import webbrowser
from dotenv import load_dotenv
#from flask import Flask, jsonify
#from flask_cors import CORS
from datetime import datetime
import pytz
import time
import json
from selenium.webdriver.common.action_chains import ActionChains


#app = Flask(__name__)
#CORS(app)
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
CST = pytz.timezone("America/Chicago")

def past_midnight(time):
    update = datetime.fromtimestamp(time, CST)
    now = datetime.now(CST)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return update < midnight

def scrap_div():
    options = Options()
    #options.headless = False
    #options.binary_location = "/usr/bin/google-chrome" 
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")  
    options.add_argument("--remote-debugging-port=9222")  
    options.add_argument("--disable-gpu")  
    options.add_argument("--window-size=1920,1080")  
    options.add_argument("--start-maximized")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--disable-software-rasterizer")
    load_dotenv(override=True)

    #chromedriver_path = "./ChromeDriver/chromedriver.exe" 

    #service = Service(executable_path="/usr/local/bin/chromedriver")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    DUOLINGO_EMAIL = os.getenv("DUOLINGO_EMAIL")
    DUOLINGO_PASSWORD = os.getenv("DUOLINGO_PASSWORD")
    try:
        print("Opening Duolingo website...")
        driver.get("https://www.duolingo.com")
        wait = WebDriverWait(driver, 15)

        print("Clicking 'Already have an account' button...")
        account = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='have-account']"))
        )
        account.click()

        time.sleep(10)

        print("Waiting for email input field...")
        email = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='email-input']")))
        password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='password-input']")))

        # Click and enter email
        email.send_keys(DUOLINGO_EMAIL)
        # Wait for email to be set properly
        WebDriverWait(driver, 10).until(lambda driver: email.get_attribute("value") == DUOLINGO_EMAIL)

        # Trigger email input events
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", email)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", email)

        # Send password
        password.send_keys(DUOLINGO_PASSWORD)
        # Wait for password to be set properly
        WebDriverWait(driver, 10).until(lambda driver: password.get_attribute("value") == DUOLINGO_PASSWORD)

        # Print password value for debugging
        print("Entered password:", password.get_attribute("value"))

        # Trigger password input events
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password)

        # Print again to ensure it was correctly set
        print("Password after events:", password.get_attribute("value"))
        if password.get_attribute("value") == DUOLINGO_PASSWORD:
            print("Password entered correctly!")
        else:
            print("Password mismatch!")
        # Wait for login button to be clickable
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='register-button']"))
        )

        # Click the login button
        login_button.click()
        driver.save_screenshot("debug_after_click.png")
        # Wait for page to load
        WebDriverWait(driver, 40).until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Save a screenshot
        driver.save_screenshot("debug_after_login.png")
        print("Logged in successfully!")

        time.sleep(10)
        print("Logged in, waiting for profile tab...")
        try:
            print(driver.page_source)
            driver.save_screenshot("debug_2_after_login.png")
            print("Waiting for the page to fully load...")
            WebDriverWait(driver, 40).until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("Page loaded.")
            driver.save_screenshot("debug_3_after_load.png")
            print("Waiting for the profile tab to be present...")
            profile_link = WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='profile-tab']"))
            )
            print("Profile tab located.")
            
            print("Scrolling into view...")
            driver.execute_script("arguments[0].scrollIntoView();", profile_link)
            
            print("Clicking the profile tab...")
            driver.execute_script("arguments[0].click();", profile_link)
            print("Profile tab clicked.")
            
            time.sleep(2)
        except Exception as e:
            print("Profile tab not found in time", e)
        #profile_link = driver.find_element(By.CSS_SELECTOR, "[data-test='profile-tab']")  
        time.sleep(10)
        print("Got profile", profile_link)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        stats = soup.find_all("div", class_="_2Hzv5")  
        stats_html = [str(div) for div in stats]
        #for idx, div in enumerate(stats, start=1):
        #    print(div.get_text(strip=True))
        print("Successfully fetched stats.")
        return stats_html
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    finally:
        driver.quit() 
        print("Driver closed.")

#@app.route('/duolingo', methods=['GET'])
def getStats():
    cache = redis_client.get("duolingo")
    if cache:
        data = json.loads(cache)
        lastTime = data.get("timestamp",0)
        if past_midnight(lastTime):
            stats = scrap_div()
            if stats:
                freshdata = {"timestamp": time.time(), "stats": stats}
                redis_client.set("duolingo", json.dumps(freshdata))
                with open("stats.json", "w") as file:
                    json.dump(freshdata, file)
                print("Fresh data fetched, cached and saved to file.")
            else:
                print("Failed to fetch fresh data.")
        else:
            print("Data is still valid, using cached data.")
    else:
        print("No cached data found, fetching fresh data...")
        stats = scrap_div()
        if stats:
            freshdata = {"timestamp": time.time(), "stats": stats}
            redis_client.set("duolingo", json.dumps(freshdata))  
            with open("stats.json", "w") as file:
                json.dump(freshdata, file)
            print("Fresh data fetched and cached.")
        else:
            print("Failed to fetch fresh data.")

if __name__ == '__main__':
    getStats()
    #url = "http://127.0.0.1:5000/duolingo"
    #time.sleep(1)
    #webbrowser.open(url)  
    #app.run(host="127.0.0.1", port=5000, debug=True)