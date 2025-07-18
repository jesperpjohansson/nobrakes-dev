""""""

from collections.abc import AsyncIterator
import html
import json
from pathlib import Path
import re

from lxml import etree
import pytest

from nobrakes.typing import ETreeElement

DATA_DIR = Path(__file__).parent / "data"


_INVALID_URL_CHAR_RE = re.compile(r"�|”|ï|¿|½")


def normalize_url(url: str) -> str:
    return _INVALID_URL_CHAR_RE.sub("", url)


_WHITESPACE_RE = re.compile(r"[\n\r\t]+")


def normalize_markup(text: bytes | str) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")

    text = html.unescape(text)
    text = normalize_url(text)
    text = _WHITESPACE_RE.sub("", text)

    return text.strip()


def element_from_markup(markup: str) -> ETreeElement:
    root = re.search(r"[^<>\s]+", markup).group()
    return etree.fromstring(markup, parser=etree.HTMLParser()).find(f".//{root}")


@pytest.fixture
def load_pgfetch_output():
    def _load(filename: str) -> dict[str, str]:
        path = DATA_DIR / f"pgfetch_output/{filename}.json"
        with path.open() as f:
            return json.load(f)

    return _load


class _ACMMixin:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def make_mock_response():
    def _make(*, markup=b"", status_code=200):
        class MockResponse(_ACMMixin):
            def __init__(self):
                self.status_code = status_code

            async def read(self) -> bytes:
                return markup

            def iter_chunks(self, *_, **__) -> AsyncIterator[bytes]:
                async def iterator():
                    chunksize = 1024
                    nchunks = len(markup) // chunksize + 1
                    for i in range(nchunks):
                        yield markup[i * chunksize : i * chunksize + chunksize]

                return iterator()

            def iter_lines(self) -> AsyncIterator[bytes]:
                async def iterator():
                    for chunk in markup.splitlines():
                        yield chunk

                return iterator()

            def raise_for_status(self):
                if self.status_code >= 400:
                    exc_msg = f"HTTP error {self.status_code}"
                    raise Exception(exc_msg)

        return MockResponse()

    return _make


@pytest.fixture
def make_mock_session(make_mock_response):
    def _make(headers: dict | None = None, **response_by_method):
        class MockSession(_ACMMixin):
            def __init__(self):
                self.headers = headers or {}

            def request(self, *_, **__):
                return make_mock_response(**response_by_method.get("request", {}))

            def get(self, *_, **__):
                return make_mock_response(**response_by_method.get("get", {}))

            def post(self, *_, **__):
                return make_mock_response(**response_by_method.get("post", {}))

            def put(self, *_, **__):
                return make_mock_response(**response_by_method.get("put", {}))

            def delete(self, *_, **__):
                return make_mock_response(**response_by_method.get("delete", {}))

            def head(self, *_, **__):
                return make_mock_response(**response_by_method.get("head", {}))

            def options(self, *_, **__):
                return make_mock_response(**response_by_method.get("options", {}))

            def patch(self, *_, **__):
                return make_mock_response(**response_by_method.get("patch", {}))

        return MockSession()

    return _make


@pytest.fixture
def mock_session(make_mock_session):
    return make_mock_session()


@pytest.fixture
def mock_response(make_mock_response):
    return make_mock_response()
