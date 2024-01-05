import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from mdutils.mdutils import MdUtils
from tabulate import tabulate


def make_collapsible(md: str, summary: str) -> str:
    return tag_wrap(tag_wrap(summary, "summary") + md, "details")
    return "\n".join(
        (
            f"<details><summary>{summary}</summary>",
            md,
            "</details>",
        )
    )


def tag_wrap(string: str, tag: str, separator: str = "\n"):
    return separator.join(
        (
            f"<{tag}>",
            string,
            f"</{tag}>",
        )
    )


def table_to_csv(table: list[dict], path: Path):
    if len(table) > 1 and not all(
        # assert all keys are in the same order
        item.keys() == table[0].keys()
        for item in table[1:]
    ):
        raise ValueError("All table row keys must be identical, and in the same order")

    with path.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(table[0].keys())
        writer.writerows(item.values() for item in table)


class SupportsAsDict(Protocol):
    def as_dict(self) -> dict:
        ...


def output_table(
    items: Iterable[SupportsAsDict],
    path: Path,
    md: MdUtils,
    collapsible: bool,
    collapsible_summary: str = "See table",
) -> None:
    """
    Creates a markdown table, and saves to a CSV
    """
    as_dicts = tuple(item.as_dict for item in items)

    md_table = tabulate(as_dicts, tablefmt="github", headers="keys")

    if collapsible:
        md_table = make_collapsible(f"\n{md_table}", summary=collapsible_summary)

    md.new_line(md_table)
    table_to_csv(as_dicts, path)
