from __future__ import annotations

import re
from html.parser import HTMLParser

_BLOCK_TAGS = {
    "address",
    "article",
    "blockquote",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
}
_SIGNATURE_CLOSINGS = {
    "best regards,",
    "kind regards,",
    "many thanks,",
    "regards,",
    "thanks,",
}
_ORIGINAL_MESSAGE_MARKERS = {
    "-----original message-----",
    "________________________________",
}
_OUTLOOK_HEADER_WINDOW = 6


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "br":
            self._line_break()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self._line_break()

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def _line_break(self) -> None:
        if not self.parts or not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def text(self) -> str:
        return "".join(self.parts)


def html_to_text(value: str) -> str:
    """Convert message HTML into conservative plain text without external dependencies."""
    if not value.strip():
        return ""
    parser = _HTMLTextExtractor()
    parser.feed(value)
    parser.close()
    return parser.text()


def normalize_message_body(*, body_text: str, body_html: str) -> str:
    """Return the useful new-message content while retaining raw bodies separately."""
    source = body_text if body_text.strip() else html_to_text(body_html)
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in source.split("\n")]
    lines = _strip_quoted_history(lines)
    lines = _strip_signature(lines)
    return _collapse_blank_lines(lines)


def _strip_quoted_history(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        lowered = line.lower()
        if lowered in _ORIGINAL_MESSAGE_MARKERS:
            return lines[:index]
        if re.match(r"^on .+ wrote:$", line, flags=re.IGNORECASE):
            return lines[:index]
        if lowered.startswith("from:") and _looks_like_outlook_history(lines, index):
            return lines[:index]

    first_quoted_index = next(
        (index for index, line in enumerate(lines) if line.startswith(">")),
        None,
    )
    if first_quoted_index is not None:
        remainder = [line for line in lines[first_quoted_index:] if line]
        if remainder and all(line.startswith(">") for line in remainder):
            return lines[:first_quoted_index]
    return lines


def _looks_like_outlook_history(lines: list[str], start: int) -> bool:
    window = [line.lower() for line in lines[start : start + _OUTLOOK_HEADER_WINDOW]]
    return any(line.startswith(("sent:", "date:")) for line in window) and any(
        line.startswith(("to:", "subject:")) for line in window
    )


def _strip_signature(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if line in {"--", "-- "}:
            return lines[:index]

    for index, line in enumerate(lines):
        if line.lower() not in _SIGNATURE_CLOSINGS:
            continue
        non_empty_after = [item for item in lines[index + 1 :] if item]
        if len(non_empty_after) <= 8:
            return lines[:index]
    return lines


def _collapse_blank_lines(lines: list[str]) -> str:
    collapsed: list[str] = []
    previous_blank = True
    for line in lines:
        is_blank = not line
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank

    while collapsed and not collapsed[-1]:
        collapsed.pop()
    return "\n".join(collapsed).strip()
