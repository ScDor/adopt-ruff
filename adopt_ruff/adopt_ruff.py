import json
from pathlib import Path

from mdutils.mdutils import MdUtils
from pydantic import BaseModel

from adopt_ruff.models.ruff_config import RuffConfig
from adopt_ruff.models.ruff_output import Violation
from adopt_ruff.models.rule import FixAvailability, Rule
from adopt_ruff.utils import output_table

(ARTIFACTS_PATH := Path("artifacts")).mkdir(exist_ok=True)


def load(
    rules_path: Path = Path("rules.json"),
    violations_path: Path = Path("violations.json"),
    configurations_path: Path = Path("pyproject.toml"),
) -> tuple[
    tuple[Rule, ...],
    tuple[Violation, ...],
    RuffConfig,
]:
    def _load_json_list(path: Path, model: BaseModel):
        with path.open() as open_file:
            return tuple(model(**value) for value in json.load(open_file))

    rules = _load_json_list(rules_path, Rule)

    violations = _load_json_list(violations_path, Violation)
    config = RuffConfig.from_path(configurations_path, rules)

    return rules, violations, config


def run(
    rules: tuple[Rule, ...],
    violations: tuple[Violation, ...],
    config: RuffConfig,
    repo_name: str,
) -> str:
    md = MdUtils("output")
    md.new_header(1, f"adopt-ruff report for {repo_name}")
    rules_already_configured = config.all_rules

    if respected := sorted(
        respected_rules(violations, rules, rules_already_configured),
        key=lambda rule: rule.code,
    ):
        md.new_header(2, "Respected Ruff rules")
        md.new_line(
            f"{len(respected)} Ruff rules are already respected in the repo - "
            "they can be added right away 🚀"
        )
        output_table(
            items=respected,
            path=ARTIFACTS_PATH / "respected.csv",
            md=md,
            collapsible=True,
        )

    if autofixable := sorted(
        autofixable_rules(violations, rules, rules_already_configured),
        key=lambda rule: rule.code,
    ):
        md.new_header(2, "Autofixable Ruff rules")
        md.new_line(
            f"{len(autofixable)} Ruff rules are violated in the repo, but can be auto-fixed 🪄"
        )
        output_table(
            items=autofixable,
            path=ARTIFACTS_PATH / "autofixable.csv",
            md=md,
            collapsible=True,
        )

    return md.get_md_text()


def respected_rules(
    violations: tuple[Violation, ...],
    rules: tuple[Rule, ...],
    rules_already_configured: set[Rule],
) -> set[Rule]:
    violated_codes = {v.code for v in violations}

    return {
        rule
        for rule in rules
        if (rule.code not in violated_codes) and (rule not in rules_already_configured)
    }


def autofixable_rules(
    violations: tuple[Violation, ...],
    rules: tuple[Rule, ...],
    rules_already_configured: set[Rule],
    include_sometimes_fixable: bool = False,
    include_preview: bool = False,
) -> set[Rule]:
    violated_codes = {v.code for v in violations}

    return {
        rule
        for rule in rules
        if rule.code in violated_codes
        and rule not in rules_already_configured
        and rule.is_fixable
        and (not rule.preview if not include_preview else True)
        and (
            rule.fix == FixAvailability.ALWAYS
            if not include_sometimes_fixable
            else True
        )
    }


def main():
    rules, violations, config = load()
    result = run(
        rules, violations, config, repo_name="dummy/repo"
    )  # TODO repo name arg

    Path("result.md").write_text(result)


if __name__ == "__main__":
    main()
