#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome import service as fs
from webdriver_manager.chrome import ChromeDriverManager

import time
import datetime
import os

from dotenv import load_dotenv

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)

from parking_checker import check_parking_availability
# ===
target_date = "2026/03/18"
target_period = 5
sleeptime = 55

load_dotenv()
access_token = os.environ.get('LINE_ACCESS_TOKEN')
if not access_token:
    raise ValueError("LINE_ACCESS_TOKEN が設定されていません")

targetDt = datetime.datetime.strptime(target_date,'%Y/%m/%d')

target_dates = []
for d in range(target_period):
    target_dates.append(targetDt.strftime('%Y/%m/%d'))
    targetDt = targetDt + datetime.timedelta(days=1)


CONFIG_P4 = {
    'name': 'Parking 4 ',
    'url': "https://haneda-p4.jp/airport/",
    'next_month_id': "p2next",
    'calendar_path': '//div[@id="calendar01"]/div/table[@class="calendar_btm"]/tbody/tr/td[@class="publ"]',
    'find_xpath': '//div[@id=\'calendar01\']/div/table[@class="calendar_waku"]/tbody/tr/td/span[text()="{day}"]/..',
}
CONFIG_P4P = {
    'name': 'Parking 4P',
    'url': "https://haneda-p4.jp/airport/",
    'next_month_id': "p3next",
    'calendar_path': '//div[@id="calendar02"]/div/table[@class="calendar_btm"]/tbody/tr/td[@class="priv"]',
    'find_xpath': '//div[@id=\'calendar02\']/div/table[@class="calendar_waku"]/tbody/tr/td/span[text()="{day}"]/..',
}
CONFIG_P5 = {
    'name': 'Parking 5 ',
    'url': "https://pk-reserve.haneda-airport.jp/airport/entrance/0000.jsf",
    'next_month_id': "_idJsp68:_idJsp76",
    'calendar_path': '//div[@id="calendar01_body"]/input[@id="_idJsp68:_idJsp69"]/following-sibling::table[1]/tbody/tr/td[@class="publ"]',
    'find_xpath': '//div[@id=\'calendar01_body\']/input[@id="_idJsp68:_idJsp69"]/following-sibling::table[@class="calendar_waku_body"]/tbody/tr/td[text()="{day}"]',
}

CONFIG_P5P = {
    'name': 'Parking 5P',
    'url': "https://pk-reserve.haneda-airport.jp/airport/entrance/0000.jsf",
    'next_month_id': "_idJsp68:_idJsp88",
    'calendar_path': '//div[@id="calendar01_body"]/input[@id="_idJsp68:_idJsp81"]/following-sibling::table[1]/tbody/tr/td[@class="priv"]',
    'find_xpath': '//div[@id=\'calendar01_body\']/input[@id="_idJsp68:_idJsp81"]/following-sibling::table[@class="calendar_waku_body"]/tbody/tr/td[text()="{day}"]',
}
chromeDriver = fs.Service(executable_path=ChromeDriverManager().install())

configuration = Configuration(
    access_token=os.environ.get('LINE_ACCESS_TOKEN')
)

def send_line_msg(messageText):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=os.environ.get('LINE_USER_ID'),
                messages=[TextMessage(text=messageText)]
            )
        )


def checkParkingAvailability(browser, config):
    available_count, result_text = check_parking_availability(browser, config, target_dates)
    print(result_text)
    if available_count == target_period:
        print("Great!!!!")
        send_line_msg("Great chance at " + config['name'] + "!!")

def create_browser():
    chrome_option = webdriver.ChromeOptions()
    chrome_option.add_argument('--headless')
    return webdriver.Chrome(service=chromeDriver, options=chrome_option)


def main():
    send_line_msg("Hello Worlds")
    browser = create_browser()
    try:
        for i in range(12*60):
            try:
                print (f"\nHaneda Airport Parking Reservation Infomation: {target_period} day(s) from {target_date}")
                checkParkingAvailability(browser, CONFIG_P4)
                checkParkingAvailability(browser, CONFIG_P4P)
                checkParkingAvailability(browser, CONFIG_P5)
                checkParkingAvailability(browser, CONFIG_P5P)
            except Exception as e:
                print(f"Error occurred: {e}")
                print("Restarting browser...")
                try:
                    browser.quit()
                except:
                    pass
                browser = create_browser()
            time.sleep(sleeptime)
        send_line_msg("12 hours done")
    finally:
        browser.quit()

if __name__ == '__main__':
    main()
