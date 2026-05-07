# LDlinkPy API Reference

This reference summarizes the public functions exported by `ldlinkpy`. It is intentionally concise; the longer examples in [examples.md](examples.md) show practical command-line usage.

Most endpoint functions accept an optional `token` argument. When `token=None`, `LDlinkPy` reads the token from the `LDLINK_TOKEN` environment variable.

## Common Parameters

| Parameter | Meaning |
| --- | --- |
| `token` | LDlink API token. If omitted or `None`, `LDLINK_TOKEN` is used. |
| `api_root` | Base LDlink REST API URL. Usually left as the default. |
| `genome_build` | Genome build, usually `grch37`, `grch38`, or `grch38_high_coverage`. |
| `pop` | One or more 1000 Genomes population codes, such as `CEU`, `YRI`, `EUR`, or `ALL`. |
| `r2d` | LD measure, usually `r2` or `d`. |
| `file` | Optional output path. When `False`, no file is written. |
| `return_type` | Output mode for functions that support it, usually `dataframe` or `raw`. |

## Common Returns

Most endpoint functions return a `pandas.DataFrame` by default. Functions that support raw output may return a string, dictionary, or list depending on the LDlink response. `ldproxy_batch` writes files and returns a list of file paths.

## Common Exceptions

`LDlinkPy` may raise:

- `TokenMissingError` or `ValueError` when no token is supplied and `LDLINK_TOKEN` is not set.
- `ValidationError` or `ValueError` for invalid variants, populations, genome builds, thresholds, or output options.
- `RuntimeError` or `APIError` for HTTP failures, LDlink API errors, or response parsing failures.

Exception classes and messages are still being standardized as part of package cleanup.

## Endpoint Functions

### `ldpair`

Query LD statistics for one variant pair or multiple variant pairs.

Signature:

```python
ldpair(var1=None, var2=None, snp_pairs=None, pop="CEU", genome_build="grch37", token=None, file=False, api_root=DEFAULT_API_ROOT, output="table", request_method="auto")
```

| Parameter | Description |
| --- | --- |
| `var1`, `var2` | Variant pair as rsIDs or chromosome coordinates. Used for a single-pair query. |
| `snp_pairs` | Optional collection of variant pairs for multi-pair queries. |
| `pop` | One or more population codes. |
| `genome_build` | Genome build to query. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `file` | Optional file path for output. |
| `api_root` | LDlink REST API root. |
| `output` | `table` for parsed tabular output or `text` for text output. |
| `request_method` | `auto`, `get`, or `post`. |

Returns: `pandas.DataFrame`, text, dictionary, or list depending on query mode and output mode.

### `ldmatrix`

Create an LD matrix for a set of variants.

Signature:

```python
ldmatrix(snps, pop="CEU", r2d="r2", genome_build="grch37", token=None, api_root=DEFAULT_API_ROOT, return_type="dataframe", request_method="auto", file=False)
```

| Parameter | Description |
| --- | --- |
| `snps` | Two or more variants as a string or sequence. |
| `pop` | One or more population codes. |
| `r2d` | LD measure, `r2` or `d`. |
| `genome_build` | Genome build to query. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `api_root` | LDlink REST API root. |
| `return_type` | `dataframe` or `raw`. |
| `request_method` | `auto`, `get`, or `post`. |
| `file` | Optional file path for output. |

Returns: `pandas.DataFrame` by default, or raw response content when `return_type="raw"`.

### `ldproxy`

Find proxy variants for a query variant.

Signature:

```python
ldproxy(snp, pop="CEU", r2d="r2", token=None, file=False, genome_build="grch37", win_size=500000, api_root=DEFAULT_API_ROOT, return_type="dataframe")
```

| Parameter | Description |
| --- | --- |
| `snp` | Query variant as an rsID or chromosome coordinate. |
| `pop` | One or more population codes. |
| `r2d` | LD measure, `r2` or `d`. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `file` | Optional file path for output. |
| `genome_build` | Genome build to query. |
| `win_size` | Window size in base pairs. |
| `api_root` | LDlink REST API root. |
| `return_type` | `dataframe` or `raw`. |

Returns: `pandas.DataFrame` by default, or raw text when `return_type="raw"`.

### `ldproxy_batch`

Run multiple LDproxy queries and write output files.

Signature:

```python
ldproxy_batch(snp, pop="CEU", r2d="r2", token=None, append=False, genome_build="grch37", win_size=500000, api_root=DEFAULT_API_ROOT)
```

| Parameter | Description |
| --- | --- |
| `snp` | Variants as a string, iterable, or pandas DataFrame. |
| `pop` | One or more population codes. |
| `r2d` | LD measure, `r2` or `d`. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `append` | If `True`, append all results to one combined file. |
| `genome_build` | Genome build to query. |
| `win_size` | Window size in base pairs. |
| `api_root` | LDlink REST API root. |

Returns: list of written file paths.

### `ldtrait`

Query trait associations linked to variants in LD.

Signature:

```python
ldtrait(snps, pop="CEU", r2d="r2", r2d_threshold=0.1, win_size=500000, genome_build="grch37", token=None, api_root=DEFAULT_API_ROOT, return_type="dataframe", request_method="auto", timeout=600.0, *, file=False, on_no_hits="empty")
```

| Parameter | Description |
| --- | --- |
| `snps` | One or more variants. |
| `pop` | One or more population codes. |
| `r2d` | LD measure, `r2` or `d`. |
| `r2d_threshold` | LD threshold. |
| `win_size` | Window size in base pairs. |
| `genome_build` | Genome build to query. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `api_root` | LDlink REST API root. |
| `return_type` | `dataframe` or `raw`. |
| `request_method` | `auto`, `get`, or `post`. |
| `timeout` | Request timeout in seconds. |
| `file` | Optional file path for output. |
| `on_no_hits` | `empty` to return an empty DataFrame, or `raise` to raise on no-hit responses. |

Returns: `pandas.DataFrame` by default, or raw response content when requested.

### `ldexpress`

Query GTEx expression associations for variants in LD.

Signature:

```python
ldexpress(snps, pop="CEU", tissue="ALL", r2d="r2", r2d_threshold=0.1, p_threshold=0.1, win_size=500000, genome_build="grch37", token=None, file=False, api_root=DEFAULT_API_ROOT, on_no_hits="empty")
```

| Parameter | Description |
| --- | --- |
| `snps` | One or more variants. |
| `pop` | One or more population codes. |
| `tissue` | GTEx tissue name, abbreviation, or `ALL`. |
| `r2d` | LD measure, `r2` or `d`. |
| `r2d_threshold` | LD threshold. |
| `p_threshold` | P-value threshold. |
| `win_size` | Window size in base pairs. |
| `genome_build` | Genome build to query. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `file` | Optional file path for output. |
| `api_root` | LDlink REST API root. |
| `on_no_hits` | `empty` to return an empty DataFrame, or `raise` to raise on no-hit responses. |

Returns: `pandas.DataFrame`.

### `ldhap`

Query haplotype and variant tables for a variant set.

Signature:

```python
ldhap(snps, pop="CEU", token=None, table_type="haplotype", genome_build="grch37", api_root=DEFAULT_API_ROOT)
```

| Parameter | Description |
| --- | --- |
| `snps` | One or more variants. |
| `pop` | One or more population codes. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `table_type` | Output table type, such as `haplotype`, `variant`, `both`, or `merged`. |
| `genome_build` | Genome build to query. |
| `api_root` | LDlink REST API root. |

Returns: `pandas.DataFrame` for most table types, or a dictionary-like result for `table_type="both"`.

### `ldpop`

Query LD statistics across populations for two variants.

Signature:

```python
ldpop(var1, var2, pop="CEU", r2d="r2", token=None, file=False, genome_build="grch37", api_root=DEFAULT_API_ROOT)
```

| Parameter | Description |
| --- | --- |
| `var1`, `var2` | Query variants as rsIDs or chromosome coordinates. |
| `pop` | One or more population codes. |
| `r2d` | LD measure, `r2` or `d`. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `file` | Optional file path for output. |
| `genome_build` | Genome build to query. |
| `api_root` | LDlink REST API root. |

Returns: `pandas.DataFrame`.

### `snpclip`

Prune variants by LD and minor allele frequency thresholds.

Signature:

```python
snpclip(snps, pop="CEU", r2_threshold=0.1, maf_threshold=0.01, genome_build="grch37", token=None, file=False, api_root=DEFAULT_API_ROOT, return_type="dataframe")
```

| Parameter | Description |
| --- | --- |
| `snps` | One or more variants. |
| `pop` | One or more population codes. |
| `r2_threshold` | R2 pruning threshold. |
| `maf_threshold` | Minor allele frequency threshold. |
| `genome_build` | Genome build to query. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `file` | Optional file path for output. |
| `api_root` | LDlink REST API root. |
| `return_type` | `dataframe` or `raw`. |

Returns: `pandas.DataFrame` by default, or raw text when `return_type="raw"`.

### `snpchip`

Identify genotyping arrays containing variants.

Signature:

```python
snpchip(snps, chip="ALL", genome_build="grch37", token=None, api_root=DEFAULT_API_ROOT, return_type="dataframe")
```

| Parameter | Description |
| --- | --- |
| `snps` | One or more variants. |
| `chip` | Chip/platform code or collection of codes. |
| `genome_build` | Genome build to query. |
| `token` | LDlink token or `None` to use `LDLINK_TOKEN`. |
| `api_root` | LDlink REST API root. |
| `return_type` | `dataframe` or `raw`. |

Returns: `pandas.DataFrame` by default, or raw text when `return_type="raw"`.

## Lookup Helpers

### `list_pop()`

Return available 1000 Genomes population codes and labels.

Returns: `pandas.DataFrame`.

### `list_chips()` / `list_chip_platforms()`

Return available genotyping chip/platform codes and labels. `list_chips()` is an alias for `list_chip_platforms()`.

Returns: `pandas.DataFrame`.

### `list_gtex_tissues()`

Return GTEx tissue names and LDexpress tissue codes.

Returns: `pandas.DataFrame`.
