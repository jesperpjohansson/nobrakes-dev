"""Tests for `nobrakes._element_utils`."""

import re

from lxml import etree
import pytest

from nobrakes._element_utils import string, table, xpath
from nobrakes.exceptions import ElementError
from nobrakes.typing import ETreeElement


class TestString:
    @staticmethod
    @pytest.fixture
    def div():
        return etree.fromstring("<div>\t\nHello <b> world </b>!</div>")

    @staticmethod
    def test_iter_stripped_text(div):
        assert list(string.iter_stripped_text(div)) == ["Hello", "world", "!"]

    @staticmethod
    def test_stripped_text_returns_stripped_text(div):
        assert string.stripped_text(div) == "Hello"

    @staticmethod
    def test_stripped_text_returns_empty_string_when_element_contains_no_text():
        elem = etree.fromstring("<p></p>")
        assert string.stripped_text(elem) == ""

    @staticmethod
    def test_stripped_text_e_returns_stripped_text(div):
        assert string.stripped_text_e(div) == "Hello"

    @staticmethod
    def test_first_stripped_text_returns_first_stripped_text():
        elem = etree.fromstring("<ul><li>First item</li><li>Second item</li></ul>")
        assert string.first_stripped_text(elem) == "First item"

    @staticmethod
    def test_href_returns():
        elem = etree.fromstring('<a href="/test">link</a>')
        assert string.href(elem) == "/test"

    @staticmethod
    def test_href_returns_none():
        elem = etree.fromstring("<a>no href</a>")
        assert string.href(elem) is None

    @staticmethod
    @pytest.mark.parametrize(
        ("func", "exc_type"),
        [
            (string.stripped_text_e, ElementError),
            (string.first_stripped_text_e, ElementError),
            (string.href_e, ElementError),
        ],
    )
    def test_func_raises_when_string_is_missing(func, exc_type):
        elem = etree.fromstring("<p>  \t \n   \t  </p>")
        with pytest.raises(exc_type):
            func(elem)

    @staticmethod
    def test_href_e_returns():
        elem = etree.fromstring('<a href="/test">link</a>')
        assert string.href_e(elem) == "/test"


class TestTable:
    @staticmethod
    @pytest.fixture
    def markup():
        return """
            <table>
                <thead>
                    <tr><th>{th1}</th><th>{th2}</th></tr>
                </thead>
                <tbody>
                    <tr><td>{td11}</td><td>{td12}</td></tr>
                    <tr><td>{td21}</td><td>{td22}</td></tr>
                    <tr><td>{td31}</td><td>{td32}</td></tr>
                </tbody>
            </table>
            """

    @staticmethod
    @pytest.fixture
    def default_table(markup):
        return etree.fromstring(markup)

    @staticmethod
    def test_column_returns_expected_values(default_table):
        tbody = default_table.find("./tbody")
        result = table.column(tbody, 1)
        assert [td.text for td in result] == ["{td11}", "{td21}", "{td31}"]

    @staticmethod
    def test_column_raises_when_i_gt_n_columns(default_table):
        tbody = default_table.find("./tbody")
        i = 3
        exc_msg = f"Index {i} is greater than the number of columns in <tbody>."
        with pytest.raises(IndexError, match=re.escape(exc_msg)):  # n columns == 2
            table.column(tbody, i)

    @staticmethod
    def test_filtered_tbody_includes_matching_rows(markup):
        markup = markup.format(
            th1="",
            th2="",
            td11="apple",
            td12=100,
            td21="banana",
            td22=200,
            td31="cherry",
            td32=50,
        )
        tbody = etree.fromstring(markup).find("./tbody")
        predicates = {1: lambda s: s != "banana", 2: lambda s: int(s) > 50}
        result = table.filtered_tbody(tbody, predicates)
        assert len(result) == 1
        assert result[0].xpath("string()") == "apple100"

    @staticmethod
    def test_table_apply_returns_expected(markup):
        markup = markup.format(
            th1="<span> H1\t</span>",
            th2="H2",
            td11="<span>R1C1\t\t</span>",
            td12="\nR1C2",
            td21="<span>R2C1  </span>",
            td22="      R2C2",
            td31="<span>R3C1\r</span>",
            td32="R3C2",
        )

        results = list(
            table.apply(
                etree.fromstring(markup),
                thfuncs=[string.first_stripped_text, string.first_stripped_text],
                tdfuncs=[string.first_stripped_text, string.first_stripped_text],
            )
        )

        assert results == [
            ["H1", "H2"],
            ["R1C1", "R1C2"],
            ["R2C1", "R2C2"],
            ["R3C1", "R3C2"],
        ]

    @staticmethod
    def test_table_apply_wrong_length_raises(default_table):
        with pytest.raises(
            ValueError, match=re.escape("zip() argument 2 is longer than argument 1")
        ):
            list(
                table.apply(
                    default_table,
                    [string.first_stripped_text],
                    [string.first_stripped_text, string.first_stripped_text],
                )
            )

    @staticmethod
    def test_table_text_returns_expected(default_table):
        assert list(table.stripped_text(default_table)) == [
            ["{th1}", "{th2}"],
            ["{td11}", "{td12}"],
            ["{td21}", "{td22}"],
            ["{td31}", "{td32}"],
        ]

    @staticmethod
    def test_table_first_text_returns_expected(markup):
        markup = markup.format(
            th1="<span> H1\t</span>",
            th2="H2",
            td11="<span>R1C1\t\t</span>",
            td12="\nR1C2",
            td21="<span>R2C1  </span>",
            td22="      R2C2",
            td31="<span>R3C1\r</span>",
            td32="R3C2",
        )

        assert list(table.first_stripped_text(etree.fromstring(markup))) == [
            ["H1", "H2"],
            ["R1C1", "R1C2"],
            ["R2C1", "R2C2"],
            ["R3C1", "R3C2"],
        ]

    @staticmethod
    @pytest.mark.parametrize(
        ("tag", "missing"),
        [
            ("<tbody></tbody>", "<thead>"),
            ("<thead></thead>", "<tbody>"),
            ("", "<thead> and <tbody>"),
        ],
    )
    def test__select_table_raises_when_table_is_thead_or_tbody(tag, missing):
        elem = etree.fromstring(f"<table>{tag}</table>")
        with pytest.raises(
            ElementError, match=re.escape(f"<table> is missing {missing}.")
        ):
            table._select_table_children(elem)


class TestXPath:
    @staticmethod
    @pytest.fixture
    def markup():
        return etree.fromstring(
            """
            <html>
                <body>
                    <div class="item">One</div>
                    <div class="item">Two</div>
                    <span id="single">Hello</span>
                </body>
            </html>
            """
        )

    @staticmethod
    def test_element_list_returns_list_of_elements(markup):
        elems = xpath.element_list(markup, "//div[@class='item']")
        assert isinstance(elems, list)
        assert len(elems) == 2
        assert all(isinstance(e, ETreeElement) for e in elems)

    @staticmethod
    def test_first_element_d_returns_first_match(markup):
        elem = xpath.first_element_d(markup, "//div")
        assert elem is not None
        assert elem.tag == "div"
        assert elem.text == "One"

    @staticmethod
    def test_string_returns_string(markup):
        result = xpath.string(markup, "string(//span[@id='single'])")
        assert result == "Hello"

    @staticmethod
    @pytest.mark.parametrize(
        "selector",
        [
            "string(//div[@class='item'])",  # returns str
            "//div/text()",  # returns list[str]
        ],
    )
    def test_element_list_raises_when_returned_value_is_not_a_list_of_elements(
        markup, selector
    ):
        with pytest.raises(
            ValueError, match=re.escape("did not return list[ETreeElement].")
        ):
            xpath.element_list(markup, selector)

    @staticmethod
    def test_string_raises_when_xpath_returned_value_is_not_a_string(markup):
        with pytest.raises(ValueError, match=re.escape("did not return str.")):
            xpath.string(markup, "//div/text()")  # returns list[str]

    @staticmethod
    @pytest.mark.parametrize(
        ("func", "selector", "value"),
        [
            ("element_list", ".//missing", []),
            ("first_element_d", ".//missing", None),
            ("string_list", ".//missing/text()", []),
            ("string", "string(.//missing)", ""),
        ],
    )
    def test_func_returns_default_value_when_no_matches_are_found(
        markup, func, selector, value
    ):
        assert getattr(xpath, func)(markup, selector) == value

    @staticmethod
    def test_first_element_e_raises_when_no_matches_are_found(markup):
        with pytest.raises(ElementError):
            xpath.first_element_e(markup, "//section")

    @staticmethod
    def test_string_list_returns_list_of_strings(markup):
        result = xpath.string_list(markup, "//div/text()")
        assert result == ["One", "Two"]

    @staticmethod
    def test_string_list_raises_when_returned_value_is_not_a_list(markup):
        with pytest.raises(ValueError, match=re.escape("did not return list[str].")):
            xpath.string_list(markup, "string(//div/text())")

    @staticmethod
    def test_element_list_raises_when_returned_items_are_not_strings(markup):
        with pytest.raises(ValueError, match=re.escape("did not return list[str].")):
            xpath.string_list(markup, "//div")
