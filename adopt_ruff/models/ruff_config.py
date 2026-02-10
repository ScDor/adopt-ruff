import tomllib
from pathlib import Path

from pydantic import BaseModel

from adopt_ruff.models.rule import Rule
from adopt_ruff.utils import logger

MIN_RULE_CODE_LEN = 4
DEFAULT_SELECT_RULES = ("E", "F")


class RawRuffConfig(BaseModel):
    selected_codes: set[str]
    ignored_codes: set[str]

    @classmethod
    def read_toml(cls, path: Path) -> "RawRuffConfig":
        try:
            toml = tomllib.loads(path.read_text())
        except ValueError as e:
            raise ValueError(f"make sure that {path.name} is a valid toml") from e

        match path.name:
            case "pyproject.toml":
                if (ruff_section := toml.get("tool", {}).get("ruff")) is None:
                    logger.warning(
                        f"could not find `tool` or `tool.ruff` in {path.name}, using default"
                    )
                    return cls.default_config()

            case "ruff.toml" | ".ruff.toml":
                ruff_section = toml
            case _:
                raise ValueError(
                    f"config file must be pyproject.toml, ruff.toml or .ruff.toml, got {path.name}"
                )

        ruff_lint_section = ruff_section.get(
            "lint", ruff_section
        )  # both are valid, `lint` was added at some point

        raw_select_codes = set(ruff_lint_section.get("select", ()))
        raw_ignored_codes = set(ruff_lint_section.get("ignore", ()))

        logger.debug(f"{len(raw_select_codes)=}, {len(raw_ignored_codes)=}")
        return RawRuffConfig(
            selected_codes=raw_select_codes,
            ignored_codes=raw_ignored_codes,
        )

    @classmethod
    def default_config(cls) -> "RawRuffConfig":
        return RawRuffConfig(
            selected_codes=set(DEFAULT_SELECT_RULES),
            ignored_codes=set(),
        )


class RuffConfig(BaseModel):
    selected_rules: set[Rule]
    ignored_rules: set[Rule]

    @staticmethod
    def from_file(path: Path | None, rules: set[Rule]) -> "RuffConfig":
        if path:
            logger.debug(f"reading ruff config file from {path!s}")
            raw_config = RawRuffConfig.read_toml(path)
        else:
            logger.warning(
                f"Config path was not specified, using default={DEFAULT_SELECT_RULES}"
            )
            raw_config = RawRuffConfig.default_config()

        return RuffConfig(
            selected_rules=_parse_raw_rules(raw_config.selected_codes, rules),
            ignored_rules=_parse_raw_rules(raw_config.ignored_codes, rules),
        )

    @property
    def all_rules(self) -> set[Rule]:
        return self.selected_rules | self.ignored_rules


def _parse_raw_rules(raw_codes: set[str], rules: set[Rule]) -> set[Rule]:
    """Convert code values (E401), categories (E) and ALL, into Rule objects."""
    if "ALL" in raw_codes:
        return rules

    code_to_rule = {rule.code: rule for rule in rules}

    result: set[Rule] = set()

    for code in raw_codes:
        if code.isalpha() or len(code) < MIN_RULE_CODE_LEN:
            code_rules = tuple(
                rule for rule in rules if rule.code.removeprefix(code).isnumeric()
            )
            logger.debug(
                f"assuming {code} is a category, adding {len(code_rules)} rules: {sorted(r.code for r in code_rules)!s}"
            )
            result.update(code_rules)
            # TODO are there cases of category names with len>=MIN_RULE_CODE_LEN, mixing alpha&digits?
        else:
            result.add(code_to_rule[code])

    logger.debug(f"converted {len(raw_codes)} raw codes into {len(result)} rules")

    return result
