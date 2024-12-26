from __future__ import annotations

from pydantic import BaseModel


class Location(BaseModel):
    column: int
    row: int


class Edit(BaseModel):
    content: str
    end_location: Location
    location: Location


class Fix(BaseModel):
    applicability: str
    edits: tuple[Edit, ...]
    message: str | None


class Violation(BaseModel):
    cell: None  # TODO handle notebook output
    code: str
    end_location: Location
    filename: str
    fix: Fix | None
    location: Location
    message: str
    noqa_row: int
    url: str
