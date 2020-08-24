from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import requests
import re
import math
import random
import getpass
from bs4 import BeautifulSoup

class tixCraftSelenium(object):
    """
    This class executes the selenium to automate grabbing tickets in tixCraft.
    """

    def __init__(self):
        self.DEBUG_MODE = False
        self.URL = 'https://tixcraft.com/'

        # CONCERT_URL = 'https://tixcraft.com/activity/game/20_GreenDay'
        while True:
            self.CONCERT_URL = input("輸入你想要搶票的演唱會網址，格式為「https://tixcraft.com/activity/...」: ")
            pattern = 'tixcraft.com/activity/'
            if re.search(pattern, self.CONCERT_URL):
                if re.search(r'/detail/', self.CONCERT_URL):
                    self.CONCERT_URL = re.sub(r'/detail/', r'/game/', self.CONCERT_URL)
                break
            else:
                print("請輸入正確的演唱會搶票網址")
                continue

        # Setting your login information.
        # USERNAME = 'YOUR_USERNAME'
        # PASSWORD = 'YOUR_PASSWORD'
        while True:
            self.USERNAME = input("輸入你的Google帳號: ")
            if self.USERNAME:
                break
            else:
                print("請重新輸入你的Google帳號(輸入不得為空)")
                continue
        while True:
            self.PASSWORD = getpass.getpass(prompt="輸入你的Google密碼: ")
            if self.PASSWORD:
                break
            else:
                print("請重新輸入你的Google密碼(輸入不得為空)")
                continue

        # nYourPrice = 4800
        # nYourTickets = 4
        while True:
            try:
                self.nYourPrice = int(input("輸入你想搶的票價: "))
                break
            except ValueError:
                print("請重新輸入票價(需為阿拉伯數字)")
                continue
        while True:
            try:
                self.nYourTickets = int(input("輸入你想搶的張數: "))
                break
            except ValueError:
                print("請重新輸入票價(需為阿拉伯數字)")
                continue

        # arrSkipedAreas = ["搖滾站區"]
        self.arrSkipedAreas = input("輸入你不想搶的區域，沒有的話可以按Enter跳過 (optional): ").split()

        # purchaseTime = "2020 07 11 11 00 00"
        while True:
            try:
                self.purchaseTime = input("輸入此演唱會的搶票日期，不需要即可按Enter跳過，範例格式為「Y(2020) m(01-12) d(1-31) H(0-23) M(00-59) S(00-59)」 (optional): ")
                if self.purchaseTime:
                    time.strptime(self.purchaseTime, "%Y %m %d %H %M %S")
                break
            except ValueError:
                print("請重新輸入正確的格式！")
                continue


    def google_login(self, driver):
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
        driver.find_element_by_xpath("//input[@name='identifier']").send_keys(self.USERNAME)
        driver.find_element_by_xpath("//div[@id='identifierNext']").click()

        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.NAME, 'password'))
        )
        time.sleep(1)
        driver.find_element_by_xpath("//input[@name='password']").send_keys(self.PASSWORD)
        driver.find_element_by_xpath("//div[@id='passwordNext']").click()


    def waiting_for_deadline(self, driver, purchaseTime):
        # Wating for the concert date and time before the concert starts.
        deadline = time.strptime(purchaseTime, "%Y %m %d %H %M %S")
        mkt_deadline = time.mktime(deadline)
        waiting_time = math.ceil(mkt_deadline - time.time())
        if waiting_time > 0 and not self.DEBUG_MODE:
            time.sleep(waiting_time)  # Pause program to 11 a.m
            driver.refresh()


    def click_order(self, driver):
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//input[@class='btn btn-next']"))
        )
        driver.find_element_by_xpath("//input[@class='btn btn-next']").click()


    def wait_for_verification(self, driver):
        # If enter the verfication page (for some Japanese/Korean performance), then should be wait 200 sec.
        js = "if (location.pathname.match('/ticket/verify/')) { document.getElementById('checkCode').focus(); }"
        driver.execute_script(js)
        WebDriverWait(driver, 200).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//ul[@class='area-list']"))
        )


    def select_zone(self, driver):
        # 1. Find the price zones you prefer.
        resp = requests.get(driver.current_url)
        soup = BeautifulSoup(resp.text, 'lxml')

        domZonePrices = soup.find_all('div', {'class': 'zone-label'})
        arrZoneList = []
        for i in range(len(domZonePrices)):
            pattern = '\d+'
            nPrice = int(re.search(pattern, domZonePrices[i].text).group())
            if self.nYourPrice == nPrice:
                arrZoneList.append(i)
        if not len(arrZoneList):
            print("沒有符合你想要的價位 ({}元) 的區域！檢查一下你輸入的價格吧！".format(self.nYourPrice))
            return

        # 2. Choose an area with the most remaining tickets.
        arrBestZoneAreas = []
        nMaxRemain = 0

        for k in range(len(arrZoneList)):
            iZone = arrZoneList[k]
            domAnchors = soup.select('ul.area-list')[iZone].select('a')
            for i in range(len(domAnchors)):
                isSkiped = False
                for j in range(len(self.arrSkipedAreas)):
                    if None != re.search(self.arrSkipedAreas[j], domAnchors[i].text):
                        isSkiped = True
                        break
                if isSkiped:
                    continue

                arrRemains = re.search(r'\d+', domAnchors[i].font.text)
                if None == arrRemains:
                    nRemain = 10000
                else:
                    nRemain = int(arrRemains.group())

                if nRemain < self.nYourTickets:
                    continue

                if nMaxRemain < nRemain:
                    # Update nMaxRemain and reset candidate list.
                    nMaxRemain = nRemain
                    arrBestZoneAreas = []
                
                if nMaxRemain == nRemain:
                    arrBestZoneAreas.append(iZone * 1000 + i)

        if 0 == len(arrBestZoneAreas):
            print("這個價位 ({}元) 的票一張不剩囉！檢查一下你輸入的價格吧！".format(self.nYourPrice))
            return

        # 3. Click on one of the best area randomly.
        iLuckyZoneArea = arrBestZoneAreas[math.floor(random.uniform(0, 1) * len(arrBestZoneAreas))]
        iLuckyZone = iLuckyZoneArea // 1000 + 1
        iLuckyArea = iLuckyZoneArea % 1000 + 1

        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//ul[@class='area-list']"))
        )
        driver.find_element_by_xpath("//ul[@class='area-list'][{}]/li[{}]/a".format(iLuckyZone, iLuckyArea)).click()


    def purchase_ticket(self, driver):
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, "//select[@class='mobile-select']"))
        )
        select = Select(driver.find_element_by_xpath("//select[@class='mobile-select']"))
        select.select_by_index(self.nYourTickets)
        driver.find_element_by_xpath("//input[@id='TicketForm_agree']").click()
        driver.find_element_by_xpath("//input[@id='TicketForm_verifyCode']").send_keys("")
