# LDlinkPy Development and Release Checklist

This checklist tracks the remaining work to finish, document, release, and publish **LDlinkPy**.

## 1. Finish the package

- [x] Complete all planned endpoint functions
- [ ] Make public function names and arguments consistent
- [ ] Finalize input validation and exception messages
- [ ] Confirm sequential-only request behavior is enforced client-wide
  - [ ] Move `ldproxy` off per-instance `LDlinkClient` locking or otherwise confirm it shares the global request lock
- [ ] Standardize return types and output formatting
- [ ] Remove dead code, duplication, and temporary workarounds
- [ ] Verify package metadata and version number
- [x] Confirm license selection and `LICENSE` file

## 2. Testing

- [x] Add pytest coverage for every public function
- [ ] Mock all HTTP responses
  - [ ] Replace or isolate the real API smoke-style test in `tests/test_ldproxy_batch.py`
- [ ] Confirm tests never call the real LDlink API
- [x] Add tests for invalid inputs
- [x] Add tests for API error handling
- [x] Add tests for response parsing and returned objects
- [x] Run the full test suite in a fresh virtual environment
- [ ] Add GitHub Actions CI
- [ ] Recruit humans using Windows and macOS for testing

## 3. Documentation

- [x] Write a clear `README.md`
- [x] Add installation instructions
- [x] Add a quick start section
- [x] Document token setup with `LDLINK_TOKEN`
- [x] Document each public function and its parameters
- [x] Document return types and common exceptions
- [x] Add a parity note comparing LDlinkPy to LDlinkR where appropriate

## 4. Examples

- [ ] Create small example scripts or notebooks
- [x] Add at least one example for each major endpoint
- [x] Add one end-to-end workflow example
- [x] Keep examples simple, realistic, and reproducible
- [ ] Confirm examples are useful for biomedical research users

## 5. Packaging and distribution

- [ ] Build source and wheel distributions
- [ ] Test installation from built artifacts
- [ ] Publish to TestPyPI
- [ ] Publish to PyPI
- [ ] Prepare a conda-forge recipe
- [ ] Write release notes for the first public release

## 6. Project polish

- [ ] Add `CITATION.cff`
- [ ] Add a contributing guide
- [ ] Add issue templates
- [ ] Add a pull request template
- [ ] Move GitHub repository from personal account to senior PI account or organization
- [x] Add `official` remote and sync `main` to both GitHub remotes
- [ ] Tag a stable release

## 7. Visibility and adoption

- [ ] Request a link or announcement on the official LDlink website
- [x] Prepare a short project description for GitHub and PyPI
- [ ] Share with early users for testing and feedback

## 8. Review and publication

- [ ] Submit the package for pyOpenSci review
- [ ] Address reviewer comments
- [ ] Choose a target journal for the software paper
- [ ] Draft the manuscript
- [ ] Include a real-world use case
- [ ] Submit the paper

## Immediate next steps

- [x] Finish remaining package functions
- [ ] Finish tests
- [x] Write the README
- [x] Write examples
- [ ] Publish to PyPI

## Note

- Keep this checklist in the `repo root` since this is the only planning file.
- Move to **`docs/`** if it starts collecting multiple project notes, checklists, or publication planning files.
