# Contributing to ResearchOS

Thank you for your interest in contributing to ResearchOS! This guide explains how to contribute code, documentation, and features.

---

## Core Principles

ResearchOS is built on three core principles. **All contributions must align with these:**

1. **Determinism** — Every computation must be deterministic and reproducible
2. **Explainability** — Every conclusion must have complete reasoning and evidence
3. **Scientific Rigor** — Every hypothesis must be falsifiable and testable

**Non-Negotiable Rule:** ResearchOS never executes trades or sends orders to exchanges. Architecture guards enforce this.

---

## Development Workflow

### 1. Set Up Your Environment

```bash
# Clone the repository
git clone https://github.com/your-org/ResearchOS.git
cd ResearchOS

# Create a feature branch (NOT on master)
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
pip install pytest pytest-cov pytest-xdist
```

### 2. Code Style & Conventions

**Python:**
- Follow PEP 8
- Use type hints for public APIs
- Document public functions with docstrings
- Max line length: 100 characters for code, 80 for docstrings

**Example:**
```python
def deterministic_hash(data: dict) -> str:
    """
    Compute deterministic SHA-256 hash of data.
    
    Args:
        data: Dictionary to hash (must be JSON-serializable)
    
    Returns:
        SHA-256 hex digest
    
    Raises:
        TypeError: If data is not JSON-serializable
    
    Examples:
        >>> h1 = deterministic_hash({"x": 1})
        >>> h2 = deterministic_hash({"x": 1})
        >>> assert h1 == h2  # Deterministic
    """
    import json
    from hashlib import sha256
    payload = json.dumps(data, sort_keys=True)
    return sha256(payload.encode()).hexdigest()
```

### 3. Testing Requirements

**MANDATORY:** All code changes require tests.

```bash
# Run full test suite
pytest researchos/tests/ tests/unit/ -v --tb=short

# Run with coverage
pytest researchos/tests/ tests/unit/ --cov=researchos --cov-fail-under=70 --cov-report=html

# Run specific test file
pytest researchos/tests/test_your_feature.py -v

# Run with parallel workers (faster)
pytest researchos/tests/ tests/unit/ -n auto
```

**Coverage Requirements:**
- New code: Minimum 70% coverage
- Critical modules (evidence, core): 90%+ required
- Use `pytest --cov-report=html` to see uncovered lines

**Test Isolation:**
- Use `tmp_path` fixture for file I/O
- Use `:memory:` SQLite for database tests
- NEVER read from `researchos.db` in tests
- NEVER write to production directories

### 4. Architecture Compliance

**Frozen Core (DO NOT MODIFY):**

The following are immutable and protected by architecture guards. Do not modify without architectural review:

- `researchos/core/identity.py` — Deterministic hashing (v2.0)
- `researchos/core/lifecycle.py` — Object lifecycle validation
- `researchos/objects/` — Immutable contracts (Experiment, Run, Result)
- `researchos/evidence/` — Evidence Repository, Lineage Graph
- `researchos/experiments/runner.py` — Certified BaseExperimentRunner

**Modifiable Layers:**

- `researchos/quant_engine/` — Analytics modules (improve test coverage)
- `researchos/decision_engine/` — New features OK
- `researchos/data_engine/` — Add new data sources
- `researchos/intelligence/` — Add new analysis modules

**Strictly External:**

- Trading execution code MUST be in `monitoring/` package (outside `researchos/`)
- Exchange connection code MUST be in `monitoring/` or separate package
- No `ccxt`, `binance`, or trading APIs in core researchos imports

Verify with:
```bash
python -c "import ast; code = open('your_file.py').read(); tree = ast.parse(code); 
imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
assert 'ccxt' not in imports, 'ccxt import forbidden in core'"
```

### 5. Commit Message Format

Use **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `test` — Test improvements
- `refactor` — Code refactoring (no behavior change)
- `perf` — Performance improvement
- `chore` — Tooling, configuration, dependencies

**Examples:**
```
feat(quant_engine): add technical indicators for fibonacci retracements
fix(evidence): correct hash collision in lineage graph
docs(readme): update getting started guide
test(validation): add edge case tests for walk-forward splitter
```

### 6. Pull Request Process

1. **Create PR on `develop` branch (NOT `master`)**

   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub: feature/your-feature-name → develop
   ```

2. **Ensure CI/CD passes:**
   - ✅ Python tests (Python 3.10, 3.11, 3.12)
   - ✅ Security scan (no hardcoded secrets)
   - ✅ Coverage check (≥70%)
   - ✅ Lint check (PEP 8 warnings only)

3. **PR Description Template:**

   ```markdown
   ## Description
   Brief description of changes.
   
   ## Related Issues
   Closes #123
   
   ## Changes
   - List major changes
   - Organized by module
   
   ## Testing
   - Describe tests added
   - Coverage: X% → Y%
   
   ## Breaking Changes
   - None (or list if applicable)
   ```

4. **Code Review:**
   - Address feedback from reviewers
   - Push additional commits (do NOT force-push)
   - Wait for approval

5. **Merge:**
   - Squash commits on merge (keep history clean)
   - Delete feature branch after merge

---

## Coverage Targets by Module

Use this to understand where to focus new tests:

| Category | Module | Target | Current | Status |
|---|---|---|---|---|
| **Core** | identity, lifecycle, core | 95%+ | 100% | ✅ Excellent |
| **Evidence** | evidence/*, repository | 95%+ | 100% | ✅ Excellent |
| **Contracts** | objects/*, experiments | 95%+ | 98%+ | ✅ Excellent |
| **Orchestration** | decision_engine, orchestration, market_memory | 90%+ | 87-96% | ✅ Good |
| **Analytics** | quant_engine/technical, historical, econometrics | 80%+ | 70-95% | ⚠️ At-Risk |
| **Validation** | validation/rules, validators, walk_forward | 80%+ | 35-85% | 🔴 Critical |
| **Experimental** | portfolio, fundamental, probability | 70%+ | 14-40% | 🔴 Critical |

**Priority:** Fix 🔴 Critical modules before proposing new features.

---

## Common Tasks

### Add a New Quantitative Indicator

1. Create module: `researchos/quant_engine/technical/new_indicator.py`
2. Implement with full type hints
3. Add contract: `researchos/quant_engine/technical/contracts.py`
4. Create test: `researchos/tests/test_technical_new_indicator.py`
5. Aim for 90%+ coverage

### Add a New Data Source

1. Update `researchos/data_engine/loader.py` to register source
2. Implement loading logic in `researchos/data_engine/repository.py`
3. Add contract validation
4. Create test with mock data
5. Test with `pytest researchos/tests/test_data_loader.py -v`

### Fix a Coverage Gap

1. Open [docs/COVERAGE_REPORT.md](docs/COVERAGE_REPORT.md)
2. Identify module with gap
3. Run coverage for that module:
   ```bash
   pytest --cov=researchos.module --cov-report=html researchos/tests/test_module.py
   ```
4. Open `htmlcov/index.html`, find uncovered lines
5. Write tests to cover those lines
6. Verify improvement

### Improve Performance

1. Profile before/after:
   ```python
   import timeit
   time_before = timeit.timeit(lambda: old_function(), number=1000)
   time_after = timeit.timeit(lambda: new_function(), number=1000)
   ```
2. Document performance impact in PR
3. Ensure no correctness regressions
4. May bypass coverage checks if perf gain is significant

---

## Release Process

Handled by maintainers. For reference:

1. Ensure `develop` branch is stable
2. Create release PR: `release/v1.1.0` → `master`
3. Update RELEASE_NOTES.md and version.py
4. Merge to master with `--no-ff`
5. Tag release: `git tag -a v1.1.0`
6. Push tags: `git push --tags`
7. CI/CD automates publish to PyPI (when available)

---

## Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Open a GitHub Issue with:
  - Python version (`python --version`)
  - OS (`uname -a`)
  - Error traceback
  - Minimal reproducible example
- **Design Questions:** Start an Issue marked "discussion" before implementing

---

## Code of Conduct

ResearchOS is committed to scientific integrity and professional collaboration:

- Be respectful of others' work and ideas
- Focus feedback on code, not the person
- Assume good intent
- Report violations to maintainers

---

## Resources

- **Architecture Guide:** [docs/ARCHITECTURE_FREEZE_V2.md](docs/ARCHITECTURE_FREEZE_V2.md)
- **Test Baseline:** [docs/TEST_BASELINE.md](docs/TEST_BASELINE.md)
- **Coverage Report:** [docs/COVERAGE_REPORT.md](docs/COVERAGE_REPORT.md)
- **Phase Roadmap:** [docs/PHASE_4_ROADMAP.md](docs/PHASE_4_ROADMAP.md)

---

**Last Updated:** 2026-08-16  
**Version:** v1.0.0
