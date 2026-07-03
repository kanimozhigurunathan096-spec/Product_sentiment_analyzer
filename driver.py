from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():

    options = Options()

    options.add_argument("--start-maximized")

    # Uncomment this if you don't want Chrome window
    # options.add_argument("--headless=new")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.implicitly_wait(10)

    return driver