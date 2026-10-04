from dataclasses import dataclass
from typing import Literal

SpecialistFieldKind = Literal["text", "code", "url", "multiline"]


@dataclass(frozen=True)
class SpecialistField:
    key: str
    label: str
    value: str
    kind: SpecialistFieldKind = "text"
