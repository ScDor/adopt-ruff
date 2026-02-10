"""Tests for category-level grouping functionality."""

import pytest

from adopt_ruff.models.rule import FixAvailability, Rule
from adopt_ruff.utils import (
    extract_category_prefix,
    find_complete_categories,
    generate_pyproject_suggestion,
)


class TestExtractCategoryPrefix:
    """Tests for extract_category_prefix function."""

    def test_simple_prefix(self):
        """Test extracting simple letter prefixes."""
        assert extract_category_prefix("B010") == "B"
        assert extract_category_prefix("C401") == "C"
        assert extract_category_prefix("E501") == "E"

    def test_multi_letter_prefix(self):
        """Test extracting multi-letter prefixes."""
        assert extract_category_prefix("RUF001") == "RUF"
        assert extract_category_prefix("ASYNC100") == "ASYNC"
        assert extract_category_prefix("PLW0127") == "PLW"

    def test_prefix_only(self):
        """Test when code is just a prefix."""
        assert extract_category_prefix("RUF") == "RUF"
        assert extract_category_prefix("B") == "B"


class TestFindCompleteCategories:
    """Tests for find_complete_categories function."""

    def create_rule(self, code: str, linter: str) -> Rule:
        """Helper to create a test rule."""
        return Rule(
            name=f"test-{code}",
            code=code,
            linter=linter,
            summary="Test rule",
            message_formats=(),
            fix=FixAvailability.ALWAYS,
            explanation="Test explanation",
            preview=False,
        )

    def test_complete_category(self):
        """Test detecting a complete category."""
        # Create all rules
        all_rules = {
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("RUF002", "Ruff-specific rules"),
            self.create_rule("RUF003", "Ruff-specific rules"),
            self.create_rule("B010", "flake8-bugbear"),
            self.create_rule("B011", "flake8-bugbear"),
        }

        # All RUF rules are in the situation
        situation_rules = [
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("RUF002", "Ruff-specific rules"),
            self.create_rule("RUF003", "Ruff-specific rules"),
        ]

        complete = find_complete_categories(situation_rules, all_rules)

        assert "RUF" in complete
        assert complete["RUF"] == ("Ruff-specific rules", 3)
        assert "B" not in complete  # Not all B rules are in situation

    def test_incomplete_category(self):
        """Test when category is not complete."""
        all_rules = {
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("RUF002", "Ruff-specific rules"),
            self.create_rule("RUF003", "Ruff-specific rules"),
        }

        # Only some RUF rules are in the situation
        situation_rules = [
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("RUF002", "Ruff-specific rules"),
        ]

        complete = find_complete_categories(situation_rules, all_rules)

        assert "RUF" not in complete  # Not all RUF rules are in situation

    def test_multiple_complete_categories(self):
        """Test detecting multiple complete categories."""
        all_rules = {
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("RUF002", "Ruff-specific rules"),
            self.create_rule("ASYNC100", "flake8-async"),
            self.create_rule("ASYNC101", "flake8-async"),
            self.create_rule("B010", "flake8-bugbear"),
        }

        situation_rules = [
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("RUF002", "Ruff-specific rules"),
            self.create_rule("ASYNC100", "flake8-async"),
            self.create_rule("ASYNC101", "flake8-async"),
        ]

        complete = find_complete_categories(situation_rules, all_rules)

        assert "RUF" in complete
        assert complete["RUF"] == ("Ruff-specific rules", 2)
        assert "ASYNC" in complete
        assert complete["ASYNC"] == ("flake8-async", 2)
        assert "B" not in complete

    def test_empty_situation(self):
        """Test with no rules in situation."""
        all_rules = {
            self.create_rule("RUF001", "Ruff-specific rules"),
            self.create_rule("B010", "flake8-bugbear"),
        }

        complete = find_complete_categories([], all_rules)

        assert len(complete) == 0

    def test_single_rule_category(self):
        """Test category with just one rule."""
        all_rules = {
            self.create_rule("X001", "single-rule-linter"),
            self.create_rule("B010", "flake8-bugbear"),
        }

        situation_rules = [
            self.create_rule("X001", "single-rule-linter"),
        ]

        complete = find_complete_categories(situation_rules, all_rules)

        assert "X" in complete
        assert complete["X"] == ("single-rule-linter", 1)


class TestGeneratePyprojectSuggestion:
    """Tests for generate_pyproject_suggestion function."""

    def test_single_category_select(self):
        """Test generating suggestion for a single category with select."""
        suggestion = generate_pyproject_suggestion(["RUF"], "select")
        assert "[tool.ruff.lint]" in suggestion
        assert 'select = ["RUF"]' in suggestion
        assert "```toml" in suggestion

    def test_multiple_categories_select(self):
        """Test generating suggestion for multiple categories."""
        suggestion = generate_pyproject_suggestion(["RUF", "ASYNC", "B"], "select")
        assert "[tool.ruff.lint]" in suggestion
        assert 'select = ["ASYNC", "B", "RUF"]' in suggestion  # Should be sorted

    def test_ignore_section(self):
        """Test generating suggestion with ignore section."""
        suggestion = generate_pyproject_suggestion(["RUF"], "ignore")
        assert "[tool.ruff.lint]" in suggestion
        assert 'ignore = ["RUF"]' in suggestion

    def test_empty_categories(self):
        """Test with empty category list."""
        suggestion = generate_pyproject_suggestion([], "select")
        assert suggestion == ""

    def test_categories_are_sorted(self):
        """Test that categories are sorted in output."""
        suggestion = generate_pyproject_suggestion(["Z", "A", "M"], "select")
        assert 'select = ["A", "M", "Z"]' in suggestion
