#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
from __future__ import annotations

from collections.abc import Iterator

import pytest
from _pytest.monkeypatch import MonkeyPatch

from tests.unit.cmk.gui.conftest import SetConfig

import cmk.gui.main
from cmk.gui.ctx_stack import request_local_attr
from cmk.gui.http import request
from cmk.gui.logged_in import user

RequestContextFixture = Iterator[None]


def test_get_start_url_default(request_context: RequestContextFixture) -> None:
    assert cmk.gui.main._get_start_url() == "dashboard.py"


def test_get_start_url_default_config(
    request_context: RequestContextFixture,
    set_config: SetConfig,
) -> None:
    with set_config(start_url="bla.py"):
        assert cmk.gui.main._get_start_url() == "bla.py"


def test_get_start_url_user_config(
    monkeypatch: MonkeyPatch, request_context: RequestContextFixture, set_config: SetConfig
) -> None:
    class MockUser:
        @property
        def start_url(self) -> str:
            return "user_url.py"

    local = request_local_attr()
    monkeypatch.setattr(local, "user", MockUser())
    with set_config(start_url="bla.py"):
        assert cmk.gui.main._get_start_url() == "user_url.py"


def test_get_start_url(request_context: RequestContextFixture) -> None:
    start_url = "dashboard.py?name=mein_dashboard"
    request.set_var("start_url", start_url)

    assert cmk.gui.main._get_start_url() == start_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://localhost/",
        "javascript:alert(1)",
        "javAscRiPt:alert(1)",
        "localhost:80/bla",
    ],
)
def test_get_start_url_invalid(request_context: RequestContextFixture, invalid_url: str) -> None:
    request.set_var("start_url", invalid_url)

    assert cmk.gui.main._get_start_url() == "dashboard.py"


def test_get_start_url_invalid_config(
    monkeypatch: MonkeyPatch, request_context: RequestContextFixture
) -> None:
    monkeypatch.setattr(
        user,
        "_attributes",
        {
            "start_url": "http://asdasd/",
        },
    )
    assert cmk.gui.main._get_start_url() == "dashboard.py"
