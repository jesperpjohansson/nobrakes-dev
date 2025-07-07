"""Tests for `nobrakes.__init__.py`."""

import importlib
import importlib.util
import sys

import pytest


@pytest.mark.parametrize(
    ("lib", "class_name"),
    [
        ("aiohttp", "AIOHTTPResponseAdapter"),
        ("aiohttp", "AIOHTTPSessionAdapter"),
        ("httpx", "HTTPXResponseAdapter"),
        ("httpx", "HTTPXSessionAdapter"),
    ],
)
def test_raises_if_missing_dependency(monkeypatch, lib, class_name):
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: None if name == lib else "not_none"
    )

    sys.modules.pop("nobrakes.__init__", None)
    module = importlib.import_module("nobrakes.__init__")
    missing_class = getattr(module, class_name)
    with pytest.raises(ImportError, match=f"{class_name}.*{lib}"):
        missing_class()
