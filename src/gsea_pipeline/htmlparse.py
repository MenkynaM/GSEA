"""A very small HTML reader, enough for GSEA reports and MSigDB index pages.

This replaces the BeautifulSoup dependency.  It is not a general HTML5 parser:
it builds a tree from :mod:`html.parser` events with just enough implicit-close
handling for the HTML 4.01 that GSEA emits, where ``<li>`` tags are never closed
and ``<th>`` cells sit outside any row.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser

#: Elements that never have children or an end tag.
VOID_TAGS = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)

#: An open element of the key is closed by a start tag in the value set.
IMPLICIT_CLOSE = {
    "li": {"li"},
    "p": {"p", "div", "ul", "ol", "table", "h1", "h2", "h3", "h4", "h5", "h6"},
    "td": {"td", "th", "tr"},
    "th": {"td", "th", "tr"},
    "tr": {"tr"},
    "option": {"option"},
}


@dataclass
class Node:
    """An element, its attributes, and its children (elements and text)."""

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """All descendant text, concatenated."""
        parts: list[str] = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text)
        return "".join(parts)

    @property
    def classes(self) -> list[str]:
        return self.attrs.get("class", "").split()

    def iter_elements(self) -> Iterator[Node]:
        """Yield every descendant element, depth first."""
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.iter_elements()

    def find_all(self, tag: str, *, css_class: str | None = None) -> list[Node]:
        """Every descendant with this tag, optionally carrying this class."""
        return [
            node
            for node in self.iter_elements()
            if node.tag == tag and (css_class is None or css_class in node.classes)
        ]

    def find(self, tag: str, *, css_class: str | None = None) -> Node | None:
        """The first descendant matching :meth:`find_all`, or ``None``."""
        for node in self.iter_elements():
            if node.tag == tag and (css_class is None or css_class in node.classes):
                return node
        return None


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self._stack: list[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs) -> None:
        while len(self._stack) > 1:
            open_tag = self._stack[-1].tag
            if tag in IMPLICIT_CLOSE.get(open_tag, ()):
                self._stack.pop()
            else:
                break
        node = Node(tag, {k: (v or "") for k, v in attrs})
        self._stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs) -> None:
        node = Node(tag, {k: (v or "") for k, v in attrs})
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        for depth in range(len(self._stack) - 1, 0, -1):
            if self._stack[depth].tag == tag:
                del self._stack[depth:]
                return
        # A stray end tag with no matching start tag: ignore it, as browsers do.

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def parse_html(markup: str) -> Node:
    """Parse ``markup`` into a tree rooted at a synthetic ``#document`` node."""
    builder = _TreeBuilder()
    builder.feed(markup)
    builder.close()
    return builder.root


@dataclass(frozen=True)
class Link:
    """An ``<a>`` element reduced to the two things callers want."""

    href: str
    text: str


def iter_links(root: Node) -> list[Link]:
    """Every ``<a>`` element that has an ``href``."""
    return [
        Link(node.attrs["href"], node.text.strip())
        for node in root.find_all("a")
        if "href" in node.attrs
    ]


def list_items(root: Node) -> list[str]:
    """The text of every ``<li>``, whitespace collapsed."""
    return [" ".join(node.text.split()) for node in root.find_all("li")]


@dataclass(frozen=True)
class Table:
    """A parsed HTML table."""

    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def read_table(container: Node, *, drop_first_column: bool = True) -> Table:
    """Read the ``<th>`` header and ``<tr>``/``<td>`` rows under ``container``.

    GSEA's tables open with an unlabelled column holding the row number, which
    ``drop_first_column`` discards.
    """
    start = 1 if drop_first_column else 0
    header = tuple(cell.text.strip() for cell in container.find_all("th")[start:])
    rows = []
    for row in container.find_all("tr"):
        cells = row.find_all("td")[start:]
        if cells:
            rows.append(tuple(cell.text.strip() for cell in cells))
    return Table(header, tuple(rows))
