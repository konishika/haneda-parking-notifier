"""試験のあいだ、parking_checker の「今」を止める。

parking_checker は「今の月から対象の月まで何回めくるか」を、今日の日付から数える。
試験の対象日は 2026/03 に固定してあるので、止めないと、試験を流す日によって結果が変わる
（2026年4月以降は、めくる回数が0以下になって全部落ちる）。
"""
import datetime

import pytest

import parking_checker

FROZEN = datetime.datetime(2026, 3, 1, 9, 0, 0)


class _FrozenDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return FROZEN


class _FrozenModule:
    """parking_checker が使う datetime モジュールの代わり。now() だけ止める"""
    timedelta = datetime.timedelta
    datetime = _FrozenDateTime


@pytest.fixture(autouse=True)
def frozen_now(monkeypatch):
    monkeypatch.setattr(parking_checker, "datetime", _FrozenModule)
