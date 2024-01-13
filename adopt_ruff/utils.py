import csv
from collections.abc import Iterable
from pathlib import Path

from loguru import logger
from mdutils.mdutils import MdUtils
from tabulate import tabulate

(ARTIFACTS_PATH := Path("artifacts")).mkdir(exist_ok=True)

logger.add((ARTIFACTS_PATH / "adopt-ruff.log"), level="TRACE")


def make_collapsible(content: str, summary: str) -> str:
    return f"""<details>
<summary>{summary}</summary>

{content}

</details>
"""


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


def output_table(
    items: Iterable[dict],
    path: Path,
    md: MdUtils,
    collapsible: bool,
    collapsible_summary: str = "Details",
) -> None:
    """
    Creates a markdown table, and saves to a CSV
    """
    md_table = tabulate(items, tablefmt="github", headers="keys")

    if collapsible:
        md_table = make_collapsible(md_table, summary=collapsible_summary)

    md.new_line(md_table)
    table_to_csv(list(items), path)
