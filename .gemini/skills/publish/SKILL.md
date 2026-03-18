---
name: publish
description: Bump version, build, test, and publish the sigmashake Python SDK to PyPI.
argument-hint: "<version> [--dry-run] [--skip-tests]"
allowed-tools: Bash(python3 *), Bash(pip *), Bash(git *), Bash(twine *), Bash(hatch *), Read, Edit, Glob, Grep
---

# Publish sigmashake Python SDK

Bump the version, run the full quality pipeline, build the distribution, and publish to PyPI.

## Input

`$ARGUMENTS` — Required: a semver version string (e.g., `0.2.0`, `1.0.0`). Optional flags: `--dry-run` (build but don't upload), `--skip-tests` (skip test suite).

If no version is provided, ask the user for one. Show the current version from `src/sigmashake/_version.py` for reference.

## Steps

### 1. Validate Version

1. Read `src/sigmashake/_version.py` to get the current version.
2. Parse the target version from `$ARGUMENTS`. It must be valid semver and strictly greater than the current version.
3. If invalid or not provided, stop and ask the user.

### 2. Run Tests (unless `--skip-tests`)

```bash
python3 -m pytest tests/ -v --tb=short 2>&1
```

If any tests fail, stop. Do NOT publish a broken package.

### 3. Bump Version

Update the version in **both** files (they must stay in sync):

1. `src/sigmashake/_version.py` — update `__version__ = "<new>"`
2. `pyproject.toml` — update `version = "<new>"`

Verify the two files agree after editing.

### 4. Build

```bash
python3 -m pip install --quiet --break-system-packages build twine 2>&1 | tail -3
rm -rf dist/
python3 -m build 2>&1
```

Verify the build produced files:
```bash
ls -la dist/
```

Expected: one `.tar.gz` (sdist) and one `.whl` (wheel).

### 5. Validate Distribution

```bash
python3 -m twine check dist/* 2>&1
```

If twine check fails, stop and report the issue.

### 6. Commit Version Bump

```bash
git add src/sigmashake/_version.py pyproject.toml
git commit -m "Release v<version>

Co-Authored-By: Gemini Opus 4.6 <noreply@anthropic.com>"
git tag "v<version>"
```

### 7. Publish (unless `--dry-run`)

```bash
python3 -m twine upload dist/* 2>&1
```

Auth requires one of:
- `TWINE_USERNAME` + `TWINE_PASSWORD` env vars
- `~/.pypirc` configured
- `TWINE_API_KEY` env var (for token auth, set username to `__token__`)

If `--dry-run` is set, skip upload and report what would be published.

### 8. Push

```bash
git push origin main --quiet
git push origin "v<version>" --quiet
```

### 9. Report

```
Published: sigmashake v<version>
  - PyPI: https://pypi.org/project/sigmashake/<version>/
  - Tag: v<version>
  - Files: <list dist files with sizes>
```

## Rules

- Never publish if tests fail (unless `--skip-tests`).
- Never publish if `twine check` fails.
- Version must be bumped in BOTH `_version.py` and `pyproject.toml`.
- Always tag the release commit.
- Never force push or skip hooks.
- If `--dry-run`, do everything except the actual `twine upload` and `git push`.
- If PyPI credentials are missing, stop and tell the user how to configure them.
