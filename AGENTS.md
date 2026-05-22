# LDlinkPy Agent Instructions

These instructions apply to the whole repository.

## Repository

- Work in the local repository at `/Users/myersta/PythonProjects/ldlinkpy`.
- Treat `LDLINKPY_CHECKLIST.md` as the active project plan.
- Preserve user changes. Do not revert or overwrite files you did not intentionally edit.
- Prefer small, focused changes with tests or checks appropriate to the risk.

## Git Remotes

- Keep both GitHub remotes in sync:
  - `origin`: `https://github.com/timyers/ldlinkpy.git`
  - `official`: `https://github.com/machiela-lab/LDlinkPy.git`
- After committing changes, push `main` to both remotes unless explicitly told otherwise:
  - `git push origin main`
  - `git push official main`
- When creating tags, push the tag to both remotes as well:
  - `git push origin <tag>`
  - `git push official <tag>`

## Version Updates

When updating the package version, update every tracked version-bearing file together:

- `pyproject.toml`
- `ldlinkpy/__init__.py`
- `CITATION.cff`

Then verify both runtime and installed package metadata report the same version:

```bash
.venv/bin/python -c "import ldlinkpy; print(ldlinkpy.__version__)"
.venv/bin/python -c "import importlib.metadata as m; print(m.version('ldlinkpy'))"
```

If needed, refresh the editable install metadata:

```bash
.venv/bin/python -m pip install -e . --no-deps
```

## Checks

Before committing code changes, run:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
```

For documentation-only or checklist-only changes, a focused review of the diff is usually enough.

## Release Checkpoints

- Create annotated tags for meaningful checkpoints.
- Do not create a version tag until the package metadata has been bumped to the same version.
- Use tag messages that summarize the checkpoint, for example:

```bash
git tag -a v0.4.4 -m "Release v0.4.4: Section 1 completion and shared request locking"
```

## Project Preferences

- Be cautious about public behavior changes now that the package is working.
- Prefer read-only audits before changing endpoint behavior, argument names, return types, or validation messages.
- Keep deferred, non-release-blocking ideas as plain bullets in the `Future to-do` section rather than checklist boxes.
