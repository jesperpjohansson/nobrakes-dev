"""Implements `ElementAccumulator`."""

from __future__ import annotations

import asyncio
from copy import copy
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from lxml import etree

from nobrakes._models import TagSignature

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, ItemsView, Iterator

    from nobrakes.typing import ETreeElement


class ElementAccumulator:
    """
    Pull specific HTML elements from a document using lxml's `HTMLPullParser`.

    This class is designed to efficiently extract a predefined set of HTML elements
    (described by `TagSignature`) from streamed or chunked HTML content, without needing
    to parse the entire document into memory.

    Parameters
    ----------
    *target_tags : TagSignature
        One or more `TagSignature` objects that specify the HTML tag names and attribute
        constraints used to identify the desired elements in the document.

    Attributes
    ----------
    in_progress : TagSignature or None
        The current target element being parsed, if any.
    remaining : tuple[TagSignature, ...]
        Tuple of target tags that have not yet been extracted.
    done : bool
        True if all target elements have been successfully extracted.

    """

    def __init__(self, *target_tags: TagSignature) -> None:
        self._target_tags = target_tags
        self._remaining: set[TagSignature] = set(self._target_tags)
        self._in_progress: None | tuple[TagSignature, ETreeElement] = None
        self._parser = etree.HTMLPullParser(
            events=("start", "end"),
            tag={x.tag for x in target_tags},
        )

    @property
    def in_progress(self) -> None | TagSignature:
        """Return a tag representation of the element being extracted."""
        if self._in_progress:
            return self._in_progress[0]

        return None

    @property
    def remaining(self) -> tuple[TagSignature, ...]:
        """Return a tuple of tag representations of unextracted target elements."""
        return tuple(self._remaining)

    @property
    def done(self) -> bool:
        """Return `True` if there are no more target elements left to extract."""
        return not self._remaining

    def _handle_start(self, element: ETreeElement) -> None:
        """
        Handle a start event for an HTML element.

        If no element is currently being extracted, check if the incoming element
        matches any of the target tags and attribute constraints. If it does,
        mark this element as in progress for extraction.
        """
        if not self._in_progress:
            sig = TagSignature(
                element.tag,
                MappingProxyType(dict(cast("ItemsView[str, str]", element.items()))),
            )

            if matching_sig := next(filter(lambda x: x in sig, self._remaining), None):
                self._in_progress = (matching_sig, element)

    def _handle_end(self, element: ETreeElement) -> ETreeElement | None:
        """
        Process an end event for an HTML element.

        If the element matches the one currently being extracted, finalize the
        extraction, remove it from the remaining targets, and return the completed
        element.

        If the element is unrelated to any target, clear it to free memory.
        """
        if self._in_progress:
            sig, elem = self._in_progress
            if elem is element:
                self._remaining.remove(sig)
                self._in_progress = None
                return elem
        else:
            element.clear()

        return None

    def feed(self, chunk: bytes) -> Iterator[ETreeElement]:
        """
        Feed a chunk of HTML data into the parser and yield extracted elements.

        Processes the HTML incrementally, triggering start/end event handlers,
        and yields elements as soon as they are fully extracted.

        Parameters
        ----------
        chunk : bytes
            A chunk of HTML data to parse.

        Yields
        ------
        ETreeElement
            Extracted elements matching the target signatures.
        """
        self._parser.feed(chunk)
        for ev, el in self._parser.read_events():
            handler = getattr(self, f"_handle_{ev}")
            if (extracted := handler(el)) is not None:
                yield extracted

    async def aiter_feed(self, chunks: AsyncIterator[bytes]) -> list[ETreeElement]:
        """
        Asynchronously feed HTML chunks into the parser and collect extracted elements.

        Consumes chunks from an async iterator, processing each chunk in a separate
        thread to avoid blocking. Stops as soon as all target elements have been
        extracted.

        Parameters
        ----------
        chunks : AsyncIterator[bytes]
            Asynchronous iterator providing chunks of HTML data.

        Returns
        -------
        list[ETreeElement]
            List of all extracted elements matching the target signatures.
        """
        elements: list[ETreeElement] = []
        async for chunk in chunks:
            elements.extend(await asyncio.to_thread(self.feed, chunk))
            if self.done:
                break
        return elements

    def reset(self) -> None:
        """
        Reset the accumulator to its initial state for reuse.

        Clears any in-progress extraction state and resets the set of remaining
        target elements to the original list. Also resets the internal parser state.

        Notes
        -----
        This method must be called before reusing an existing instance to
        ensure correct behavior.
        """
        self._in_progress = None
        self._remaining.clear()
        self._remaining.update(copy(self._target_tags))
        self._parser.close()
        for _ in self._parser.read_events():
            pass
