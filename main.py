from selenium import webdriver
from tixCraft import *
import time

if __name__ == '__main__':
    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')

    tCS = tixCraftSelenium()

    driver = webdriver.Chrome()
    driver.set_page_load_timeout(60)

    if not tCS.DEBUG_MODE:
        driver.get(tCS.URL)
    else:
        driver.get(tCS.CONCERT_URL)

    # Google Login tixCraft.
    if not tCS.DEBUG_MODE:
        tCS.google_login(driver)
    
    # Fulfill web page.
    driver.maximize_window()
    time.sleep(1)

    # Located to "TARGET_URL" and click "Immediately Purchase".
    if not tCS.DEBUG_MODE:
        driver.get(tCS.CONCERT_URL)
    time.sleep(1)

    if tCS.purchaseTime:
        tCS.waiting_for_deadline(driver, tCS.purchaseTime)
        time.sleep(1)

    tCS.click_order(driver)
    time.sleep(1)

    tCS.wait_for_verification(driver)
    time.sleep(1)

    # Select zone to captcha input anchor.
    tCS.select_zone(driver)
    time.sleep(1)

    # Select would like to purchase ticket.
    tCS.purchase_ticket(driver)

    # Relay 20 min to payoff.
    time.sleep(1200)