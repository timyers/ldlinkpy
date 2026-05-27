# LDlinkPy Development and Release Checklist

This checklist tracks the remaining work to finish, document, release, and publish **LDlinkPy**.

## 1. Finish the package

- [x] Complete all planned endpoint functions
- [x] Confirm sequential-only request behavior is enforced client-wide
  - [x] Move `ldproxy` off per-instance `LDlinkClient` locking or otherwise confirm it shares the global request lock
- [x] Verify package metadata and version number
- [x] Confirm license selection and `LICENSE` file

## 2. Testing

- [x] Add pytest coverage for every public function
- [x] Mock all HTTP responses
  - [x] Replace or isolate the real API smoke-style test in `tests/test_ldproxy_batch.py`
- [x] Confirm tests never call the real LDlink API
- [x] Add tests for invalid inputs
- [x] Add tests for API error handling
- [x] Add tests for response parsing and returned objects
- [x] Run the full test suite in a fresh virtual environment
- [x] Add GitHub Actions CI
- [x] Add Windows/macOS CI matrix
- [x] Add Ruff linting gradually
  - [x] Fix duplicate, unused, and unsorted imports
  - [x] Review and fix low-risk Ruff style findings
  - [x] Decide which Ruff rules to enforce before release
  - [x] Run Ruff locally with no remaining enforced findings
  - [x] Add Ruff lint checks to GitHub Actions CI

## 3. Documentation

- [x] Write a clear `README.md`
- [x] Add installation instructions
- [x] Add a quick start section
- [x] Document token setup with `LDLINK_TOKEN`
- [x] Document each public function and its parameters
- [x] Document return types and common exceptions
- [x] Add a parity note comparing LDlinkPy to LDlinkR where appropriate

## 4. Examples

- [x] Create small example scripts or notebooks
- [x] Add at least one example for each major endpoint
- [x] Add one end-to-end workflow example
- [x] Keep examples simple, realistic, and reproducible
- [x] Confirm examples are useful for biomedical research users

## 5. Packaging and distribution

- [x] Build source and wheel distributions
- [x] Test installation from built artifacts
- [x] Publish to TestPyPI
- [ ] Publish to PyPI
- [x] Write release notes for the first public release

## 6. Project polish

- [x] Add `CITATION.cff`
- [x] Move GitHub repository from personal account to senior PI account or organization
- [x] Add `official` remote and sync `main` to both GitHub remotes
- [ ] Tag a stable release

## 7. Visibility and adoption

- [ ] Request a link or announcement on the official LDlink website
- [x] Prepare a short project description for GitHub and PyPI
- [ ] Share with early users for testing and feedback

## 8. Review and publication

- [x] Update the `CITATION.cff`
- [ ] Submit the package for pyOpenSci review
- [ ] Address reviewer comments
- [ ] Choose a target journal for the software paper
- [ ] Draft the manuscript
- [x] Include a real-world use case
- [ ] Submit the paper

## Immediate next steps

- [x] Finish remaining package functions
- [x] Finish tests
- [x] Write the README
- [x] Write examples
- [ ] Publish to PyPI

## Future to-do

- Prepare a conda-forge recipe after the PyPI release is stable and there is user demand
- Review public function names and arguments for consistency after the first release
- Refine input validation and exception messages after the first release
- Standardize return types and output formatting after the first release
- Remove dead code, duplication, and temporary workarounds after the first release
- Add a contributing guide if outside contribution volume increases
- Add issue templates if outside contribution volume increases
- Add a pull request template if outside contribution volume increases

## Note

- Keep this checklist in the `repo root` since this is the only planning file.
- Move to **`docs/`** if it starts collecting multiple project notes, checklists, or publication planning files.
