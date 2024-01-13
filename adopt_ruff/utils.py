import csv
from collections.abc import Iterable
from pathlib import Path

from loguru import logger
from mdutils.mdutils import MdUtils
from tabulate import tabulate

(ARTIFACTS_PATH := Path("artifacts")).mkdir(exist_ok=True)

logger.add((ARTIFACTS_PATH / "adopt-ruff.log"), level="DEBUG")


def make_collapsible(content: str, summary: str) -> str:
    return f"""<details>
<summary>{summary}</summary>

{content}

</details>
"""


def table_to_csv(items: list[dict], path: Path) -> None:
    if not items:
        logger.warning(f"no items to write to {path.name}, skipping")
        return

    if len(items) > 1 and not all(
        # assert all keys are in the same order
        item.keys() == items[0].keys()
        for item in items[1:]
    ):
        raise ValueError("All table row keys must be identical, and in the same order")

    with path.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(items[0].keys())  # Headers
        writer.writerows(item.values() for item in items)

    logger.debug(f"wrote {len(items)} to {path.absolute()!s}")


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

    md_table = tabulate(
        [make_name_clickable(item) for item in items],
        tablefmt="github",
        headers="keys",
    )

    if collapsible:
        md_table = make_collapsible(md_table, summary=collapsible_summary)

    md.new_line(md_table)
    table_to_csv(list(items), path)


def make_name_clickable(item: dict) -> dict:
    if not (name := item.get("Name")):
        return item
    return item | {"Name": f"[{name}](https://docs.astral.sh/ruff/rules/{name})"}


def search_config_file(path: Path) -> Path | None:
    """
    Searches for common configuration files under the given directory.
    """
    for name in ("pyproject.toml", "ruff.toml", ".ruff.toml"):
        if (file_path := path / name).exists():
            logger.info(f"found config file at {file_path.resolve()!s}")
            return file_path
    return None
