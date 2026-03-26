#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome import service as fs
from webdriver_manager.chrome import ChromeDriverManager

import argparse
import time
import datetime
import os
import smtplib
import tomllib
from email.message import EmailMessage

from dotenv import load_dotenv

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.messaging.exceptions import ApiException

from parking_checker import check_parking_availability
sleeptime = 55
line_available = True

load_dotenv()
access_token = os.environ.get('LINE_ACCESS_TOKEN')
if not access_token:
    raise ValueError("LINE_ACCESS_TOKEN が設定されていません")

gmail_user     = os.environ.get('GMAIL_USER')
gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
if not gmail_password:
    raise ValueError("GMAIL_APP_PASSWORD が設定されていません")

email_to       = os.environ.get('EMAIL_TO')

with open('config.toml', 'rb') as f:
    config = tomllib.load(f)

configuration = Configuration(
    access_token=os.environ.get('LINE_ACCESS_TOKEN')
)

def send_email(subject, body):
    if not (gmail_user and gmail_password and email_to):
        return
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From']    = gmail_user
    msg['To']      = email_to
    msg.set_content(body)
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(gmail_user, gmail_password)
        smtp.send_message(msg)


def send_line_msg(messageText):
    global line_available
    if not line_available:
        return
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
        msg = "Great chance at " + config['name'] + "!!\n" + config['url']
        send_line_msg(msg)
        send_email("羽田駐車場 空き通知", msg)

def create_browser():
    chrome_option = webdriver.ChromeOptions()
    chrome_option.add_argument('--headless=new')       # GUIなし環境向け
    chrome_option.add_argument('--no-sandbox')         # Linux サーバー向け
    chrome_option.add_argument('--disable-dev-shm-usage')
    chrome_option.add_argument('--window-size=1280,900')
    chrome_driver = fs.Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=chrome_driver, options=chrome_option)


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
    days_from_now = (targetDt - datetime.datetime.now()).days
    if days_from_now > 30:
        print(f"警告: 指定された日付 {target_date} は30日以上先です ({days_from_now}日後)")
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

    try:
        send_line_msg("Hello Worlds")
    except ApiException as e:
        if e.status == 429:
            global line_available
            line_available = False
            print("LINE送信上限に達しました。メール通知に切り替えます。")
            send_email("羽田駐車場 通知開始（メール切り替え）", "LINE送信上限のためメール通知に切り替えました。")
        else:
            raise
    browser = create_browser()
    try:
        for _ in range(12*60):
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
