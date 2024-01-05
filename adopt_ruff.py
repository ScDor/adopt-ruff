from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from mdutils.mdutils import MdUtils
from tabulate import tabulate

from models.ruff_output import Violation
from models.rule import Rule

if TYPE_CHECKING:
    from pydantic import BaseModel

ARTIFACTS_PATH = Path("artifacts")
ARTIFACTS_PATH.mkdir(exist_ok=True)


def load(
    rules_path: Path = Path("rules.json"),
    violations_path: Path = Path("violations.json"),
) -> tuple[tuple[Rule, ...], tuple[Violation, ...]]:
    def _load_json_list(path: Path, model: BaseModel):
        with path.open() as open_file:
            return tuple(model(**value) for value in json.load(open_file))

    return (
        _load_json_list(rules_path, Rule),
        _load_json_list(violations_path, Violation),
    )


def run(
    rules: tuple[Rule, ...],
    violations: tuple[Violation, ...],
    repo_name: str = "dummy/repo",
) -> str:
    md = MdUtils("output", f"adopt-ruff report for {repo_name}")

    # TODO ignore configured/ignored?
    if already_respected := respected_rules(violations, rules):
        md.new_header(1, "Respected Ruff rules")
        md.new_line(f"{len(already_respected)} Ruff rules can be added right away 🚀")
        md.new_line(f"{repo_name} already respects them - enforcing will be seamless.")
        md.new_paragraph(tabulate(already_respected, tablefmt="github", headers="keys"))
        # TODO save a CSV artifact

    # TODO add autofixable table (always/sometimes)
    return md.get_md_text()


def respected_rules(
    violations: tuple[Violation, ...],
    rules: tuple[Rule, ...],
) -> tuple[dict]:
    violation_codes = {v.code for v in violations}
    respected = [rule for rule in rules if rule.code not in violation_codes]
    return tuple(
        {
            "Linter": rule.linter,
            "Code": rule.code,
            "Name": rule.name,
            "Fixable": rule.fix.one_word,
            "Preview": rule.preview,
        }
        for rule in sorted(respected, key=lambda r: r.code)
    )


rules, violations = load()
result = run(rules, violations)
Path("result.md").write_text(result)
print(result)