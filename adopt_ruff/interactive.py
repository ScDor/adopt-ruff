"""Interactive mode for selecting and applying Ruff rules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import questionary
from questionary import Choice

from adopt_ruff.utils import logger

if TYPE_CHECKING:
    from adopt_ruff.models.rule import Rule


def run_interactive_mode(
    respected: list[Rule],
    autofixable: list[Rule],
    applicable: list[Rule],
    config_path: Path,
) -> None:
    """
    Run interactive mode to select rules and update config.

    Args:
        respected: Rules with 0 violations (safe to add)
        autofixable: Rules with violations that can be auto-fixed
        applicable: Rules with violations (sorted by count)
        config_path: Path to the ruff configuration file
    """
    # Check if running in an interactive terminal
    if not sys.stdin.isatty():
        logger.error(
            "Interactive mode requires a TTY (interactive terminal). "
            "Cannot run in non-interactive environments like CI/CD pipelines."
        )
        sys.exit(1)

    if not any((respected, autofixable, applicable)):
        logger.info("No rules to add! Your configuration is already comprehensive.")
        return

    logger.info("\n🎯 Interactive Mode - Select rules to add to your configuration\n")

    selected_rules: set[Rule] = set()

    # Present each category
    if respected:
        _select_from_category(
            rules=respected,
            category_name="Respected Rules",
            description=f"{len(respected)} rules with 0 violations - safe to add immediately 🚀",
            selected_rules=selected_rules,
        )

    if autofixable:
        _select_from_category(
            rules=autofixable,
            category_name="Autofixable Rules",
            description=f"{len(autofixable)} rules with violations that can be auto-fixed 🪄",
            selected_rules=selected_rules,
        )

    if applicable:
        _select_from_category(
            rules=applicable,
            category_name="Applicable Rules",
            description=f"{len(applicable)} rules with violations (will require manual fixes) 🔧",
            selected_rules=selected_rules,
        )

    if not selected_rules:
        logger.info("No rules selected. Exiting without changes.")
        return

    # Show preview and confirm
    _preview_and_apply(selected_rules, config_path)


def _select_from_category(
    rules: list[Rule],
    category_name: str,
    description: str,
    selected_rules: set[Rule],
) -> None:
    """
    Present a category of rules and let the user select which ones to add.

    Args:
        rules: List of rules in this category
        category_name: Name of the category
        description: Description text for the category
        selected_rules: Set to add selected rules to (modified in place)
    """
    # Ask if user wants to explore this category
    explore = questionary.confirm(
        f"\n{category_name}\n{description}\n\nWould you like to explore this category?",
        default=True,
    ).ask()

    if not explore:
        return

    # Offer quick options
    quick_action = questionary.select(
        f"\nHow would you like to proceed with {category_name}?",
        choices=[
            Choice("Select all rules in this category", value="all"),
            Choice("Choose specific rules", value="specific"),
            Choice("Skip this category", value="skip"),
        ],
    ).ask()

    if quick_action == "skip":
        return

    if quick_action == "all":
        selected_rules.update(rules)
        logger.info(f"✓ Added all {len(rules)} rules from {category_name}")
        return

    # Let user select specific rules
    choices = [
        Choice(
            title=f"{rule.code:8} - {rule.name:50} ({rule.linter})",
            value=rule,
            checked=False,
        )
        for rule in rules
    ]

    selected = questionary.checkbox(
        f"\nSelect rules from {category_name} (use space to select, enter to confirm):",
        choices=choices,
    ).ask()

    if selected:
        selected_rules.update(selected)
        logger.info(f"✓ Selected {len(selected)} rule(s) from {category_name}")


def _preview_and_apply(selected_rules: set[Rule], config_path: Path) -> None:
    """
    Show preview of changes and apply them to the config file.

    Args:
        selected_rules: Set of rules to add to configuration
        config_path: Path to the configuration file
    """
    logger.info(f"\n📋 Preview: {len(selected_rules)} rules will be added to your configuration\n")

    # Group rules by category for better display
    rule_codes = sorted(rule.code for rule in selected_rules)

    # Show in columns for readability
    for i in range(0, len(rule_codes), 5):
        logger.info("  " + ", ".join(rule_codes[i : i + 5]))

    # Confirm
    confirm = questionary.confirm(
        f"\nAdd these {len(selected_rules)} rules to {config_path.name}?",
        default=True,
    ).ask()

    if not confirm:
        logger.info("Cancelled. No changes made.")
        return

    # Apply changes
    _update_config_file(config_path, rule_codes)


def _update_config_file(config_path: Path, rule_codes: list[str]) -> None:
    """
    Update the ruff configuration file with selected rules.

    Args:
        config_path: Path to the configuration file
        rule_codes: List of rule codes to add
    """
    import tomllib

    content = config_path.read_text()
    config = tomllib.loads(content)

    # Determine the structure based on file type and get existing select list
    if config_path.name == "pyproject.toml":
        tool_section = config.get("tool", {})
        ruff_section = tool_section.get("ruff", {})
        lint_section = ruff_section.get("lint", ruff_section)
        existing_select = lint_section.get("select", [])
    else:  # ruff.toml or .ruff.toml
        lint_section = config.get("lint", config)
        existing_select = lint_section.get("select", [])

    # Add new rules (avoiding duplicates)
    existing_set = set(existing_select)
    new_rules = [code for code in rule_codes if code not in existing_set]

    if not new_rules:
        logger.warning("All selected rules are already in the configuration!")
        return

    # Update select list
    updated_select = sorted(set(existing_select + new_rules))

    # Build the new content
    _write_updated_toml(config_path, updated_select)


def _write_updated_toml(config_path: Path, updated_select: list[str]) -> None:
    """
    Write the updated configuration back to the TOML file.

    This function manually updates the select list while preserving
    the rest of the file's formatting and structure.

    Args:
        config_path: Path to the configuration file
        updated_select: Updated list of selected rules
    """
    content = config_path.read_text()
    lines = content.splitlines(keepends=True)

    # Find the select line
    in_ruff_section = False
    in_lint_section = False
    select_line_idx = None

    for i, line in enumerate(lines):
        # Track sections
        if config_path.name == "pyproject.toml":
            if "[tool.ruff.lint]" in line or "[tool.ruff]" in line:
                in_ruff_section = True
            elif line.startswith("[") and "tool.ruff" not in line:
                in_ruff_section = False
        else:
            if "[lint]" in line:
                in_lint_section = True
            elif line.startswith("["):
                in_lint_section = False
                in_ruff_section = False

        # Find select line in the right section
        if (in_ruff_section or in_lint_section) and "select" in line and "=" in line:
            select_line_idx = i
            break

    # Format the new select list
    select_str = '["' + '", "'.join(updated_select) + '"]'

    if select_line_idx is not None:
        # Replace existing select line
        indent = len(lines[select_line_idx]) - len(lines[select_line_idx].lstrip())
        lines[select_line_idx] = " " * indent + f"select = {select_str}\n"
    else:
        # Add select line to the appropriate section
        # Find where to insert (after [tool.ruff.lint] or [lint] section header)
        insert_idx = None
        for i, line in enumerate(lines):
            if config_path.name == "pyproject.toml":
                if "[tool.ruff.lint]" in line:
                    insert_idx = i + 1
                    break
                elif "[tool.ruff]" in line and "[tool.ruff.lint]" not in content:
                    # Insert into [tool.ruff] if [tool.ruff.lint] doesn't exist
                    insert_idx = i + 1
                    break
            else:
                if "[lint]" in line or (i == 0 and not line.startswith("[")):
                    insert_idx = i + 1
                    break

        if insert_idx is not None:
            lines.insert(insert_idx, f"select = {select_str}\n")
        else:
            # Append to end of file
            lines.append(f"\nselect = {select_str}\n")

    # Write back
    config_path.write_text("".join(lines))
    logger.info(f"✅ Successfully updated {config_path.name} with {len(updated_select)} rules!")
