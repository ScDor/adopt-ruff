from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class FixAvailability(Enum):
    ALWAYS = "Fix is always available."
    SOMETIMES = "Fix is sometimes available."
    NOT = "Fix is not available."

    @property
    def one_word(self) -> str:
        match self:
            case FixAvailability.ALWAYS:
                return "Always"
            case FixAvailability.SOMETIMES:
                return "Sometimes"
            case FixAvailability.NOT:
                return "No"
            case _:
                raise ValueError


class Rule(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    name: str
    code: str
    linter: str
    summary: str
    message_formats: tuple[str, ...]
    fix: FixAvailability
    explanation: str
    preview: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Name": self.name,
            "Fixable": self.fix.one_word,
            "Preview": self.preview,
            "Linter": self.linter,
        }

    @property
    def is_fixable(self):
        return self.fix in {FixAvailability.ALWAYS, FixAvailability.SOMETIMES}
