from collections.abc import Iterable
from pathlib import Path

from mdutils.mdutils import MdUtils

from models.ruff_config import RuffConfig
from models.ruff_output import Violation
from models.rule import FixAvailability, Rule
from utils import output_table


class BaseSuggestion:
    name: str

    @staticmethod
    def relevant_rules(
        rules: Iterable[Rule], violations: Iterable[Violation], config: RuffConfig
    ) -> Iterable[Rule]:
        raise NotImplementedError

    @staticmethod
    def output(rules: Iterable[Rule], md: MdUtils, output_path: Path):
        raise NotImplementedError


class Respected(BaseSuggestion):
    @staticmethod
    def relevant_rules(
        rules: Iterable[Rule],
        violations: Iterable[Violation],
        config: RuffConfig,
    ):
        return {
            rule
            for rule in rules
            if (rule.code not in {v.code for v in violations})
            and (rule not in config.all_rules)
        }

    @staticmethod
    def output(rules: Iterable[Rule], md: MdUtils, output_path: Path):
        md.new_header(2, "Respected Ruff rules")
        md.new_line(
            f"{len(rules)} Ruff rules are already respected in the repo - "
            "they can be added right away 🚀"
        )
        output_table(
            items=rules,
            path=output_path / "respected.csv",
            md=md,
            collapsible=True,
        )


class Autofixable(BaseSuggestion):
    @staticmethod
    def relevant_rules(
        rules: Iterable[Rule],
        violations: Iterable[Violation],
        config: RuffConfig,
        include_preview: bool = False,
        include_sometimes_fixable: bool = False,
    ):
        violated_codes = {v.code for v in violations}

        return {
            rule
            for rule in rules
            if rule.code in violated_codes
            and rule not in config.all_rules
            and rule.is_fixable
            and (not rule.preview if not include_preview else True)
            and (
                rule.fix == FixAvailability.ALWAYS
                if not include_sometimes_fixable
                else True
            )
        }

    @staticmethod
    def output(rules: Iterable[Rule], md: MdUtils, output_path: Path):
        md.new_header(2, "Autofixable Ruff rules")
        md.new_line(
            f"{len(rules)} Ruff rules are violated in the repo, but can be auto-fixed 🪄"
        )
        output_table(
            items=rules,
            path=output_path / "autofixable.csv",
            md=md,
            collapsible=True,
        )
