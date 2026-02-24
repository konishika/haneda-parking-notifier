import datetime
import time
import traceback

from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By


def check_parking_availability(browser, config, target_dates):
    """
    駐車場の空き状況を確認する。

    Args:
        browser: Selenium WebDriver インスタンス
        config: 駐車場設定 dict (name, url, next_month_id, calendar_path, find_xpath)
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
        browser.get(config['url'])
        browser.implicitly_wait(5)

        for d in target_dates:
            d_dt = datetime.datetime.strptime(d, '%Y/%m/%d')
            day = d_dt.strftime('%-d')
            month = '  ' + d_dt.strftime('%-m')
            month = month[-1:]

            max_tries = 3
            for _ in range(max_tries):
                try:
                    calendar_path = config['calendar_path']
                    result_element = browser.find_element(by=By.XPATH, value=calendar_path)
                    element_text = result_element.text
                    if month in element_text:
                        break
                    next_button = browser.find_element(by=By.ID, value=config['next_month_id'])
                    next_button.click()
                    time.sleep(1)
                except StaleElementReferenceException:
                    time.sleep(1)
                    continue
            else:
                raise Exception(f"月が見つかりませんでした: {month}")

            find_xpath = config['find_xpath'].format(day=day)
            result_element = browser.find_element(by=By.XPATH, value=find_xpath)
            result_class = result_element.get_attribute("class")
            if "full" in result_class:
                result_text = result_text + " X"
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
