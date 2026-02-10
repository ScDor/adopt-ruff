import csv
import re
from collections import defaultdict
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
    """Creates a markdown table, and saves to a CSV."""
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
    """Searches for common configuration files under the given directory."""
    for name in ("pyproject.toml", "ruff.toml", ".ruff.toml"):
        if (file_path := path / name).exists():
            logger.info(f"found config file at {file_path.resolve()!s}")
            return file_path
    return None


def extract_category_prefix(code: str) -> str:
    """
    Extracts the category prefix from a rule code.
    Examples: RUF001 -> RUF, B010 -> B, ASYNC100 -> ASYNC
    """
    match = re.match(r"^([A-Z]+)", code)
    return match.group(1) if match else code


def find_complete_categories(rules: Iterable, all_rules: set) -> dict[str, tuple[str, int]]:
    """
    Finds categories where ALL rules from that category are in the given set.

    Args:
        rules: The rules in the current situation (e.g., autofixable, respected)
        all_rules: All available rules

    Returns:
        Dict mapping category prefix to (linter_name, count)
    """
    from adopt_ruff.models.rule import Rule

    rules_list = list(rules) if not isinstance(rules, list) else rules

    # Group all rules by category
    all_by_category: dict[str, list[Rule]] = defaultdict(list)
    for rule in all_rules:
        prefix = extract_category_prefix(rule.code)
        all_by_category[prefix].append(rule)

    # Group current situation rules by category
    current_by_category: dict[str, list[Rule]] = defaultdict(list)
    for rule in rules_list:
        prefix = extract_category_prefix(rule.code)
        current_by_category[prefix].append(rule)

    # Find complete categories (all rules from category are in current situation)
    complete_categories = {}
    for prefix, current_rules in current_by_category.items():
        all_in_category = all_by_category[prefix]
        if len(current_rules) == len(all_in_category) and len(current_rules) > 0:
            # All rules from this category are in the current situation
            linter_name = current_rules[0].linter
            complete_categories[prefix] = (linter_name, len(current_rules))

    return complete_categories


def generate_pyproject_suggestion(category_prefixes: list[str], section: str) -> str:
    """
    Generates a pyproject.toml configuration suggestion.

    Args:
        category_prefixes: List of category prefixes (e.g., ["RUF", "ASYNC"])
        section: Either "select" for respected/autofixable or "ignore" for applicable

    Returns:
        Formatted configuration suggestion
    """
    if not category_prefixes:
        return ""

    codes = ", ".join(f'"{prefix}"' for prefix in sorted(category_prefixes))
    return f"""```toml
[tool.ruff.lint]
{section} = [{codes}]
```"""
