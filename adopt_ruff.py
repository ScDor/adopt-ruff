import json
from pathlib import Path

from mdutils.mdutils import MdUtils
from pydantic import BaseModel

from models.ruff_config import RuffConfig
from models.ruff_output import Violation
from models.rule import Rule
from suggestors import Autofixable, Respected

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
    repo_name: str = "dummy/repo",
) -> str:
    md = MdUtils("output")
    md.new_header(1, f"adopt-ruff report for {repo_name}")

    suggested = False

    for suggestor in (Respected, Autofixable):
        if suggested_rules := suggestor.relevant_rules(rules, violations, config):
            suggested = True
            suggestor.output(suggested_rules, md, ARTIFACTS_PATH)

    if not suggested:
        md.new_paragraph(
            "You adopted Ruff well! 👏\n",
            f"There are no Ruff rules I can suggest for {repo_name} at this time.",
        )
    return md.get_md_text()


if __name__ == "__main__":
    rules, violations, config = load()
    result = run(rules, violations, config)
    Path("result.md").write_text(result)
