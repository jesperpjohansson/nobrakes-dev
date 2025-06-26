"""Tests for `nobrakes._models`."""

from collections.abc import Mapping
import re
from types import MappingProxyType

import pytest

from nobrakes._models import HashableMapping, TagSignature


@pytest.fixture
def tt():
    attrs = {"href": "https://example.com", "class": "MyClass"}
    return TagSignature(tag="a", attrs=MappingProxyType(attrs))


class TestHashableMapping:
    @staticmethod
    def test_hashable_mapping_equality_and_hash():
        d = {"a": 1, "b": 2}
        hm1 = HashableMapping(d)
        hm2 = HashableMapping({"b": 2, "a": 1})

        assert isinstance(hm1, Mapping)
        assert dict(hm1) == d
        assert hash(hm1) == hash(hm2)
        assert hm1 == hm2
        assert {hm1, hm2} == {hm1}

    @staticmethod
    def test_hashable_mapping_immutable_behavior():
        d = {"x": 42}
        hm = HashableMapping(d)

        assert hm["x"] == d["x"]
        assert len(hm) == 1
        assert list(hm) == ["x"]


class TestTagSignature:
    @staticmethod
    def test_contains(tt: TagSignature):
        assert tt in TagSignature(tt.tag, tt.attrs.copy() | {"id": "123"})

    @staticmethod
    def test_does_not_contain(tt: TagSignature):
        assert TagSignature(tt.tag, tt.attrs.copy() | {"id": "123"}) not in tt

    @staticmethod
    def test_contains_raises_when_value_is_not_a_tag_signature(tt: TagSignature):
        value = {"tag": tt.tag, "attrs": tt.attrs}
        exc_msg = f"Expected value of type TagSignature, got {type(value).__name__}"
        with pytest.raises(TypeError, match=re.escape(exc_msg)):
            assert value in tt

    @staticmethod
    def test_hash(tt: TagSignature):
        tt2 = TagSignature(tt.tag, tt.attrs)
        assert hash(tt) == hash(tt2)
