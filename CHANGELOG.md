# Changelog

## 0.4.5 - 2026-05-27

First public release candidate for PyPI.

- Publish-ready package metadata, README, citation metadata, and project links.
- Public Python interface for LDpair, LDproxy, LDproxy_batch, LDtrait, LDmatrix, LDexpress, LDhap, LDpop, SNPclip, SNPchip, and lookup helpers.
- Packaged local lookup tables for populations, GTEx tissues, and SNP chip platforms.
- Mocked pytest coverage for public functions, validation, parsing, and API error handling.
- GitHub Actions CI with Ruff linting and Python checks across Linux, macOS, and Windows.
- End-to-end biomedical workflow example for population-specific LD and haplotype feasibility around the Ewing sarcoma 6p25.1/RREB1 susceptibility locus.
- TestPyPI upload and clean install-back smoke test verified before the real PyPI release.
