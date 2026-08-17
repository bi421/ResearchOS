---
name: Feature / Bug Fix
about: Contribute a new feature or bug fix to ResearchOS
title: "[FEATURE/FIX] Brief description"
labels: ""
assignees: ""

---

## Description
<!-- Briefly describe what this PR does -->

## Type
- [ ] Feature (new capability)
- [ ] Bug Fix (resolves an issue)
- [ ] Documentation (docs only, no code changes)
- [ ] Test Coverage (tests only)
- [ ] Performance (optimization, no logic change)
- [ ] Refactoring (code improvement, no behavior change)

## Related Issues
<!-- Link to related issues: Closes #123, Related to #456 -->
Closes #

## Changes Made
<!-- List the main changes, organized by file/module -->

## Testing
<!-- Describe how this was tested -->
- [ ] Unit tests added/updated
- [ ] Coverage: (old)% → (new)%
- [ ] Tested locally with: `pytest researchos/tests/ -v`
- [ ] Coverage check: `pytest --cov=researchos --cov-fail-under=70`

## Architecture Compliance
<!-- Confirm this PR respects ResearchOS architecture -->
- [ ] No modifications to frozen core (identity, lifecycle, evidence, contracts)
- [ ] No trading/exchange code in researchos/ package
- [ ] No hardcoded secrets or credentials
- [ ] Tests use fixtures (tmp_path, :memory:) — no production database access
- [ ] Code follows PEP 8 and includes type hints

## Breaking Changes
<!-- Describe any breaking changes, or state "None" -->
- None

## Screenshots
<!-- If applicable, add screenshots showing the changes -->

## Additional Notes
<!-- Any other information reviewers should know -->

---

## PR Checklist
Before submitting, please ensure:

- [ ] Branch created from `develop` (not `master`)
- [ ] Conventional commit message used
- [ ] All tests pass locally: `pytest researchos/tests/ tests/unit/ -v`
- [ ] Coverage check passes: `pytest --cov=researchos --cov-fail-under=70`
- [ ] No hardcoded secrets (check with `grep -r "API_KEY\|SECRET"`)
- [ ] Documentation updated (if adding features)
- [ ] CHANGELOG.md entry added (for major features)

**Thank you for contributing to ResearchOS! 🙏**
