"""Tests for `nobrakes._element_utils`."""

import re

from lxml import etree
import pytest

from nobrakes._element_utils import string, table, xpath
from nobrakes.exceptions import ElementError
from nobrakes.typing import ETreeElement


class TestString:
    @pytest.fixture(scope="class")
    def div(self):
        return etree.fromstring("<div>\t\nHello <b> world </b>!</div>")

    def test_iter_stripped_text_returns_expected_value(self, div):
        assert list(string.iter_stripped_text(div)) == ["Hello", "world", "!"]

    @pytest.mark.parametrize(
        ("func", "markup", "expected"),
        [
            (string.stripped_text, "<div>\t\nHello <b> world </b>!</div>", "Hello"),
            (string.stripped_text, "<p></p>", ""),
            (string.stripped_text_e, "<div>\t\nHello <b> world </b>!</div>", "Hello"),
            (string.first_stripped_text, "<ul><li>one</li><li>two</li></ul>", "one"),
            (string.href, '<a href="/test">anchor</a>', "/test"),
            (string.href, "<a>anchor</a>", None),
            (string.href_e, '<a href="/test">anchor</a>', "/test"),
        ],
    )
    def test_func_returns_expected_value(self, func, markup, expected):
        elem = etree.fromstring(markup)
        assert func(elem) == expected

    @pytest.mark.parametrize(
        ("func", "exc_type"),
        [
            (string.stripped_text_e, ElementError),
            (string.first_stripped_text_e, ElementError),
            (string.href_e, ElementError),
        ],
    )
    def test_func_raises_when_string_is_missing(self, func, exc_type):
        elem = etree.fromstring("<p>  \t \n   \t  </p>")
        with pytest.raises(exc_type):
            func(elem)


class TestTable:
    @pytest.fixture(scope="class")
    def markup(self):
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

    @pytest.fixture
    def default_table(self, markup):
        return etree.fromstring(markup)

    def test_column_returns_expected_values(self, default_table):
        tbody = default_table.find("./tbody")
        result = table.column(tbody, 1)
        assert [td.text for td in result] == ["{td11}", "{td21}", "{td31}"]

    def test_column_raises_when_i_gt_n_columns(self, default_table):
        tbody = default_table.find("./tbody")
        i = 3
        exc_msg = f"Index {i} is greater than the number of columns in <tbody>."
        with pytest.raises(IndexError, match=re.escape(exc_msg)):  # n columns == 2
            table.column(tbody, i)

    def test_filtered_tbody_includes_matching_rows(self, markup):
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

    def test_table_apply_returns_expected(self, markup):
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

    def test_table_apply_wrong_length_raises(self, default_table):
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

    def test_table_text_returns_expected(self, default_table):
        assert list(table.stripped_text(default_table)) == [
            ["{th1}", "{th2}"],
            ["{td11}", "{td12}"],
            ["{td21}", "{td22}"],
            ["{td31}", "{td32}"],
        ]

    def test_table_first_text_returns_expected(self, markup):
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

    @pytest.mark.parametrize(
        ("tag", "missing"),
        [
            ("<tbody></tbody>", "<thead>"),
            ("<thead></thead>", "<tbody>"),
            ("", "<thead> and <tbody>"),
        ],
    )
    def test__select_table_raises_when_table_is_thead_or_tbody(self, tag, missing):
        elem = etree.fromstring(f"<table>{tag}</table>")
        with pytest.raises(
            ElementError, match=re.escape(f"<table> is missing {missing}.")
        ):
            table._select_table_children(elem)


class TestXPath:
    @pytest.fixture(scope="class")
    def markup(self):
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

    def test_string_returns_string(self, markup):
        result = xpath.string(markup, "string(//span[@id='single'])")
        assert result == "Hello"

    def test_string_list_returns_list_of_strings(self, markup):
        result = xpath.string_list(markup, "//div/text()")
        assert result == ["One", "Two"]

    def test_element_list_returns_list_of_elements(self, markup):
        elems = xpath.element_list(markup, "//div[@class='item']")
        assert isinstance(elems, list)
        assert len(elems) == 2
        assert all(isinstance(e, ETreeElement) for e in elems)

    def test_first_element_d_returns_first_match(self, markup):
        elem = xpath.first_element_d(markup, "//div")
        assert elem is not None
        assert elem.tag == "div"
        assert elem.text == "One"

    def test_first_element_e_raises_when_no_matches_are_found(self, markup):
        with pytest.raises(ElementError):
            xpath.first_element_e(markup, "//section")

    @pytest.mark.parametrize(
        ("f", "selector", "v"),
        [
            (xpath.element_list, ".//missing", []),
            (xpath.first_element_d, ".//missing", None),
            (xpath.string_list, ".//missing/text()", []),
            (xpath.string, "string(.//missing)", ""),
        ],
    )
    def test_func_returns_default_value_when_no_matches_are_found(
        self, markup, f, selector, v
    ):
        assert f(markup, selector) == v

    @pytest.mark.parametrize(
        ("f", "selector", "t"),
        [
            (xpath.string, "//div/text()", "str"),
            (xpath.string_list, "string(//div/text())", "list[str]"),
            (xpath.string_list, "//div", "list[str]"),
            (xpath.element_list, "string(//div[@class='item'])", "list[ETreeElement]"),
            (xpath.element_list, "//div/text()", "list[ETreeElement]"),
        ],
    )
    def test_raises_when_returned_value_is_not_a_t(self, f, markup, selector, t):
        with pytest.raises(ValueError, match=re.escape(f"did not return {t}.")):
            f(markup, selector)
