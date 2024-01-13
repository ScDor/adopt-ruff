import itertools
import json
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

import more_itertools
import typer
from loguru import logger
from mdutils.mdutils import MdUtils
from packaging.version import Version

from adopt_ruff.models.ruff_config import RuffConfig
from adopt_ruff.models.ruff_output import Violation
from adopt_ruff.models.rule import FixAvailability, Rule
from adopt_ruff.utils import output_table

(ARTIFACTS_PATH := Path("artifacts")).mkdir(exist_ok=True)


def run_ruff() -> tuple[set[Rule], tuple[Violation, ...], Version]:
    try:
        ruff_version = Version(
            subprocess.run(
                ["ruff", "--version"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.split()[1]  # ruff's output is `ruff x.y.z`
        )

    except FileNotFoundError:
        logger.error("Make sure ruff is installed (pip install ruff)")
        sys.exit(1)

    # Now when ruff is found, assume the following commands will run properly
    rules = {
        Rule(**value)
        for value in json.loads(
            subprocess.run(
                ["ruff", "rule", "--all", "--output-format=json"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout
        )
    }
    violations = tuple(
        Violation(**value)
        for value in json.loads(
            subprocess.run(
                ["ruff", ".", "--output-format=json", "--select=ALL", "--exit-zero"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout
        )
    )
    return rules, violations, ruff_version


def run(
    rules: set[Rule],
    violations: tuple[Violation, ...],
    config: RuffConfig,
    ruff_version: Version,
    include_sometimes_fixable: bool,
    include_preview: bool,
    repo_name: str,
) -> str:
    logger.info(
        f"{include_sometimes_fixable=}, {include_preview=}, {repo_name=}, {ruff_version=}"
    )
    md = MdUtils("output")

    repo_name_header = f"for {repo_name} " if repo_name else ""
    md.new_header(1, f"adopt-ruff report {repo_name_header}(ruff {ruff_version!s})")

    configured_rules = config.all_rules

    if respected := sorted(
        respected_rules(violations, rules, configured_rules),
        key=lambda rule: rule.code,
    ):
        md.new_header(2, "Respected Ruff rules")
        md.new_line(
            f"{len(respected)} Ruff rules are already respected in the repo - "
            "they can be added right away 🚀"
        )
        output_table(
            items=([r.as_dict for r in respected]),
            path=ARTIFACTS_PATH / "respected.csv",
            md=md,
            collapsible=True,
        )

    if autofixable := sort_by_code(
        autofixable_rules(
            violations,
            rules,
            configured_rules,
            include_sometimes_fixable,
            include_preview,
        )
        # TODO pass args
    ):
        md.new_header(2, "Autofixable Ruff rules")
        md.new_line(
            f"{len(autofixable)} Ruff rules are violated in the repo, but can be auto-fixed 🪄"
        )
        output_table(
            items=([r.as_dict for r in autofixable]),
            path=ARTIFACTS_PATH / "autofixable.csv",
            md=md,
            collapsible=True,
        )

    if violated_rule_to_violations := (
        violated_rules(
            violations,
            rules,
            excluded_rules=(
                itertools.chain.from_iterable(
                    (configured_rules, respected, autofixable)
                )
            ),
        )
    ):
        rule_to_violation_count = {
            rule: len(violations_)
            for rule, violations_ in violated_rule_to_violations.items()
        }

        applicable_rules = sorted(
            violated_rule_to_violations.keys(),
            key=lambda rule: (rule_to_violation_count[rule], rule.linter, rule.code),
        )

        md.new_header(2, "Applicable Rules")
        md.new_line(
            f"{len(applicable_rules)} other Ruff rules are not yet configured in the repository"
        )
        output_table(
            items=(
                [
                    r.as_dict | {"Violations": rule_to_violation_count[r]}
                    for r in applicable_rules
                ]
            ),
            path=ARTIFACTS_PATH / "applicable.csv",
            md=md,
            collapsible=True,
        )

    return md.get_md_text()


def sort_by_code(rules: Iterable[Rule]) -> list[Rule]:
    return sorted(rules, key=lambda rule: rule.code)


def respected_rules(
    violations: tuple[Violation, ...],
    rules: Iterable[Rule],
    configured_rules: set[Rule],
) -> set[Rule]:
    violated_codes = {v.code for v in violations}

    return {
        rule
        for rule in rules
        if (rule.code not in violated_codes) and (rule not in configured_rules)
    }


def autofixable_rules(
    violations: tuple[Violation, ...],
    rules: Iterable[Rule],
    configured_rules: set[Rule],
    include_sometimes_fixable: bool = False,
    include_preview: bool = False,
) -> set[Rule]:
    violated_codes = {v.code for v in violations}

    return {
        rule
        for rule in rules
        if rule.code in violated_codes
        and rule not in configured_rules
        and rule.is_fixable
        and (not rule.preview if not include_preview else True)
        and (
            rule.fix == FixAvailability.ALWAYS
            if not include_sometimes_fixable
            else True
        )
    }


def violated_rules(
    violations: tuple[Violation, ...],
    rules: set[Rule],
    excluded_rules: Iterable[Rule],
) -> dict[Rule, tuple[Violation, ...]]:
    ignore_codes = {rule.code for rule in excluded_rules}
    return {
        rule: violations
        for rule, violations in map_rules_to_violations(rules, violations).items()
        if rule.code not in ignore_codes
    }


def map_rules_to_violations(
    rules: Iterable[Rule],
    violations: Iterable[Violation],
) -> dict[Rule, tuple[Violation, ...]]:
    code_to_violations = more_itertools.bucket(violations, key=lambda v: v.code)
    code_to_rule = {rule.code: rule for rule in rules}

    return {
        code_to_rule[code]: tuple(code_to_violations[code])
        for code in code_to_violations
    }


def _main(
    include_preview: bool,
    include_sometimes_fixable: bool,
    repo_name: str = "",
):
    rules, violations, ruff_version = run_ruff()
    config: RuffConfig = RuffConfig.from_path(Path("pyproject.toml"), rules)

    result = run(
        rules,
        violations,
        config,
        ruff_version=ruff_version,
        include_preview=include_preview,
        include_sometimes_fixable=include_sometimes_fixable,
        repo_name=repo_name,
    )

    Path("result.md").write_text(result)


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()
