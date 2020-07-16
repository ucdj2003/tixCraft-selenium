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

DEBUG_MODE = False

url = 'https://tixcraft.com/'
# target_url = 'https://tixcraft.com/activity/game/20_GreenDay'
target_url = input("輸入你想要搶票的演唱會網址，格式為/activity/game/ : ")


# TODO: 3 way sign in argparse implement.
# parser = argparse.ArgumentParser()
# parser.add_argument("-g", "--google", action="store_true", help="Sign in with Google account")
# args = parser.parse_args()
# if args.google:
#     print("Sign in with Google!")

# Setting your login information.
USERNAME = input("輸入你的Google帳號: ")
PASSWORD = input("輸入你的Google密碼: ")

# You can modify below variable.
nYourPrice = int(input("輸入你想搶的票價: "))
nYourTickets = int(input("輸入你想搶的張數: "))
# arrSkipedAreas = []
arrSkipedAreas = input("輸入你不想搶的價格區域(optional): ").split()
# purchaseTime = "2020 07 11 11 00 00"
purchaseTime = input("輸入此演唱會的搶票日期，範例格式為 {Y(2020) m(01-12) d(0-31) H(0-23) M(00-59) S(00-59)} : ")



def google_login(driver):
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

def select_zone(driver):
    # 1. Find the price zones you prefer.
    resp = requests.get(driver.current_url)
    soup = BeautifulSoup(resp.text, 'lxml')

    domZonePrices = soup.find_all('div', {'class': 'zone-label'})
    arrZoneList = []
    for i in range(len(domZonePrices)):
        pattern = str(nYourPrice)
        nPrice = re.search(pattern, domZonePrices[i].text)
        if None != nPrice:
            arrZoneList.append(i)
    if not len(arrZoneList):
        print('沒有符合你想要的價位 ({} 元) 的區域！檢查一下 nYourPrice。'.format(nYourPrice))
        return

    # 2. Choose an area with the most remaining tickets.
    arrBestZoneAreas = []
    nMaxRemain = 0
    domAnchors = soup.find_all(class_=re.compile('select_form'))

    for k in range(len(arrZoneList)):
        iZone = arrZoneList[k]
        pattern = str(nYourPrice)
        idx = -1
        for i in range(len(domAnchors)):
            isSkiped = False
            if None == re.search(pattern, domAnchors[i].text):
                continue
            idx += 1
            for j in range(len(arrSkipedAreas)):
                if None != re.search(arrSkipedAreas[j], domAnchors[i].text):
                    isSkiped = True
                    break
            if isSkiped:
                continue

            arrRemains = re.search('\d+', domAnchors[i].font.text)
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
        print('這個價位 ({}元) 的票一張不剩囉！改一下 nYourPrice，或是重新整理。'.format(nYourPrice))
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

if __name__ == '__main__':
    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    driver = webdriver.Chrome()
    driver.set_page_load_timeout(60)

    if not DEBUG_MODE:
        driver.get(url)
    else:
        driver.get(target_url)

    # Google Login tixCraft.
    if not DEBUG_MODE:
        google_login(driver)
    
    # Fulfill web page.
    driver.maximize_window()
    time.sleep(1)

    # Located to "target_url" and click "Immediately Purchase".
    if not DEBUG_MODE:
        driver.get(target_url)
    time.sleep(1)

    deadline = time.strptime(purchaseTime, "%Y %m %d %H %M %S")
    mkt_deadline = time.mktime(deadline)
    waiting_time = math.ceil(mkt_deadline - time.time())
    if waiting_time > 0 and not DEBUG_MODE:
        time.sleep(waiting_time)  # Pause program to 11 a.m
        driver.refresh()

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//input[@class='btn btn-next']"))
    )
    driver.find_element_by_xpath("//input[@class='btn btn-next']").click()

    # If enter the verfication page (for some Japanese/Korean performance), then should be wait 100 sec.
    WebDriverWait(driver, 100).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//ul[@class='area-list']"))
    )

    # Select zone to captcha input anchor.
    select_zone(driver)
    time.sleep(1)

    # Select would like to purchase ticket.
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, "//select[@class='mobile-select']"))
    )
    select = Select(driver.find_element_by_xpath("//select[@class='mobile-select']"))
    select.select_by_index(nYourTickets)
    driver.find_element_by_xpath("//input[@id='TicketForm_agree']").click()
    driver.find_element_by_xpath("//input[@id='TicketForm_verifyCode']").send_keys("")

    # Relay 20 min to payoff.
    time.sleep(1200)