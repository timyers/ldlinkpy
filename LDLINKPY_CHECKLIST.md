# LDlinkPy Development and Release Checklist

This checklist tracks the remaining work to finish, document, release, and publish **LDlinkPy**.

## 1. Finish the package

- [ ] Complete all planned endpoint functions
- [ ] Make public function names and arguments consistent
- [ ] Finalize input validation and exception messages
- [ ] Confirm sequential-only request behavior is enforced client-wide
- [ ] Standardize return types and output formatting
- [ ] Remove dead code, duplication, and temporary workarounds
- [ ] Verify package metadata and version number
- [ ] Confirm license selection and `LICENSE` file

## 2. Testing

- [ ] Add pytest coverage for every public function
- [ ] Mock all HTTP responses
- [ ] Confirm tests never call the real LDlink API
- [ ] Add tests for invalid inputs
- [ ] Add tests for API error handling
- [ ] Add tests for response parsing and returned objects
- [ ] Run the full test suite in a fresh virtual environment
- [ ] Add GitHub Actions CI

## 3. Documentation

- [ ] Write a clear `README.md`
- [ ] Add installation instructions
- [ ] Add a quick start section
- [ ] Document token setup with `LDLINK_TOKEN`
- [ ] Document each public function and its parameters
- [ ] Document return types and common exceptions
- [ ] Add a parity note comparing LDlinkPy to LDlinkR where appropriate

## 4. Examples

- [ ] Create small example scripts or notebooks
- [ ] Add at least one example for each major endpoint
- [ ] Add one end-to-end workflow example
- [ ] Keep examples simple, realistic, and reproducible
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
- [ ] Tag a stable release

## 7. Visibility and adoption

- [ ] Request a link or announcement on the official LDlink website
- [ ] Prepare a short project description for GitHub and PyPI
- [ ] Share with early users for testing and feedback

## 8. Review and publication

- [ ] Submit the package for pyOpenSci review
- [ ] Address reviewer comments
- [ ] Choose a target journal for the software paper
- [ ] Draft the manuscript
- [ ] Include a real-world use case
- [ ] Submit the paper

## Immediate next steps

- [ ] Finish remaining package functions
- [ ] Finish tests
- [ ] Write the README
- [ ] Write examples
- [ ] Publish to PyPI

## Note

- Keep this checklist in the `repo root` since this is the only planning file.
- Move to **`docs/`** if it starts collecting multiple project notes, checklists, or publication planning files.


