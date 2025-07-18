"""Tests for `nobrakes._accumulator`."""

import re

from lxml import etree
import pytest

from nobrakes._accumulator import ElementAccumulator
from nobrakes._models import TagSignature


@pytest.fixture(scope="module")
def markup():
    return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Sample Page</title>
        </head>
        <body>
            <div id="main-content">
                <h1 class="title">Welcome to the Sample Page</h1>
            </div>
            <div>
                <h2 class="title">This is a header</h2>
            </div>
        </body>
        </html>
    """


@pytest.fixture
def markup_iter_chunks(markup):
    chunksize = 100
    nchunks = len(markup) // chunksize + 1
    return (markup[i * 100 : i * 100 + 100] for i in range(nchunks))


@pytest.fixture
def markup_aiter_chunks(markup_iter_chunks):
    async def iterator():
        for chunk in markup_iter_chunks:
            yield chunk

    return iterator()


@pytest.fixture
def markup_iter_chars(markup):
    return (char for char in markup)


@pytest.fixture
def markup_aiter_chars(markup_iter_chars):
    async def iterator():
        for char in markup_iter_chars:
            yield char

    return iterator()


@pytest.mark.asyncio
async def test_expected_end_state_when_all_target_tags_exist(markup_aiter_chunks):
    acc = ElementAccumulator(
        TagSignature("head"), TagSignature("div", {"id": "main-content"})
    )

    result = await acc.aiter_feed(markup_aiter_chunks)
    assert len(result) == 2
    assert result[0].tag == "head"
    assert not result[0].attrib
    assert result[1].tag == "div"
    assert result[1].attrib.get("id") == "main-content"
    assert acc.remaining == ()
    assert acc.in_progress is None
    assert acc.done is True


@pytest.mark.asyncio
async def test_expected_end_state_when_not_all_target_tags_exist(markup_aiter_chunks):
    acc = ElementAccumulator(TagSignature("footer"))
    result = await acc.aiter_feed(markup_aiter_chunks)
    assert next(iter(result), None) is None
    assert acc.remaining == acc._target_tags
    assert acc.in_progress is None
    assert acc.done is False


@pytest.mark.parametrize("tag", ["html", "head", "body"])
def test_expected_intermediate_state_when_all_target_tags_exist(markup, tag):
    target_tag = TagSignature(tag)
    acc = ElementAccumulator(target_tag)
    i = markup.index(f"</{tag}>")

    _ = list(acc.feed(markup[:i]))
    assert acc.remaining == acc._target_tags == (target_tag,)
    assert acc.in_progress == target_tag


@pytest.mark.asyncio
async def test_aiter_feed_stops_consuming_when_done(markup, markup_aiter_chars):
    expected_remaining_markup = markup.split("</head>")[-1]
    acc = ElementAccumulator(TagSignature("head"))
    _ = await acc.aiter_feed(markup_aiter_chars)
    remaining_markup = "".join([c async for c in markup_aiter_chars])

    assert acc.done is True
    assert remaining_markup == expected_remaining_markup


def test_reset_resets_internal_state(markup):
    acc = ElementAccumulator(TagSignature("head"), TagSignature("body"))
    i = markup.index("</body>")
    _ = list(acc.feed(markup[:i]))

    # Ensure state has been altered.
    assert acc.in_progress is not None
    assert len(acc.remaining) == 1

    acc.reset()

    # Reset state should match initial state.
    assert acc.in_progress is None
    assert set(acc.remaining) == set(acc._target_tags)  # Order is not guaranteed.


def test_reset_method_flushes_parser(markup):
    acc = ElementAccumulator(TagSignature("head"), TagSignature("body"))
    i = markup.index("</body>")
    _ = list(acc.feed(markup[:i]))

    acc.reset()

    # Feed buffer should be completely flushed, causing an etree.XMLSyntaxError
    # when the parser is forcefully closed a second time.
    with pytest.raises(etree.XMLSyntaxError, match=re.escape("no element found")):
        acc._parser.close()
