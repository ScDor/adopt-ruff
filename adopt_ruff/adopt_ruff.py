import json
from collections.abc import Iterable
from pathlib import Path

from mdutils.mdutils import MdUtils
from pydantic import BaseModel, DirectoryPath

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


def find_applicable_rules(
    rules: tuple[Rule, ...],
    rules_already_configured: set[Rule],
):
    return set(rules).difference(rules_already_configured)


def find_respected_rules(
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


def find_autofixable_rules(
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


def output_rules(
    rules: Iterable[Rule],
    md: MdUtils,
    title: str,
    description: str,
    output_dir: DirectoryPath = ARTIFACTS_PATH,
    collapsible: bool = True,
):
    if not rules:
        return

    rules = tuple(sort_by_code(rules))

    md.new_header(2, f"{title.title()} Ruff rules")
    md.new_line(f"{len(rules)} Ruff rules {description}")

    output_table(
        items=sort_by_code(rules),
        path=output_dir / f"{title.lower()}.csv",
        md=md,
        collapsible=collapsible,
    )


def sort_by_code(rules: Iterable[Rule]) -> list[Rule]:
    return tuple(sorted(rules, key=lambda rule: rule.code))


def run(
    rules: tuple[Rule, ...],
    violations: tuple[Violation, ...],
    config: RuffConfig,
    repo_name: str,
) -> str:
    md = MdUtils("output")
    md.new_header(1, f"adopt-ruff report for {repo_name}")
    configured_rules = config.all_rules

    output_rules(
        rules=find_respected_rules(violations, rules, configured_rules),
        file_name="respected",
        title="Respected",
        description="are already respected in the repo - they can be added right away 🚀",
        md=md,
    )

    output_rules(
        title="autofixable",
        rules=find_autofixable_rules(  # TODO pass args
            violations, rules, configured_rules
        ),
        description="are violated in the repo, but can be auto-fixed 🪄",
        md=md,
    )

    output_rules(
        title="applicable",
        rules=find_applicable_rules(rules, configured_rules),
        description="are not yet configured in the repository 🛠️",
        md=md,
    )

    return md.get_md_text()


def main():
    rules, violations, config = load()
    result = run(
        rules, violations, config, repo_name="dummy/repo"
    )  # TODO repo name arg

    Path("result.md").write_text(result)


if __name__ == "__main__":
    main()
