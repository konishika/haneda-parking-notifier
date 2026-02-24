import pytest
from unittest.mock import MagicMock, patch, call
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By

from parking_checker import check_parking_availability

# テスト用のシンプルな設定
TEST_CONFIG = {
    'name': 'Test Parking',
    'url': 'http://example.com',
    'next_month_id': 'next_btn',
    'calendar_path': '//calendar',
    'find_xpath': '//day[text()="{day}"]',
}

TARGET_DATES = ["2026/03/18"]  # 3月 → month = "3"


@pytest.fixture
def browser():
    """Selenium WebDriver のモック"""
    return MagicMock()


def make_calendar_elem(month_text):
    """カレンダー要素のモックを作る (指定の月テキストを返す)"""
    elem = MagicMock()
    elem.text = month_text
    return elem


def make_day_elem(css_class):
    """日付要素のモックを作る (指定の class を返す)"""
    elem = MagicMock()
    elem.get_attribute.return_value = css_class
    return elem


# ---------------------------------------------------------------------------
# テスト: 全日程が満車 (full)
# ---------------------------------------------------------------------------
class TestAllFull:
    def test_available_count_is_zero(self, browser):
        """全日程が満車なら available_count が 0"""
        def find_element_side_effect(by, value):
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                return make_calendar_elem("3")  # 月が一致 → break
            return make_day_elem("full")         # 日付要素 → 満車

        browser.find_element.side_effect = find_element_side_effect

        count, text = check_parking_availability(browser, TEST_CONFIG, TARGET_DATES)
        assert count == 0

    def test_result_text_contains_X(self, browser):
        """全日程が満車なら result_text に X が含まれる"""
        def find_element_side_effect(by, value):
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                return make_calendar_elem("3")
            return make_day_elem("full")

        browser.find_element.side_effect = find_element_side_effect

        _, text = check_parking_availability(browser, TEST_CONFIG, TARGET_DATES)
        assert "X" in text
        assert "O" not in text


# ---------------------------------------------------------------------------
# テスト: 全日程が空き
# ---------------------------------------------------------------------------
class TestAllAvailable:
    def test_available_count_equals_target(self, browser):
        """全日程が空きなら available_count が target_dates の件数と一致"""
        dates = ["2026/03/18", "2026/03/19"]

        def find_element_side_effect(by, value):
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                return make_calendar_elem("3")
            return make_day_elem("available")  # "full" を含まない

        browser.find_element.side_effect = find_element_side_effect

        count, text = check_parking_availability(browser, TEST_CONFIG, dates)
        assert count == len(dates)

    def test_result_text_contains_O(self, browser):
        """全日程が空きなら result_text に O が含まれる"""
        def find_element_side_effect(by, value):
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                return make_calendar_elem("3")
            return make_day_elem("available")

        browser.find_element.side_effect = find_element_side_effect

        _, text = check_parking_availability(browser, TEST_CONFIG, TARGET_DATES)
        assert "O" in text
        assert "X" not in text


# ---------------------------------------------------------------------------
# テスト: 一部が満車、一部が空き (混在)
# ---------------------------------------------------------------------------
class TestMixed:
    def test_mixed_count_and_text(self, browser):
        """一部満車・一部空きのとき count と結果文字列が正しい"""
        dates = ["2026/03/18", "2026/03/19"]
        # 1日目: full / 2日目: available
        classes = ["full", "available"]
        call_index = {"n": 0}

        def find_element_side_effect(by, value):
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                return make_calendar_elem("3")
            # 日付要素はcall順に class を返す
            elem = MagicMock()
            elem.get_attribute.return_value = classes[call_index["n"] % len(classes)]
            call_index["n"] += 1
            return elem

        browser.find_element.side_effect = find_element_side_effect

        count, text = check_parking_availability(browser, TEST_CONFIG, dates)
        assert count == 1
        assert "X" in text
        assert "O" in text


# ---------------------------------------------------------------------------
# テスト: 翌月ボタンのクリック (月ナビゲーション)
# ---------------------------------------------------------------------------
class TestMonthNavigation:
    @patch('parking_checker.time.sleep')
    def test_next_month_button_clicked_when_month_not_found(self, mock_sleep, browser):
        """対象月がカレンダーに表示されていない場合、翌月ボタンをクリックする"""
        call_count = {"n": 0}

        def find_element_side_effect(by, value):
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                call_count["n"] += 1
                if call_count["n"] == 1:
                    # 1回目: 別の月 ("2" = 2月) → 翌月ボタンをクリックさせる
                    return make_calendar_elem("2")
                else:
                    # 2回目: 対象月 ("3" = 3月) → break
                    return make_calendar_elem("3")
            if by == By.ID and value == TEST_CONFIG['next_month_id']:
                return MagicMock()  # 翌月ボタン
            return make_day_elem("available")

        browser.find_element.side_effect = find_element_side_effect

        check_parking_availability(browser, TEST_CONFIG, TARGET_DATES)

        # 翌月ボタンがクリックされたか確認
        next_btn_calls = [
            c for c in browser.find_element.call_args_list
            if c == call(by=By.ID, value=TEST_CONFIG['next_month_id'])
        ]
        assert len(next_btn_calls) == 1


# ---------------------------------------------------------------------------
# テスト: StaleElementReferenceException のリトライ
# ---------------------------------------------------------------------------
class TestStaleElementRetry:
    @patch('parking_checker.time.sleep')
    def test_retries_on_stale_element(self, mock_sleep, browser):
        """StaleElementReferenceException 発生時にリトライして成功する"""
        call_count = {"n": 0}

        def find_element_side_effect(by, value):
            call_count["n"] += 1
            if by == By.XPATH and value == TEST_CONFIG['calendar_path']:
                if call_count["n"] == 1:
                    raise StaleElementReferenceException()
                return make_calendar_elem("3")
            return make_day_elem("available")

        browser.find_element.side_effect = find_element_side_effect

        count, text = check_parking_availability(browser, TEST_CONFIG, TARGET_DATES)
        assert count == 1  # 2回目で成功 → 空きあり


# ---------------------------------------------------------------------------
# テスト: WebDriverException は呼び出し元に伝播する
# ---------------------------------------------------------------------------
class TestWebDriverException:
    def test_webdriver_exception_propagates(self, browser):
        """WebDriverException はキャッチせず raise される"""
        browser.get.side_effect = WebDriverException("browser crash")

        with pytest.raises(WebDriverException):
            check_parking_availability(browser, TEST_CONFIG, TARGET_DATES)
