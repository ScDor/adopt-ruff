import tomllib
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from adopt_ruff.models.rule import Rule

MIN_RULE_CODE_LEN = 4
DEFAULT_SELECT_RULES = ("E", "F")


class RawRuffConfig(BaseModel, frozen=True):
    selected_codes: set[str]
    ignored_codes: set[str]

    @classmethod
    def from_path(cls, path: Path) -> "RawRuffConfig":
        if not path.exists():
            raise FileNotFoundError(path)

        toml = tomllib.loads(path.read_text())
        match path.name:
            case "pyproject.toml":
                if (ruff := toml.get("tool", {}).get("ruff")) is None:
                    return cls.default_config()

            case "ruff.toml" | ".ruff.toml":
                ruff = toml
            case _:
                raise ValueError(
                    "config file must be pyproject.toml, ruff.toml or .ruff.toml"
                )

        config = ruff.get(
            "lint", ruff
        )  # both are valid, `lint` was added at some point

        return RawRuffConfig(
            selected_codes=set(config.get("select", ())),
            ignored_codes=set(config.get("ignore", ())),
        )

    @classmethod
    def default_config(cls) -> "RawRuffConfig":
        return RawRuffConfig(
            selected_codes=set(DEFAULT_SELECT_RULES),
            ignored_codes=set(),
        )


class RuffConfig(BaseModel, frozen=True):
    selected_rules: tuple[Rule, ...]
    ignored_rules: tuple[Rule, ...]

    @staticmethod
    def from_path(path: Path, rules: Iterable[Rule]) -> "RuffConfig":
        raw = RawRuffConfig.from_path(path)
        rules = tuple(rules)
        return RuffConfig(
            selected_rules=_parse_raw_rules(raw.selected_codes, rules),
            ignored_rules=_parse_raw_rules(raw.ignored_codes, rules),
        )

    @property
    def all_rules(self) -> set[Rule]:
        return set(self.selected_rules + self.ignored_rules)


def _parse_raw_rules(codes: Iterable[str], rules: tuple[Rule, ...]) -> tuple[Rule, ...]:
    """
    Convert code values (E401), categories (E) and ALL, into Rule objects
    """
    if "ALL" in codes:
        return rules

    code_to_rule = {rule.code: rule for rule in rules}
    result: list[Rule] = []

    for code in codes:
        if code.isalpha() or len(code) < MIN_RULE_CODE_LEN:
            # If it's a category name, add all rules
            result.extend(
                rule for rule in rules if rule.code.removeprefix(code).isnumeric()
            )  # TODO check
            # TODO handle cases of category names of len>=MIN_RULE_CODE_LEN, mixing alpha&digits.
        else:
            result.append(code_to_rule[code])
    return tuple(result)
