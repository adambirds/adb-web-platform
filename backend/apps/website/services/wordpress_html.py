"""Convert archived editorial HTML to reviewable Markdown without active HTML."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "wbr",
}
SUPPRESSED_TAGS = {"script", "style", "iframe", "form", "noscript", "object", "svg"}


@dataclass
class HTMLNode:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list[HTMLNode | str] = field(default_factory=list)


class EditorialParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = HTMLNode("root")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = HTMLNode(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def tree(value: str) -> HTMLNode:
    parser = EditorialParser()
    # Divi stores some project bodies as unexpanded shortcodes. Keep their text.
    parser.feed(re.sub(r"\[/?et_pb_[^\]]*\]", "", unescape(value)))
    return parser.root


def node_text(node: HTMLNode | str) -> str:
    if isinstance(node, str):
        return node
    if node.tag in SUPPRESSED_TAGS:
        return ""
    separator = " " if node.tag in {"div", "p", "li", "br"} else ""
    return separator.join(node_text(child) for child in node.children)


def plain_text(value: str) -> str:
    return " ".join(node_text(tree(value)).split())


def html_to_markdown(
    value: str,
    origin: str,
    rewrite_link: Callable[[str], str],
    rewrite_image: Callable[[str], str],
) -> str:
    def render(node: HTMLNode | str) -> str:
        if isinstance(node, str):
            text = re.sub(r"\s+", " ", node)
            return re.sub(r"([\\*\[\]_])", r"\\\1", text)
        if node.tag in SUPPRESSED_TAGS:
            return ""
        content = "".join(render(child) for child in node.children)
        tag = node.tag
        if tag in {"p", "div", "section", "article", "figure", "figcaption"}:
            return f"\n\n{content.strip()}\n\n"
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            return f"\n\n{'#' * int(tag[1])} {content.strip()}\n\n"
        if tag == "br":
            return "\n"
        if tag == "hr":
            return "\n\n---\n\n"
        if tag in {"strong", "b"}:
            return f"**{content}**"
        if tag in {"em", "i"}:
            return f"*{content}*"
        if tag == "pre":
            return f"\n\n```\n{node_text(node).strip()}\n```\n\n"
        if tag == "code":
            return f"`{node_text(node).replace('`', '')}`"
        if tag in {"ul", "ol"}:
            items = [
                child
                for child in node.children
                if isinstance(child, HTMLNode) and child.tag == "li"
            ]
            lines = []
            for index, child in enumerate(items, 1):
                prefix = f"{index}. " if tag == "ol" else "- "
                lines.append(prefix + render(child).strip().replace("\n", "\n  "))
            return "\n\n" + "\n".join(lines) + "\n\n"
        if tag == "blockquote":
            return "\n\n" + "\n".join(f"> {line}" for line in content.strip().splitlines()) + "\n\n"
        if tag == "a":
            href = urljoin(origin + "/", node.attrs.get("href") or "")
            if urlsplit(href).scheme not in {"https", "http", "mailto"}:
                return content
            return (
                f"[{content.strip()}]({rewrite_link(href).replace(' ', '%20').replace(')', '%29')})"
            )
        if tag == "img":
            src = node.attrs.get("src") or node.attrs.get("data-src") or ""
            if not src:
                return ""
            url = urljoin(origin + "/", src)
            if urlsplit(url).scheme not in {"https", "http"}:
                return ""
            alt = (node.attrs.get("alt") or "").replace("[", "").replace("]", "")
            return f"![{alt}]({rewrite_image(url).replace(' ', '%20').replace(')', '%29')})"
        if tag == "table":
            # Retain table contents readably; the original structure remains in JSON.
            return "\n\n" + content + "\n\n"
        if tag == "tr":
            return content.strip() + "\n"
        if tag in {"th", "td"}:
            return content.strip() + " | "
        return content

    return re.sub(r"\n{3,}", "\n\n", render(tree(value))).strip()
