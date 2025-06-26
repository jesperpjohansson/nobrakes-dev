"""
Models for transforming fetched page data.

See Also
--------
nobrakes._api.pgmodel :
    Public re-export module.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, ClassVar, Self, cast, final, override

from nobrakes._api import pgelements
from nobrakes._api.typing import ETreeElement, RowFuncs
from nobrakes._constants import TA_DOMAIN
from nobrakes._element_utils import string, table, xpath
from nobrakes._typing import is_element, is_str_tuple
from nobrakes.exceptions import ElementError


def _url_from_href(elem: ETreeElement) -> str:
    return (
        f"{TA_DOMAIN}{href}" if (href := xpath.string(elem, "string(.//@href)")) else ""
    )


def _replace_nbsp(i: int, rows: Iterable[list[str]]) -> Iterator[list[str]]:
    for row in rows:
        if "\xa0" in row[i]:
            row[i] = row[i].replace("\xa0", " ")
            yield row
            break

        yield row

    for row in rows:
        row[i] = row[i].replace("\xa0", " ")
        yield row


@dataclass
class PgModel(ABC):
    """Base class for page models."""

    @classmethod
    @abstractmethod
    def from_pgelements(cls, data) -> Self:  # noqa: ANN001
        """
        Abstract factory method.

        Constructs and returns an instance of the model with fields populated
        using values extracted from `data`.
        """

    @classmethod
    def _get_model_field_names(cls) -> tuple[str, ...]:
        """
        Return model field names.

        Returns
        -------
        tuple[str, ...]
            The model field names defined in `cls.__match_args__`.

        Raises
        ------
        ValueError
            If `cls.__match_args__` is missing or is not a tuple of strings.

        """
        if is_str_tuple(field_names := cls.__match_args__):
            return field_names

        exc_msg = f"{cls.__name__}.__match_args__ did not return tuple[str, ...]."
        raise ValueError(exc_msg)

    @classmethod
    def _add_field(
        cls,
        fields: dict[str, Any],
        field_name: str,
        elem: ETreeElement,
    ) -> None:
        """
        Add an item to `fields`.

        Extract a value from `elem` by invoking the `_<field_name>` handler method
        and add the result to the `fields` dictionary.

        Parameters
        ----------
        fields : dict[str, Any]
            Dictionary used to accumulate field values for model instantiation.
        field_name : str
            The model field name.
        elem : ETreeElement
            Element from which to extract the field value.

        Raises
        ------
        NotImplementedError
            If the `_<field_name>` attribute is not defined.
        ValueError
            If the `_<field_name>` attribute exists but is not callable.

        """
        try:
            method = getattr(cls, f"_{field_name}")
        except AttributeError as exc:
            exc_msg = f"{cls.__name__} is missing handler method '_{field_name}'."
            raise NotImplementedError(exc_msg) from exc

        if callable(method):
            fields[field_name] = method(elem)
        else:
            exc_msg = f"{cls.__name__}._{field_name}() is not callable."
            raise TypeError(exc_msg)

    @final
    @classmethod
    def _create(cls, data: pgelements.PgElements) -> Self:
        """
        Instantiate a model.

        This method provides a default mechanism for constructing model instances.
        Field values are derived by invoking handler methods named `_<field_name>`.
        These methods must be defined on the class and accept a single positional
        argument (`ETreeElement` instance) corresponding to the field.

        Parameters
        ----------
        data : pgelements.PgElements
            A mapping of model field names to `ETreeElement` instances.

        Returns
        -------
        Self
            An instance of the model with fields populated.

        Raises
        ------
        ValueError
            If `data` contains a value that is neither `None` nor an `ETreeElement`.

        """
        field_names = cls._get_model_field_names()
        fields: dict[str, Any] = {}
        for name in field_names:
            elem = data.get(name)
            if is_element(elem):
                cls._add_field(fields, name, elem)
            elif elem is not None:
                exc_msg = "'data' contains a non-element value."
                raise ValueError(exc_msg)

        for name in set(field_names) - fields.keys():
            fields[name] = None

        return cls(**fields)


@dataclass
class Attendance(PgModel):
    """
    Transformed attendance page data.

    Must be instantiated using `pgmodel.Attendance.from_pgelements()`.

    Attributes
    ----------
    average : str or None
        The average attendance figure, extracted from the paragraph text content.
    table : list[list[str]] or None
        Extracted text content.

    """

    average: str | None
    table: list[list[str]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.Attendance) -> Self:
        """
        Create an instance of `pgmodel.Attendance`.

        Parameters
        ----------
        data : pgelements.Attendance
            Mapping of `pgmodel.Attendance` field names to instances of
            `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.Attendance` field name.

        """
        return cls._create(data)

    @classmethod
    def _average(cls, elem: ETreeElement) -> str:
        """Extract the average attendance figure from the provided HTML element."""
        b_elem: ETreeElement | None = elem.find("b")
        if b_elem is None:
            exc_msg = "Missing expected element <b>."
            raise ElementError(exc_msg)

        avg_attendance: str | None = b_elem.tail
        if avg_attendance is None:
            exc_msg = "Missing expected tail text of element <b>."
            raise ElementError(exc_msg)

        return avg_attendance

    @classmethod
    def _table(cls, elem: ETreeElement) -> list[list[str]]:
        """Parse the attendance table HTML element."""
        return list(table.first_stripped_text(elem))


@dataclass
class RiderAverages(PgModel):
    """
    Transformed rider averages page data.

    Must be instantiated using `pgmodel.RiderAverages.from_pgelements()`.

    Attributes
    ----------
    table : list[list[str]] or None
        Extracted text content.

    Notes
    -----
    Non-breaking spaces are replaced with whitespace characters.

    """

    table: list[list[str]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.RiderAverages) -> Self:
        """
        Create an instance of `pgmodel.RiderAverages`.

        Parameters
        ----------
        data : pgelements.RiderAverages
            Mapping of `pgmodel.RiderAverages` field names to instances of
            `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.RiderAverages` field name.

        """
        return cls._create(data)

    @classmethod
    def _table(cls, elem: ETreeElement) -> list[list[str]]:
        """Parse the rider averages table HTML element."""
        return list(_replace_nbsp(1, table.first_stripped_text(elem)))


@dataclass
class Events(PgModel):
    """
    Transformed events page data.

    Must be instantiated using `pgmodel.Events.from_pgelements()`.

    Attributes
    ----------
    table : list[list[str]] or None
        Extracted text content and URLs.

    """

    thfuncs: ClassVar[RowFuncs[str]] = [
        string.first_stripped_text,
        string.first_stripped_text,
        string.stripped_text,
        string.stripped_text,
    ]
    tdfuncs: ClassVar[RowFuncs[str]] = [
        string.stripped_text,
        string.stripped_text,
        _url_from_href,
        _url_from_href,
    ]

    table: list[list[str | None]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.Events) -> Self:
        """
        Create an instance of `pgmodel.Events`.

        Parameters
        ----------
        data : pgelements.Attendance
            Mapping of `pgmodel.Attendance` field names to instances of
            `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.Attendance` field name.

        """
        return cls._create(data)

    @classmethod
    def _table(cls, elem: ETreeElement) -> list[list[str]]:
        """Transform the events table using column and cell extractors."""
        return list(table.apply(elem, thfuncs=cls.thfuncs, tdfuncs=cls.tdfuncs))


@dataclass
class Scorecard(PgModel):
    """
    Transformed scorecard page data.

    Must be instantiated using `pgmodel.Scorecard.from_pgelements()`.

    Attributes
    ----------
    result : tuple[tuple[str, str], tuple[str, str]] or None
        Two records, each containing a team's name and final score. See § 1 in Notes.
    attendance : str or None
        Extracted numeric attendance figure.
    scorecard : list[list[str]] or None
        Extracted text content. See § 2 in Notes.

    Notes
    -----
    The ordering of the teams in `result` is language-dependent.
        - Swedish - team1 = home team, team2 = away team
        - English - team1 = away team, team2 = home team

    There are inconsistencies in the source data regarding the location of the character
    representing a riders helmet color (R/B/V/G). This is handled internally. In
    `scorecard`, the text content of such as cell is formatted as a string where the
    values are separated by "/" and are supposed to appear in the following order:
    helmet color, result, gate (e.g. "B/0/4").

    """

    re_attendance_figure: ClassVar[re.Pattern[str]] = re.compile(r"\d+")

    result: tuple[tuple[str, str], tuple[str, str]] | None
    attendance: str | None
    scorecard: list[list[str]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.Scorecard) -> Self:
        """
        Create an instance of `pgmodel.Scorecard`.

        Parameters
        ----------
        data : pgelements.Scorecard
            Mapping of `pgmodel.Scorecard` field names to instances of `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.Scorecard` field name.

        """
        return cls._create(data)

    @classmethod
    def _result(cls, elem: ETreeElement) -> tuple[tuple[str, str], tuple[str, str]]:
        """Extract the full team names and final scores."""
        n = 4
        children: list[ETreeElement] = list(elem.findall(".//h2"))
        if len(children) != n:
            exc_msg = f"Expected {n} <h2> elements, got {len(children)}."
            raise ElementError(exc_msg)

        texts = list(map(string.first_stripped_text, children))
        if any(t == "" for t in texts):
            exc_msg = f"Unable to extract text from all {n} <h2> elements."
            raise ElementError(exc_msg)

        return ((texts[0], texts[1]), (texts[2], texts[3]))

    @classmethod
    def _attendance(cls, elem: ETreeElement) -> str:
        """Extract attendance figure from unstructured text."""
        if m := re.search(cls.re_attendance_figure, string.first_stripped_text(elem)):
            return m.group()

        exc_msg = "Unable to extract attendance figure."
        raise ElementError(exc_msg)

    @classmethod
    def _scorecard(cls, elem: ETreeElement) -> list[list[str]]:
        """Transform the scorecard and extracts text content."""
        v_copy = deepcopy(elem)
        tbody: ETreeElement = xpath.first_element_e(v_copy, "./tbody")

        # The <tbody> of table[@class='DriverSchema'] is expected to have two children.
        rider_heat_data_elems = cast(
            "list[ETreeElement]",
            tbody.xpath(
                ".//tr[contains(@class, 'Driver')]//td[.//table[@class='DriverSchema']]"
            ),
        )

        for td in rider_heat_data_elems:
            # tr[1] is expected to have three children. The second and third child are
            # expected to contain the riders result and gate respectively.
            divs: list[ETreeElement] = td.findall(".//tr[1]//div")

            # The first child of tr[1] is expected to contain the riders helmet color or
            # a non-breaking space. If the latter is true, the first element of tr[2]
            # is expected to contain the riders helmet color.
            if divs[0].text == "\xa0":
                fallback_element: ETreeElement = xpath.first_element_e(
                    td,
                    ".//tr[2]//div",
                )
                divs[0].text = fallback_element.text

            td.text = "/".join(map(string.first_stripped_text, divs))
            td.remove(next(td.iterchildren()))

        return list(table.first_stripped_text(v_copy))


@dataclass
class Squad(PgModel):
    """
    Transformed squad page data.

    Must be instantiated using `pgmodel.Squad.from_pgelements()`.

    Attributes
    ----------
    riders : list[list[str]] or None
        Extracted text content.
    guests : list[list[str]] or None
        Extracted text content.

    Notes
    -----
    Non-breaking spaces are replaced with whitespace characters.

    """

    riders: list[list[str]] | None
    guests: list[list[str]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.Squad) -> Self:
        """
        Create an instance of `pgmodel.Squad`.

        Parameters
        ----------
        data : pgelements.Squad
            Mapping of `pgmodel.Squad` field names to instances of
            `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.Squad` field name.

        """
        return cls._create(data)

    @classmethod
    def _riders(cls, elem: ETreeElement) -> list[list[str]]:
        """Extract rider table information."""
        return list(_replace_nbsp(0, table.first_stripped_text(elem)))

    @classmethod
    def _guests(cls, elem: ETreeElement) -> list[list[str]] | None:
        """Parse guest data or returns None if 'no records' row is present."""
        if elem.find(".//tr[@class='rgNoRecords']") is not None:
            return None

        return list(_replace_nbsp(0, table.first_stripped_text(elem)))


@dataclass
class Standings(PgModel):
    """
    Transformed standings page data.

    Must be instantiated using `pgmodel.Standings.from_pgelements()`.

    Attributes
    ----------
    po1 : list[list[str]] or None
        Records containing extracted text content. See notes.
    po2 : list[list[str]] or None
        Records containing extracted text content. See notes.
    po3 : list[list[str]] or None
        Records containing extracted text content. See notes.
    regular : list[list[str]] or None
        Extracted text content.

    Notes
    -----
    `po1`, `po2` and `po3` are transformed into records. For example, this semifinals
    play-off tree of a standings page:

    ```
    ┌───────────────────────────────────────┐
    │ PLAYOFFS                        POINTS│
    ├────────────────────────────────┬──────┤
    │ Semifinal                      │      │
    │ ├── Semifinal 1                │      │
    │ │   ├── YYYY-MM-01             │      │
    │ │   │   ├── Team A (home team) │  46  │
    │ │   │   └── Team B             │  44  │
    │ │   └── YYYY-MM-02             │      │
    │ │       ├── Team B (home team) │  47  │
    │ │       └── Team A             │  43  │
    │ └── Semifinal 2                │      │
    │     ├── YYYY-MM-03             │      │
    │     │   ├── Team C (home team) │  51  │
    │     │   └── Team D             │  39  │
    │     └── YYYY-MM-04             │      │
    │         ├── Team D (home team) │  42  │
    │         └── Team C             │  48  │
    └────────────────────────────────┴──────┘
    ```

    is transformed into the following records:
    ```
    [
        ["Semifinal 1", "YYYY-MM-01", "Team A", "46", "Team B", "44"],
        ["Semifinal 1", "YYYY-MM-02", "Team B", "47", "Team A", "43"],
        ["Semifinal 2", "YYYY-MM-03", "Team C", "51", "Team D", "39"],
        ["Semifinal 2", "YYYY-MM-04", "Team D", "42", "Team C", "48"],
    ]
    ```

    """

    re_home_team_parenthesis: ClassVar[re.Pattern[str]] = re.compile(r" \(H[^\)]*\)$")
    re_iso_date: ClassVar[re.Pattern[str]] = re.compile(r"\d{4}-\d{2}-\d{2}")

    po1: list[list[str]] | None
    po2: list[list[str]] | None
    po3: list[list[str]] | None
    regular: list[list[str]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.Standings) -> Self:
        """
        Create an instance of `pgmodel.Standings`.

        Parameters
        ----------
        data : pgelements.Standings
            Mapping of `pgmodel.Standings` field names to instances of
            `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.Standings` field name.

        """
        return cls._create(data)

    @override
    @classmethod
    def _add_field(
        cls,
        fields: dict[str, Any],
        field_name: str,
        elem: ETreeElement,
    ) -> None:
        method_name = "_po" if field_name.startswith("po") else f"_{field_name}"
        method = getattr(cls, method_name)
        fields[field_name] = method(elem)

    @classmethod
    def _po(cls, elem: ETreeElement) -> list[list[str]]:
        """Create records from a play-off tree."""
        stripped_text = [
            cls.re_home_team_parenthesis.sub("", t)
            for t in string.iter_stripped_text(elem)
        ]

        # Date is the first event-specific record field.
        date_positions = [
            i for i, x in enumerate(stripped_text) if cls.re_iso_date.match(x)
        ]

        # Stripping redundant parenthesis from home team name, e.g.
        # "Team (home team)" -> "Team".
        for date_pos in date_positions:
            home_team_pos = date_pos + 1
            incl_parenthesis = stripped_text[home_team_pos]
            excl_parenthesis = cls.re_home_team_parenthesis.sub("", incl_parenthesis)
            stripped_text[home_team_pos] = excl_parenthesis

        # E.g. "Semifinal 2".
        current_round = stripped_text[date_positions[0] - 1]

        # Number of event-specific data points.
        # 1. ISO date, 2. HT name, 3. HT score, 4. AT name, 5. AT score.
        n_event_data_points = 5

        records: list[list[str]] = []
        for i, p in enumerate(date_positions):
            event_data = stripped_text[p : p + n_event_data_points]
            records.append([current_round, *event_data])

            if p == date_positions[-1]:
                break

            if date_positions[i + 1] - p > n_event_data_points:
                current_round = stripped_text[date_positions[i + 1] - 1]

        return records

    @classmethod
    def _regular(cls, elem: ETreeElement) -> list[list[str]]:
        """Parse regular season standings table using basic text extraction."""
        return list(table.first_stripped_text(elem))


@dataclass
class Teams(PgModel):
    """
    Transformed teams page data.

    Must be instantiated using `pgmodel.Teams.from_pgelements()`.

    Attributes
    ----------
    table : list[list[str]] or None
        Extracted text content and URLs to squad pages.

    """

    thfuncs: ClassVar[RowFuncs[str]] = [
        string.first_stripped_text,
        string.first_stripped_text,
        string.first_stripped_text,
        string.stripped_text,
    ]
    tdfuncs: ClassVar[RowFuncs[str]] = [
        string.stripped_text,
        string.stripped_text,
        string.stripped_text,
        _url_from_href,
    ]

    table: list[list[str]] | None

    @classmethod
    def from_pgelements(cls, data: pgelements.Teams) -> Self:
        """
        Create an instance of `pgmodel.Teams`.

        Parameters
        ----------
        data : pgelements.Teams
            Mapping of `pgmodel.Teams` field names to instances of
            `ETreeElement`.

        Raises
        ------
        NotImplementedError
            If `data` contains a key that is not a `pgmodel.Teams` field name.

        """
        return cls._create(data)

    @classmethod
    def _table(cls, elem: ETreeElement) -> list[list[str]]:
        """Transform a teams table with pre-specified header and cell functions."""
        return list(table.apply(elem, thfuncs=cls.thfuncs, tdfuncs=cls.tdfuncs))
