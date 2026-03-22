import datetime
import time
import traceback
import os
import base64

from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def check_parking_availability(browser, config, target_dates):
    """
    駐車場の空き状況を確認する。

    Args:
        browser: Selenium WebDriver インスタンス
        config: 駐車場設定 dict (name, url, next_button_id, month_xpath, day_xpath)
        target_dates: 確認対象日のリスト (例: ["2026/03/18", "2026/03/19"])

    Returns:
        (available_count: int, result_text: str)
        available_count: 空きがあった日数
        result_text:     結果の文字列 (ログ表示用)

    Raises:
        WebDriverException: ブラウザ系エラー
    """
    dt_now = datetime.datetime.now()
    available_count = 0
    result_text = dt_now.strftime('%Y/%m/%d %H:%M:%S') + "  " + config['name'] + ": "

    try:
        max_load_tries = 3
        for attempt in range(max_load_tries):
            browser.get(config['url'])
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, config['next_button_id']))
                )
                break
            except TimeoutException:
                if attempt == max_load_tries - 1:
                    raise
                print(f"  → ページ読み込みタイムアウト、リロードします... ({attempt + 1}/{max_load_tries})")

        for d in target_dates:
            d_dt = datetime.datetime.strptime(d, '%Y/%m/%d')
            day = d_dt.strftime('%-d')
            month = '  ' + d_dt.strftime('%-m')
            month = month[-1:]

            max_tries = 2
            for _ in range(max_tries):
                try:
                    element = browser.find_element(by=By.XPATH, value=config['month_xpath'])
                    if element is None:
                        raise Exception("月要素が見つかりませんでした")

                    element_text = (element.text or element.get_attribute('textContent') or '').strip()
#                    print(f"  → 月要素のテキスト: {repr(element_text)} (対象月: {month!r})")
                    if month in element_text:
                        break
#                    else:
#                        print(f"  → 対象{month}月が見つかりませんでした ")
                    next_button = browser.find_element(by=By.ID, value=config['next_button_id'])
                    #try:
                    next_button.click()
                    #except ElementNotInteractableException:
                    #    browser.execute_script("arguments[0].click();", next_button)
                    time.sleep(1)
                except StaleElementReferenceException:
                    time.sleep(1)
                    continue
            else:
                raise Exception(f"月が見つかりませんでした: {month}")

            day_xpath = config['day_xpath'].format(day=day, date=d_dt.strftime('%Y/%m/%d'))
            element = browser.find_element(by=By.XPATH, value=day_xpath)
            result_class = element.get_attribute("class")
            if "full" in result_class or "unavailable" in result_class:
                result_text = result_text + " X"
            elif "konzatsu" in result_class or "congestion" in result_class:
                available_count = available_count + 1
                result_text = result_text + " C"
            else:
                available_count = available_count + 1
                result_text = result_text + " O"

        return available_count, result_text

    except WebDriverException:
        print(traceback.format_exc())
        raise
    except Exception:
        print(traceback.format_exc())
        return available_count, result_text

SCREENSHOT_DIR = "debug_screenshots"

def save_screenshot(browser, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    safe_name = name.replace(' ', '_')
    path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.png")
    result = browser.execute_cdp_cmd("Page.captureScreenshot", {
        "captureBeyondViewport": True,
        "fromSurface": True,
    })
    with open(path, "wb") as f:
        f.write(base64.b64decode(result["data"]))
    print(f"    screenshot: {path}")
    html_source = browser.page_source

    if html_source:
        path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.html")

        with open(path, "w", encoding="utf-8") as file:
            file.write(html_source)