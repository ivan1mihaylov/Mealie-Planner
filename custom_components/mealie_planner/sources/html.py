"""A small HTML tree with CSS-like selection, on the standard library alone.

Enough for shop pages: tag names, classes, attributes, the descendant (" ")
and child (">") combinators. The integration needs no extra packages.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re

_VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "source", "track", "wbr",
}


class Node:
    """One element."""

    __slots__ = ("tag", "attrs", "children", "parent", "_text")

    def __init__(self, tag: str, attrs: dict[str, str], parent: Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.children: list[Node | str] = []
        self.parent = parent
        self._text: str | None = None

    @property
    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    def get(self, name: str, default: str = "") -> str:
        return self.attrs.get(name, default)

    def text(self) -> str:
        """All text inside, with whitespace collapsed."""
        if self._text is None:
            parts: list[str] = []
            self._collect(parts)
            self._text = re.sub(r"\s+", " ", " ".join(parts)).strip()
        return self._text

    def raw_text(self) -> str:
        """Text as written, for <script> contents."""
        return "".join(child for child in self.children if isinstance(child, str))

    def _collect(self, parts: list[str]) -> None:
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag not in ("script", "style"):
                child._collect(parts)

    def elements(self):
        """Every element below this one, in document order."""
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.elements()

    def select(self, selector: str) -> list[Node]:
        found: list[Node] = []
        for part in selector.split(","):
            steps = _parse(part.strip())
            found.extend(node for node in self.elements() if _matches(node, steps, self))
        seen: set[int] = set()
        unique = []
        for node in found:
            if id(node) not in seen:
                seen.add(id(node))
                unique.append(node)
        return unique

    def select_one(self, selector: str) -> Node | None:
        found = self.select(selector)
        return found[0] if found else None


def _parse(selector: str) -> list[tuple[str, dict]]:
    """[(combinator, compound)], read right to left later."""
    tokens = re.findall(r">|[^\s>]+", selector)
    steps: list[tuple[str, dict]] = []
    combinator = " "
    for token in tokens:
        if token == ">":
            combinator = ">"
            continue
        compound: dict = {"tag": None, "classes": [], "attrs": []}
        match = re.match(r"[a-zA-Z][\w-]*|\*", token)
        rest = token
        if match:
            compound["tag"] = None if match.group(0) == "*" else match.group(0).lower()
            rest = token[match.end():]
        for cls in re.findall(r"\.([\w-]+)", re.sub(r"\[[^\]]*\]", "", rest)):
            compound["classes"].append(cls)
        for attr in re.findall(r"\[([^\]]+)\]", rest):
            name, _, value = attr.partition("=")
            compound["attrs"].append((name.strip(), value.strip().strip("'\"") if value else None))
        steps.append((combinator, compound))
        combinator = " "
    return steps


def _fits(node: Node, compound: dict) -> bool:
    if compound["tag"] and node.tag != compound["tag"]:
        return False
    if compound["classes"] and not set(compound["classes"]) <= node.classes:
        return False
    for name, value in compound["attrs"]:
        if name not in node.attrs:
            return False
        if value is not None and node.attrs[name] != value:
            return False
    return True


def _matches(node: Node, steps: list[tuple[str, dict]], root: Node) -> bool:
    if not steps:
        return True
    combinator, compound = steps[-1]
    if not _fits(node, compound):
        return False
    rest = steps[:-1]
    if not rest:
        return True
    if combinator == ">":
        parent = node.parent
        return parent is not None and parent is not root and _matches(parent, rest, root)
    ancestor = node.parent
    while ancestor is not None and ancestor is not root:
        if _matches(ancestor, rest, root):
            return True
        ancestor = ancestor.parent
    return False


class _Builder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self._current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {name: value or "" for name, value in attrs}, self._current)
        self._current.children.append(node)
        if tag not in _VOID:
            self._current = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {name: value or "" for name, value in attrs}, self._current)
        self._current.children.append(node)

    def handle_endtag(self, tag):
        node = self._current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self._current = node.parent

    def handle_data(self, data):
        self._current.children.append(data)


def parse(html: str) -> Node:
    """The document's root node."""
    builder = _Builder()
    builder.feed(html)
    builder.close()
    return builder.root
