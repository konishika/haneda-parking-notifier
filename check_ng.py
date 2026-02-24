#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome import service as fs
from webdriver_manager.chrome import ChromeDriverManager

import argparse
import time
import datetime
import os
import tomllib

from dotenv import load_dotenv

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)

from parking_checker import check_parking_availability
sleeptime = 55

load_dotenv()
access_token = os.environ.get('LINE_ACCESS_TOKEN')
if not access_token:
    raise ValueError("LINE_ACCESS_TOKEN が設定されていません")

with open('config.toml', 'rb') as f:
    config = tomllib.load(f)
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


def checkParkingAvailability(browser, config, target_dates, target_period):
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--date',   default='2026/03/18', help='開始日 (YYYY/MM/DD)')
    parser.add_argument('--period', default=5, type=int,  help='チェックする日数')
    parser.add_argument('--lots',   nargs='+', metavar='LOT',
                        help=f'チェックする駐車場 (例: --lots P5 P4)  選択肢: {", ".join(config.keys())}')
    args = parser.parse_args()

    target_date = args.date
    target_period = args.period
    targetDt = datetime.datetime.strptime(target_date, '%Y/%m/%d')
    target_dates = [
        (targetDt + datetime.timedelta(days=d)).strftime('%Y/%m/%d')
        for d in range(target_period)
    ]

    if args.lots:
        unknown = [k for k in args.lots if k not in config]
        if unknown:
            parser.error(f'不明な駐車場: {", ".join(unknown)}  選択肢: {", ".join(config.keys())}')
        selected = {k: config[k] for k in args.lots}
    else:
        selected = config

    send_line_msg("Hello Worlds")
    browser = create_browser()
    try:
        for i in range(12*60):
            try:
                print(f"\nHaneda Airport Parking Reservation Infomation: {target_period} day(s) from {target_date}")
                for cfg in selected.values():
                    checkParkingAvailability(browser, cfg, target_dates, target_period)
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
