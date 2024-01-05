import json
from pathlib import Path

from mdutils.mdutils import MdUtils
from pydantic import BaseModel

from models.ruff_output import Violation
from models.rule import Rule
from utils import output_table

(ARTIFACTS_PATH := Path("artifacts")).mkdir(exist_ok=True)


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
        md.new_line(
            f"{len(already_respected)} Ruff rules are respected in the repo - "
            "They can be added right away 🚀"
        )
        output_table(
            already_respected,
            ARTIFACTS_PATH / "respected.csv",
            md=md,
            collapsible=True,
        )
    return md.get_md_text()


def respected_rules(
    violations: tuple[Violation, ...],
    rules: tuple[Rule, ...],
) -> tuple[Rule, ...]:
    violated_codes = {v.code for v in violations}
    return tuple(rule for rule in rules if rule.code not in violated_codes)


rules, violations = load()
result = run(rules, violations)
Path("result.md").write_text(result)
