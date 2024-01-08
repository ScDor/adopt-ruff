from __future__ import annotations

from pydantic import BaseModel


class Location(BaseModel, frozen=True):
    column: int
    row: int


class Edit(BaseModel, frozen=True):
    content: str
    end_location: Location
    location: Location


class Fix(BaseModel, frozen=True):
    applicability: str
    edits: tuple[Edit, ...]
    message: str


class Violation(BaseModel, frozen=True):
    cell: None  # TODO handle notebook output
    code: str
    end_location: Location
    filename: str
    fix: Fix | None
    location: Location
    message: str
    noqa_row: int
    url: str
