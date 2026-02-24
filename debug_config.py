#!/usr/bin/env python3
"""
CONFIG の XPath が正しく要素を取得できているか確認するデバッグスクリプト。

使い方:
    python debug_config.py

- ヘッドレスモードで動作し、各ステップでスクリーンショットを保存します。
- 確認したい CONFIG と対象日付を下の "--- 設定 ---" セクションで変えてください。

find_xpath のプレースホルダー:
    {day}  → 日番号 (例: "18")
    {date} → 日付文字列 (例: "2026-03-18")
"""
import datetime
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome import service as fs
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# --- 設定: ここを変えてテストするCONFIGと日付を指定してください ---
# ---------------------------------------------------------------------------

TARGET_DATE = "2026/03/18"

CONFIGS_TO_CHECK = [
    # CONFIG_P2 (未定義: XPathを埋めてテストしてください)
    {
        'name': 'Parking 2',
        'url': 'https://hnd-rsv.aeif.or.jp/airport2/app/toppage',
        'next_month_id': 'cal00_next',             # TODO: 翌月ボタンのid
        'calendar_path': '//*[@id="cal00_title"]', # TODO: 月テキストを含む要素のXPath
        'find_xpath': '//*[@id="0-0-{date}"]',     # TODO: 日付セルのXPath ({day} が日番号に置換される)
    },
    # CONFIG_P3 (未定義: XPathを埋めてテストしてください)
    {
        'name': 'Parking 3',
        'url': 'https://hnd-rsv.aeif.or.jp/airport2/app/toppage',
        'next_month_id': 'cal10_next',
        'calendar_path': '//*[@id="cal10_title"]',
        'find_xpath': '//*[@id="1-0-{date}"]',
    },
]

# ---------------------------------------------------------------------------

SEP = "-" * 60


def check_xpath(browser, label, xpath, show_attr=None):
    """XPath で要素を検索して結果を表示する。"""
    print(f"\n  [{label}]")
    print(f"    xpath : {xpath}")
    if not xpath:
        print("    *** 未設定 (XPathを入力してください) ***")
        return None

    try:
        elements = browser.find_elements(by=By.XPATH, value=xpath)
        if not elements:
            print("    found : NO  (要素が見つかりません)")
            return None

        print(f"    found : YES ({len(elements)} 件)")
        for i, elem in enumerate(elements[:3]):  # 最大3件表示
            try:
                text = elem.text.replace('\n', ' ')[:80]
                print(f"    [{i}] text  : {repr(text)}")
                if show_attr:
                    val = elem.get_attribute(show_attr)
                    print(f"    [{i}] {show_attr:5} : {repr(val)}")
                html = elem.get_attribute("outerHTML") or ""
                print(f"    [{i}] html  : {html[:120]}")
            except Exception as e:
                print(f"    [{i}] (要素の読み取りエラー: {e})")
        if len(elements) > 3:
            print(f"    ... (他 {len(elements) - 3} 件)")
        return elements[0] if elements else None
    except Exception as e:
        print(f"    ERROR : {e}")
        return None


def check_next_button(browser, next_month_id):
    """翌月ボタンを ID で検索して結果を表示する。"""
    print(f"\n  [next_month_id]")
    print(f"    id    : {next_month_id!r}")
    if not next_month_id:
        print("    *** 未設定 ***")
        return

    try:
        elem = browser.find_element(by=By.ID, value=next_month_id)
        text = elem.text.replace('\n', ' ')[:80]
        html = elem.get_attribute("outerHTML") or ""
        print(f"    found : YES")
        print(f"    text  : {repr(text)}")
        print(f"    html  : {html[:120]}")
    except Exception as e:
        print(f"    found : NO  ({e})")


SCREENSHOT_DIR = "debug_screenshots"


def save_screenshot(browser, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    browser.save_screenshot(path)
    print(f"    screenshot: {path}")


def highlight(browser, element):
    """見つかった要素に赤枠を付ける (スクリーンショット用)。"""
    try:
        browser.execute_script("arguments[0].style.outline = '3px solid red';", element)
    except Exception:
        pass


def debug_config(browser, config, target_date):
    d_dt = datetime.datetime.strptime(target_date, '%Y/%m/%d')
    day = d_dt.strftime('%-d')
    date_str = d_dt.strftime('%Y/%m/%d')
    month_last = ('  ' + d_dt.strftime('%-m'))[-1:]
    safe_name = config['name'].replace(' ', '_')

    print(SEP)
    print(f"CONFIG : {config['name']}")
    print(f"URL    : {config['url']}")
    print(f"対象日 : {target_date}  (day={day}, date={date_str}, month末尾={month_last!r})")
    print(SEP)

    browser.get(config['url'])
    browser.implicitly_wait(5)
    save_screenshot(browser, f"{safe_name}_01_loaded")
    print("\n■ ページロード完了。XPathを確認します...\n")

    # calendar_path: 月テキストを含む要素
    elem = check_xpath(browser, "calendar_path", config['calendar_path'])
    if elem:
        highlight(browser, elem)

    # next_month_id: 翌月ボタン
    check_next_button(browser, config['next_month_id'])

    # 対象月まで翌月ボタンをクリックして移動する
    for _ in range(6):  # 最大6ヶ月先まで試す
        cal_elem = browser.find_elements(by=By.XPATH, value=config['calendar_path'])
        if cal_elem and month_last in cal_elem[0].text:
            print(f"  → 対象月 (末尾={month_last!r}) を確認: {repr(cal_elem[0].text)}")
            break
        try:
            next_btn = browser.find_element(by=By.ID, value=config['next_month_id'])
            next_btn.click()
            time.sleep(1)  # ページ更新を待つ
            print(f"  → 翌月ボタンをクリック")
        except Exception as e:
            print(f"  → 翌月ボタンのクリック失敗: {e}")
            break

    # find_xpath: 日付セル ({day} と {date} の両方に対応)
    raw_xpath = config['find_xpath']
    find_xpath = raw_xpath.format(day=day, date=date_str) if raw_xpath else ''
    elem = check_xpath(browser, f"find_xpath (day={day}, date={date_str})", find_xpath, show_attr="class")
    if elem:
        highlight(browser, elem)
    else:
        # find_xpath が見つからない場合、近いIDをサジェストする
        prefix = raw_xpath.split('"')[1].split('{')[0] if raw_xpath and '"' in raw_xpath else ''
        if prefix:
            hints = browser.execute_script(
                "return Array.from(document.querySelectorAll('[id]'))"
                ".map(e => e.id)"
                f".filter(id => id.startsWith('{prefix}'))"
                ".slice(0, 5);"
            )
            if hints:
                print(f"  ヒント: id='{prefix}...' の要素が見つかりました → {hints}")
            else:
                print(f"  ヒント: id='{prefix}...' に一致する要素がありません。IDの形式を確認してください。")

    save_screenshot(browser, f"{safe_name}_02_highlighted")
    print()


def main():
    chromeDriver = fs.Service(executable_path=ChromeDriverManager().install())
    chrome_option = webdriver.ChromeOptions()
    chrome_option.add_argument('--headless=new')       # GUIなし環境向け
    chrome_option.add_argument('--no-sandbox')         # Linux サーバー向け
    chrome_option.add_argument('--disable-dev-shm-usage')
    chrome_option.add_argument('--window-size=1280,900')

    browser = webdriver.Chrome(service=chromeDriver, options=chrome_option)
    try:
        for config in CONFIGS_TO_CHECK:
            debug_config(browser, config, TARGET_DATE)
    finally:
        browser.quit()
        print(f"\nブラウザを閉じました。スクリーンショットは {SCREENSHOT_DIR}/ を確認してください。")


if __name__ == '__main__':
    main()
