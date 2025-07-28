"""Each module in this subpackage contains the page-specific fetching logic."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Literal

from nobrakes._accumulator import ElementAccumulator
from nobrakes.exceptions import ElementError

if TYPE_CHECKING:
    from nobrakes._models import TagSignature
    from nobrakes.client._base import SessionAdapter
    from nobrakes.typing import ETreeElement, PgDataLabel
    from nobrakes.typing._typing import URL, NamedTargetTags

__all__ = (
    "attendance",
    "events",
    "rider_averages",
    "scorecard",
    "squad",
    "standings",
    "teams",
)


@cache
def _get_target_tags_subset(
    target_tags: NamedTargetTags,
    *data: PgDataLabel,
) -> tuple[TagSignature, ...]:
    """Return a subset of field values from `target_tags`."""
    return tuple(target_tags[k] for k in data)


@cache
def _get_sorting_indexes(
    target_tags: NamedTargetTags,
    *data: PgDataLabel,
) -> tuple[int, ...]:
    """Return a tuple containing indexes used to sort the extracted elements."""
    deterministic_order_of_elements: tuple[str, ...] = tuple(
        k for k in target_tags if k in data
    )
    try:
        return tuple(map(deterministic_order_of_elements.index, data))
    except ValueError as exc:
        exc_msg = "Invalid label in '*data'."
        raise ValueError(exc_msg) from exc


async def extract_elements[K: PgDataLabel | Literal["tab_content", "navbar"]](
    session: SessionAdapter,
    url: URL,
    target_tags: NamedTargetTags,
    *data: K,
    n: int | None = None,
) -> dict[K, ETreeElement]:
    """
    Fetch, parse and return requested elements.

    Default mechanism for fetching and parsing requested elements.
    """
    subset = _get_target_tags_subset(target_tags, *data)
    accumulator = ElementAccumulator(*subset)
    async with session.get(url) as response:
        response.raise_for_status()
        chunks = response.iter_chunks(n)
        elements: list[ETreeElement] = await accumulator.aiter_feed(chunks)

    if accumulator.remaining:
        e = ElementError(
            f"Expected {len(data)} elements, "
            f"found {len(data) - len(accumulator.remaining)}.",
        )
        e.add_note(f"URL: {url}")
        raise e

    indexes = _get_sorting_indexes(target_tags, *data)
    return dict(zip(data, (elements[i] for i in indexes), strict=True))
