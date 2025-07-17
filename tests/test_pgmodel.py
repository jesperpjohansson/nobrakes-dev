"""Tests for `nobrakes._pgmodel`."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, ClassVar
from unittest.mock import patch

from lxml import etree
import pytest

from nobrakes.exceptions import ElementError
from nobrakes.pgmodel import _pgmodel
from tests.conftest import element_from_string

_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def load_pgmodel_output():
    def _load(filename: str) -> dict:
        path = _DATA_DIR / f"pgmodel_output/{filename}.json"
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    return _load


def test__get_model_field_names_raises_when___match_args___does_not_return_str_tuple():
    class ConcreteModel(_pgmodel.PgModel):
        __match_args__ = (1, 2, 3)

        def from_pgelements(self, _):
            pass

    exc_msg = re.escape("ConcreteModel.__match_args__ did not return tuple[str, ...].")
    with pytest.raises(ValueError, match=exc_msg):
        ConcreteModel._get_model_field_names()


def test__add_field_raises_when_handler_method_is_not_implemented():
    class ConcreteModel(_pgmodel.PgModel):
        def from_pgelements(self, _):
            pass

    fields = {}
    field_name = "field"
    elem = "element"

    exc_msg = re.escape(f"ConcreteModel is missing handler method '_{field_name}'.")
    with pytest.raises(NotImplementedError, match=exc_msg):
        ConcreteModel._add_field(fields, field_name, elem)


def test__add_field_raises_when_handler_method_is_not_callable():
    class ConcreteModel(_pgmodel.PgModel):
        _field: ClassVar = None

        def from_pgelements(self, _):
            pass

    fields = {}
    field_name = "field"
    elem = "element"

    exc_msg = re.escape("ConcreteModel._field() is not callable.")
    with pytest.raises(TypeError, match=exc_msg):
        ConcreteModel._add_field(fields, field_name, elem)


def test__create_raises_when_data_contains_non_element_value():
    class ConcreteModel(_pgmodel.PgModel):
        __match_args__ = ("field_name",)

        def from_pgelements(self, _):
            pass

    data = {"field_name": "element"}

    exc_msg = re.escape("'data' contains a non-element value.")
    with pytest.raises(ValueError, match=exc_msg):
        ConcreteModel._create(data)


def test__create_adds_none_to_fields():
    with patch(
        "nobrakes.pgmodel._pgmodel.PgModel._get_model_field_names",
        new_callable=lambda: ("field_name",),
    ):

        @dataclass
        class ConcreteModel(_pgmodel.PgModel):
            field_name: Any

            def from_pgelements(self, _):
                pass

    data = {"field_name": None}
    with patch("nobrakes.pgmodel._pgmodel.is_element", lambda _: False):
        ConcreteModel._create(data)
        assert data["field_name"] is None


@pytest.mark.parametrize(
    ("model", "filename"),
    [
        (_pgmodel.Attendance, "attendance_2012"),
        (_pgmodel.RiderAverages, "rider_averages_2012"),
        (_pgmodel.Scorecard, "scorecard_pir_ham_2012"),
        (_pgmodel.Events, "events_2012"),
        (_pgmodel.Squad, "squad_vet_2012"),
        (_pgmodel.Standings, "standings_2012"),
        (_pgmodel.Teams, "teams_2012"),
    ],
)
def test_model_assigns_expected_values_to_fields(
    load_pgfetch_output, load_pgmodel_output, model, filename
):
    pgfetch_output = {
        k: element_from_string(v) for k, v in load_pgfetch_output(filename).items()
    }

    pgmodel_output = load_pgmodel_output(filename)

    if model == _pgmodel.Scorecard:
        pgmodel_output["result"] = tuple(tuple(x) for x in pgmodel_output["result"])

    assert asdict(model.from_pgelements(pgfetch_output)) == pgmodel_output


def test_attendance__average_raises_when_b_is_none():
    root = etree.Element("p")
    with pytest.raises(ElementError, match=re.escape("Missing expected element <b>.")):
        _pgmodel.Attendance._average(root)


def test_attendance__average_raises_when_b_tail_is_none():
    root = etree.Element("p")
    child = etree.Element("b")
    child.text = "Attendance figure:"
    root.append(child)
    with pytest.raises(
        ElementError,
        match=re.escape("Missing expected tail text of element <b>."),
    ):
        _pgmodel.Attendance._average(root)


@pytest.mark.parametrize(
    ("exc_type", "n_elements"), [(ElementError, 5), (ElementError, 3)]
)
def test_scorecard__result_raises_when_n_children_in_element_is_not_4(
    exc_type, n_elements
):
    root = etree.Element("div")
    root.extend(map(etree.Element, n_elements * ["h2"]))
    exc_msg = re.escape(f"Expected 4 <h2> elements, got {n_elements}.")
    with pytest.raises(exc_type, match=exc_msg):
        _pgmodel.Scorecard._result(root)


def test_scorecard__result_raises_when_text_is_missing_from_child_in_element():
    root = etree.Element("p")
    children = list(map(etree.Element, 4 * ["h2"]))
    for child, text in zip(children, ["team1", "pts", "team2", ""], strict=False):
        child.text = text

    root.extend(children)

    exc_msg = re.escape("Unable to extract text from all 4 <h2> elements.")
    with pytest.raises(ElementError, match=exc_msg):
        _pgmodel.Scorecard._result(root)


def test_scorecard__attendance_raises_when_element_has_no_text():
    root = etree.Element("h3")
    exc_msg = re.escape("Unable to extract attendance figure.")
    with pytest.raises(ElementError, match=exc_msg):
        _pgmodel.Scorecard._attendance(root)


def test_squad__guests_returns_none_when_table_has_no_records():
    root = element_from_string("""<tbody><tr class="rgNoRecords"></tr></tbody>""")
    assert _pgmodel.Squad._guests(root) is None
