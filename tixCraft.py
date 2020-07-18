from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import requests
import re
import math
import random
import argparse
from bs4 import BeautifulSoup

# TODO: 3 ways sign in argparse implement.
# parser = argparse.ArgumentParser()
# parser.add_argument("-g", "--google", action="store_true", help="Sign in with Google account")
# args = parser.parse_args()
# if args.google:
#     print("Sign in with Google!")


DEBUG_MODE = False
URL = 'https://tixcraft.com/'


def input_information():
    # TARGET_URL = 'https://tixcraft.com/activity/game/20_GreenDay'
    while True:
        TARGET_URL = input("輸入你想要搶票的演唱會網址，格式需為「.../activity/game/...」: ")
        pattern = '/activity/game/'
        if re.search(pattern, TARGET_URL):
            break
        else:
            print("請重新輸入正確的網址格式，網址需含有「/activity/game/」內容")
            continue

    # Setting your login information.
    # USERNAME = 'YOUR_USERNAME'
    # PASSWORD = 'YOUR_PASSWORD'
    while True:
        USERNAME = input("輸入你的Google帳號: ")
        if USERNAME:
            break
        else:
            print("請重新輸入你的Google帳號(輸入不得為空)")
            continue
    while True:
        PASSWORD = input("輸入你的Google密碼: ")
        if PASSWORD:
            break
        else:
            print("請重新輸入你的Google密碼(輸入不得為空)")
            continue

    # nYourPrice = 4800
    # nYourTickets = 4
    while True:
        try:
            nYourPrice = int(input("輸入你想搶的票價: "))
            break
        except ValueError:
            print("請重新輸入票價(需為阿拉伯數字)")
            continue
    while True:
        try:
            nYourTickets = int(input("輸入你想搶的張數: "))
            break
        except ValueError:
            print("請重新輸入票價(需為阿拉伯數字)")
            continue

    # arrSkipedAreas = ["搖滾站區"]
    arrSkipedAreas = input("輸入你不想搶的區域，沒有可以按Enter跳過(optional): ").split()

    # purchaseTime = "2020 07 11 11 00 00"
    while True:
        try:
            purchaseTime = input("輸入此演唱會的搶票日期，範例格式為 {Y(2020) m(01-12) d(1-31) H(0-23) M(00-59) S(00-59)} : ")
            time.strptime(purchaseTime, "%Y %m %d %H %M %S")
            break
        except ValueError:
            print("請重新輸入正確的格式！")
            continue
    
    return TARGET_URL, USERNAME, PASSWORD, nYourPrice, nYourTickets, arrSkipedAreas, purchaseTime


def google_login(driver, USERNAME, PASSWORD):
    time.sleep(1)
    driver.find_element_by_xpath("//a[@data-toggle='modal']").click()
    
    WebDriverWait(driver, 10).until(
        expected_conditions.element_to_be_clickable(
            (By.ID, 'loginGoogle'))
    )
    driver.find_element_by_xpath("//a[@id='loginGoogle']").click()

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.NAME, 'identifier'))
    )
    driver.find_element_by_xpath("//input[@name='identifier']").send_keys(USERNAME)
    driver.find_element_by_xpath("//div[@id='identifierNext']").click()

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.NAME, 'password'))
    )
    time.sleep(1)
    driver.find_element_by_xpath("//input[@name='password']").send_keys(PASSWORD)
    driver.find_element_by_xpath("//div[@id='passwordNext']").click()

def wait_to_deadline(driver, purchaseTime):
    deadline = time.strptime(purchaseTime, "%Y %m %d %H %M %S")
    mkt_deadline = time.mktime(deadline)
    waiting_time = math.ceil(mkt_deadline - time.time())
    if waiting_time > 0 and not DEBUG_MODE:
        time.sleep(waiting_time)  # Pause program to 11 a.m
        driver.refresh()

def click_order(driver):
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//input[@class='btn btn-next']"))
    )
    driver.find_element_by_xpath("//input[@class='btn btn-next']").click()

def wait_to_verfication(driver):
    # If enter the verfication page (for some Japanese/Korean performance), then should be wait 200 sec.
    js = "if (location.pathname.match('/ticket/verify/')) { document.getElementById('checkCode').focus(); }"
    driver.execute_script(js)
    WebDriverWait(driver, 200).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//ul[@class='area-list']"))
    )

def select_zone(driver, nYourPrice, nYourTickets, arrSkipedAreas):
    # 1. Find the price zones you prefer.
    resp = requests.get(driver.current_url)
    soup = BeautifulSoup(resp.text, 'lxml')

    domZonePrices = soup.find_all('div', {'class': 'zone-label'})
    arrZoneList = []
    for i in range(len(domZonePrices)):
        pattern = '\d+'
        nPrice = int(re.search(pattern, domZonePrices[i].text).group())
        if nYourPrice == nPrice:
            arrZoneList.append(i)
    if not len(arrZoneList):
        print("沒有符合你想要的價位 ({}元) 的區域！檢查一下你輸入的價格吧！".format(nYourPrice))
        return

    # 2. Choose an area with the most remaining tickets.
    arrBestZoneAreas = []
    nMaxRemain = 0

    for k in range(len(arrZoneList)):
        iZone = arrZoneList[k]
        domAnchors = soup.select('ul.area-list')[iZone].select('a')
        # print(domAnchors)
        pattern = str(nYourPrice)
        idx = -1
        for i in range(len(domAnchors)):
            isSkiped = False
            # if None == re.search(pattern, domAnchors[i].text):
            #     continue
            idx += 1
            for j in range(len(arrSkipedAreas)):
                if None != re.search(arrSkipedAreas[j], domAnchors[i].text):
                    isSkiped = True
                    break
            if isSkiped:
                continue

            arrRemains = re.search('\d+', domAnchors[i].font.text)
            # print(domAnchors[i].font.text)
            if None == arrRemains:
                nRemain = 10000
            else:
                nRemain = int(arrRemains.group())

            if nRemain < nYourTickets:
                continue

            if nMaxRemain < nRemain:
                # Update nMaxRemain and reset candidate list.
                nMaxRemain = nRemain
                arrBestZoneAreas = []
            
            if nMaxRemain == nRemain:
                arrBestZoneAreas.append(iZone * 1000 + idx)

    if 0 == len(arrBestZoneAreas):
        print("這個價位 ({}元) 的票一張不剩囉！檢查一下你輸入的價格吧！".format(nYourPrice))
        return

    # 3. Click on one of the best area randomly.
    iLuckyZoneArea = arrBestZoneAreas[math.floor(random.uniform(0, 1) * len(arrBestZoneAreas))]
    iLuckyZone = iLuckyZoneArea // 1000 + 1
    iLuckyArea = iLuckyZoneArea % 1000 + 1

    # print(arrBestZoneAreas)
    # print(iLuckyZone)
    # print(iLuckyArea)

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//ul[@class='area-list']"))
    )
    driver.find_element_by_xpath("//ul[@class='area-list'][{}]/li[{}]/a".format(iLuckyZone, iLuckyArea)).click()

def purchase_ticket(driver):
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//select[@class='mobile-select']"))
    )
    select = Select(driver.find_element_by_xpath("//select[@class='mobile-select']"))
    select.select_by_index(nYourTickets)
    driver.find_element_by_xpath("//input[@id='TicketForm_agree']").click()
    driver.find_element_by_xpath("//input[@id='TicketForm_verifyCode']").send_keys("")


if __name__ == '__main__':
    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    TARGET_URL, USERNAME, PASSWORD, nYourPrice, nYourTickets, arrSkipedAreas, purchaseTime = input_information()

    driver = webdriver.Chrome()
    driver.set_page_load_timeout(60)

    if not DEBUG_MODE:
        driver.get(URL)
    else:
        driver.get(TARGET_URL)

    # Google Login tixCraft.
    if not DEBUG_MODE:
        google_login(driver, USERNAME, PASSWORD)
    
    # Fulfill web page.
    driver.maximize_window()
    time.sleep(1)

    # Located to "TARGET_URL" and click "Immediately Purchase".
    if not DEBUG_MODE:
        driver.get(TARGET_URL)
    time.sleep(1)

    wait_to_deadline(driver, purchaseTime)
    time.sleep(1)

    click_order(driver)
    time.sleep(1)

    wait_to_verfication(driver)
    time.sleep(1)

    # Select zone to captcha input anchor.
    select_zone(driver, nYourPrice, nYourTickets, arrSkipedAreas)
    time.sleep(1)

    # Select would like to purchase ticket.
    purchase_ticket(driver)

    # Relay 20 min to payoff.
    time.sleep(1200)