---
name: adopt-ruff
description: Use when you want to expand Ruff rule coverage in a Python repository using adopt-ruff suggestions.
---

# Adopt-Ruff

## Overview
"Ruffness" is the measure of how comprehensively a Python project utilizes [Ruff](https://ruff.rs) for linting and formatting. Increasing ruffness means systematically adopting more rules to catch bugs, enforce style, and improve maintainability.

## When to Use
- You want to increase the linting strictness of a Python repository.
- You are using `adopt-ruff` to find configuration gaps.
- You need a structured way to migrate from other linters (flake8, pylint) to Ruff.

## Core Workflow

### 1. Baseline Analysis
Run `adopt-ruff` to see your current status:
```bash
adopt-ruff --path . --repo-name <your-repo>
```
Review the generated `result.md` or Job Summary.

### 2. The "Zero-Effort" Phase (Respected Rules)
Start with rules your codebase already obeys.
- **Identify:** Look at the "Respected Ruff rules" table.
- **Execute:** Add these codes to the `lint.extend-select` (or `select`) list in `pyproject.toml`.
- **Verification:** Run `ruff check .` to ensure zero violations.

### 3. The "Automated" Phase (Autofixable Rules)
Adopt rules that Ruff can fix for you.
- **Identify:** Look at the "Autofixable Ruff rules" table.
- **Batching:** Select 1-5 rules at a time.
- **Execute:** 
  1. Add rules to configuration.
  2. Run `ruff check . --fix`.
  3. Verify changes.
- **Commit:** Use a descriptive commit like `style: apply ruff autofixes for [RULE_CODES]`.

### 4. The "Incremental" Phase (Applicable Rules)
Handle rules requiring manual intervention, prioritized by least resistance.
- **Identify:** Look at "Applicable Rules" (sorted by ascending violation count).
- **Execute:** Start with rules having 1-5 violations. Fix them manually and enable the rule.
- **Refinement:** For rules with hundreds of violations, consider if the rule is appropriate for your project before attempting a mass fix.

## Common Mistakes
- **Bulk Enabling:** Enabling 50+ rules at once often leads to "fix fatigue" and abandoned PRs.
- **Config Noise:** Forgetting to remove old linter configs (flake8, isort) after adopting their Ruff equivalents.
- **Ignoring Previews:** Not using the `--preview` flag to see upcoming rules that might benefit the project early.

## Common Rationalizations
| Excuse | Reality |
|--------|---------|
| "I'll fix all 200 violations manually" | You'll likely burn out or introduce bugs. Use the incremental approach. |
| "Respected rules aren't important" | They prevent future regressions and keep the codebase consistent. |
| "I don't need adopt-ruff, I'll just use 'ALL'" | 'ALL' includes conflicting or non-idiomatic rules. `adopt-ruff` helps you select what fits your repo. |

## Red Flags
- PRs containing both Ruff configuration changes AND unrelated feature logic.
- Massive commits labeled "ruff: fix everything".
- Enabling a rule then adding dozens of `# noqa` comments instead of fixing the code.

## Quick Reference Table
| Rule Category | Priority | Tooling | Effort |
|---------------|----------|---------|--------|
| Respected | High | `adopt-ruff` | ⚡ Trivial |
| Autofixable | Medium | `ruff --fix` | 🪄 Low |
| Low Violation | Low | Manual | 🔎 Moderate |
| High Violation | Evaluate | Manual/Scripted | 🛠️ High |
