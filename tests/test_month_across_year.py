"""月をめくる回数を、年をまたいで数えること"""


def test_month_tries_count_across_new_year(monkeypatch):
    """12月に翌年1月を調べる。月の数字だけを引くと -10 回になり、1回も探さなかった"""
    import datetime as real
    from unittest.mock import MagicMock, patch

    import parking_checker

    class Dec(real.datetime):
        @classmethod
        def now(cls, tz=None):
            return real.datetime(2026, 12, 20, 9, 0, 0)

    class Mod:
        datetime = Dec
        timedelta = real.timedelta

    monkeypatch.setattr(parking_checker, "datetime", Mod)
    browser = MagicMock()
    month, day = MagicMock(), MagicMock()
    month.text = "2027年 1月"
    day.get_attribute.return_value = "vacant"
    browser.find_element.side_effect = lambda by, value: month if value == "//calendar" else day
    cfg = {"name": "T", "url": "http://example.invalid", "next_button_id": "n",
           "month_xpath": "//calendar", "day_xpath": '//day[text()="{day}"]'}
    with patch.object(parking_checker, "WebDriverWait"):
        count, text = parking_checker.check_parking_availability(browser, cfg, ["2027/01/05"])
    assert count == 1, text
