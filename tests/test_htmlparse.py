"""The stdlib HTML reader, on the malformed HTML 4.01 that GSEA emits."""

from __future__ import annotations

from gsea_pipeline.htmlparse import iter_links, list_items, parse_html, read_table

from .sample_data import GENE_SET_HTML, GSEA_INDEX_HTML


def test_unclosed_list_items_are_closed_implicitly():
    """GSEA never closes ``<li>``; without implicit closing they would nest."""
    items = list_items(parse_html(GSEA_INDEX_HTML))
    assert items[0] == "4 / 19 gene sets are upregulated in phenotype P"
    assert items[1] == "0 gene sets are significant at FDR < 25%"
    assert len(items) == 8


def test_character_references_are_decoded():
    assert "<" in list_items(parse_html("<ul><li>FDR &lt; 25%</ul>"))[0]


def test_nested_element_text_is_concatenated():
    root = parse_html("<p>a <b>bold</b> word</p>")
    assert root.find("p").text == "a bold word"


def test_links_carry_href_and_text():
    links = iter_links(parse_html(GENE_SET_HTML))
    assert links[0].href == "https://ensembl.org/x?q=HRG"
    assert links[0].text == "HRG"


def test_links_without_href_are_skipped():
    links = iter_links(parse_html('<a name="anchor">x</a><a href="y.html">y</a>'))
    assert [(link.href, link.text) for link in links] == [("y.html", "y")]


def test_find_filters_by_class():
    root = parse_html(GENE_SET_HTML)
    assert root.find("div", css_class="richTable") is not None
    assert root.find("div", css_class="nonexistent") is None
    assert len(root.find_all("div")) == 2


def test_read_table_drops_the_row_number_column():
    container = parse_html(GENE_SET_HTML).find("div", css_class="richTable")
    table = read_table(container)
    assert table.header == ("SYMBOL", "TITLE", "CORE ENRICHMENT")
    assert table.rows == (
        ("HRG", "histidine rich glycoprotein", "Yes"),
        ("APOA1", '"apolipoprotein A1, variant"', "No"),
    )


def test_read_table_can_keep_every_column():
    container = parse_html(GENE_SET_HTML).find("div", css_class="richTable")
    table = read_table(container, drop_first_column=False)
    assert table.header[0] == ""
    assert table.rows[0][0] == "1"


def test_void_and_stray_tags_do_not_unbalance_the_tree():
    root = parse_html("<div><br><img src='x'><p>text</p></span></div><div>second</div>")
    assert len(root.find_all("div")) == 2
    assert root.find("p").text == "text"
