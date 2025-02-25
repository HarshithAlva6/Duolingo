# Duolingo
1. Used Selenium to automate the Duolingo progress for personal use, i.e., login and scraping data using BeautifulSoup.
2. Download ChromeDriver(web driver) to control browser.
3. Install python-dotenv for saving credentials
4. Install flask and flask-cors for cross-browser extension.
5. Install Redis for local caching of statistics.

Terminals (Run two) -
1. > redis-server
To confirm check : netstat -ano | findstr :6379
2. > python chrome.py
3. > pip install undetected-chromedriver
