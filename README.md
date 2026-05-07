## LDlinkPy

Project status: Work in progress. Feedback and contributions are welcome.

### Calculating Linkage Disequilibrium in Human Populations of Interest

<p align="center">
  <a href="LICENSE.txt"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+"></a>
</p>

## Introduction

LDlink is an interactive suite of web-based tools for querying germline variants in human population groups of interest and generating linkage disequilibrium (LD) tables and plots. Population genotype data comes from Phase 3 (Version 5) of the 1000 Genomes Project, and variant RS numbers are indexed based on dbSNP 155.

`LDlinkPy` is a Python client for the LDlink REST API. It helps researchers query LDlink programmatically, work with results as pandas DataFrames, and build reproducible LD workflows from Python.

Internet access and a personal LDlink API token are required for API calls.

## Install

`LDlinkPy` is currently installed from GitHub and is not on PyPI yet. Using a virtual environment is recommended.

### Requirements

- Python 3.10 or newer

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install "https://github.com/timyers/ldlinkpy/archive/refs/heads/main.zip"
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install "https://github.com/timyers/ldlinkpy/archive/refs/heads/main.zip"
```

## Quick Start

### 1. Get And Set Your LDlink Token

Request a personal access token at <https://ldlink.nih.gov/apiaccess>. Once registered, your token will be emailed to you.

`LDlinkPy` reads your token from the `LDLINK_TOKEN` environment variable by default. You can also pass `token="your_token_here"` directly to endpoint functions.

macOS / Linux:

```bash
export LDLINK_TOKEN="your_token_here"
```

Windows PowerShell:

```powershell
$env:LDLINK_TOKEN="your_token_here"
```

### 2. Start Python

macOS / Linux:

```bash
./.venv/bin/python
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python
```

### 3. Import LDlinkPy

```python
from ldlinkpy import list_pop, list_chips, ldpair, ldproxy
```

### 4. Try A Simple Lookup

List available 1000 Genomes populations:

```python
list_pop()
```

<p align="center">
  <img src="docs/images/list_pop_example.png" alt="Example output for list_pop()" width="400">
</p>

List available genotyping SNP chips:

```python
list_chips()
```

### 5. Run A Simple Analysis

Check LD between two variants:

```python
ldpair("rs3", "rs4", pop="YRI")
```

<p align="center">
  <img src="docs/images/ldpair_example.png" alt="Example output for ldpair()" width="300">
</p>

Find proxy variants for a SNP:

```python
ldproxy("rs7412", pop="CEU")
```

## Public Functions

| Function | Purpose |
| --- | --- |
| `ldpair` | Query LD statistics for one or more variant pairs. |
| `ldmatrix` | Create an LD matrix for a set of variants. |
| `ldproxy` | Find proxy variants for a query variant. |
| `ldproxy_batch` | Run multiple LDproxy queries and write result files. |
| `ldtrait` | Query trait associations linked to variants in LD. |
| `ldexpress` | Query GTEx expression associations for variants in LD. |
| `ldhap` | Query haplotype and variant tables for a variant set. |
| `ldpop` | Query LD statistics across populations for two variants. |
| `snpclip` | Prune variants by LD and minor allele frequency thresholds. |
| `snpchip` | Identify genotyping arrays containing variants. |
| `list_pop` | Return available 1000 Genomes population codes. |
| `list_chips` / `list_chip_platforms` | Return available genotyping chip/platform codes. |
| `list_gtex_tissues` | Return GTEx tissue names and LDexpress tissue codes. |

Most endpoint functions return pandas DataFrames by default. Some functions support raw responses, file output, or endpoint-specific return shapes. See the API reference for details.

## More Documentation

- [API reference](docs/api_reference.md): public functions, parameters, return types, and common exceptions.
- [Longer usage examples](docs/examples.md): endpoint-by-endpoint command-line examples for local development and exploratory testing.

## Authorship

`LDlinkPy` was conceived and overseen by Timothy Myers and Mitchel Machiela, with code and documentation assistance from ChatGPT 5.2 Thinking (OpenAI) and Codex (OpenAI). Additional authors and contributors may be added as the project develops.

## Relationship To LDlinkR

`LDlinkPy` is intended to provide Python access to the major LDlink workflows familiar to LDlinkR users. Function names and behavior are generally aligned where practical, while using Python conventions such as pandas DataFrames and keyword arguments.

## Development Status

This package is still being prepared for broader review and release. The current focus is documentation, examples, packaging polish, and human testing before further endpoint behavior changes.
