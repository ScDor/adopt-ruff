import tomllib
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from adopt_ruff.models.rule import Rule
from adopt_ruff.utils import logger

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
        logger.debug(f"reading ruff config file from {path!s}")
        raw = RawRuffConfig.from_path(path)
        rules = tuple(rules)
        return RuffConfig(
            selected_rules=_parse_raw_rules(raw.selected_codes, rules),
            ignored_rules=_parse_raw_rules(raw.ignored_codes, rules),
        )

    @property
    def all_rules(self) -> set[Rule]:
        return set(self.selected_rules + self.ignored_rules)


def _parse_raw_rules(codes: set[str], rules: tuple[Rule, ...]) -> tuple[Rule, ...]:
    """
    Convert code values (E401), categories (E) and ALL, into Rule objects
    """
    if "ALL" in codes:
        return rules

    code_to_rule = {rule.code: rule for rule in rules}
    result: list[Rule] = []

    for code in codes:
        if code.isalpha() or len(code) < MIN_RULE_CODE_LEN:
            code_rules = tuple(
                rule for rule in rules if rule.code.removeprefix(code).isnumeric()
            )
            logger.debug(
                f"assuming {code} is a category, adding {len(code_rules)} rules: {sorted(r.code for r in code_rules)!s}"
            )
            result.extend(code_rules)
            # TODO are there cases of category names with len>=MIN_RULE_CODE_LEN, mixing alpha&digits?
        else:
            result.append(code_to_rule[code])
    logger.debug(f"parsed {len(codes)} codes into {len(result)} rules")
    return tuple(result)
