"""Internal data structures."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class HashableMapping[KT, VT](Mapping[KT, VT]):
    """A hashable wrapper around a mapping."""

    _wrapped: Mapping[KT, VT]

    def __getitem__(self, key: KT) -> VT:
        return self._wrapped[key]

    def __iter__(self) -> Iterator[KT]:
        return iter(self._wrapped)

    def __len__(self) -> int:
        return len(self._wrapped)

    def __hash__(self) -> int:
        return hash(frozenset(self._wrapped.items()))


@dataclass(frozen=True)
class TagSignature:
    """Models the tag signature (tag + attributes) of an HTML element."""

    tag: str
    attrs: MappingProxyType[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    _hash: int = field(init=False, repr=False)
    _attrs_set: set[tuple[str, str]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Set private fields."""
        object.__setattr__(
            self, "_hash", hash((self.tag, frozenset(self.attrs.items())))
        )
        object.__setattr__(self, "_attrs_set", set(self.attrs.items()))

    def __contains__(self, value: TagSignature) -> bool:
        """Return `True` if `value` can be considered a subset of `self`."""
        if isinstance(value, TagSignature):
            items_diff = set(value.attrs.items()) - self._attrs_set
            return self.tag == value.tag and not items_diff

        exc_msg = f"Expected value of type TagSignature, got {type(value).__name__}"
        raise TypeError(exc_msg)

    def __hash__(self) -> int:
        return self._hash
