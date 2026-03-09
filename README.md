### Project: LDlinkPython (in progress...)

### LDtrait notes

- **Recommended:** use `request_method="auto"` (POST). This is the default and is the most reliable.
- **Optional:** `request_method="get"` uses the `ldtraitget` endpoint. In some environments this may fail due to network/TLS issues. If you hit errors with GET, switch back to POST.

### Project: LDlinkPython (in progress...)

### LDtrait notes

- **Recommended:** use `request_method="auto"` (POST). This is the default and is the most reliable.
- **Optional:** `request_method="get"` uses the `ldtraitget` endpoint. In some environments this may fail due to network/TLS issues. If you hit errors with GET, switch back to POST.

### `ldhap` command-line examples (1–4)

Set your token once in your shell:

```bash
export LDLINK_TOKEN="YOUR_TOKEN_HERE"
```

1) Haplotype table (default):

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldhap; df=ldhap(snps=['rs3','rs4'], pop=['CEU','YRI'], table_type='haplotype', genome_build='grch37', token=None); print(df.head().to_string(index=False))"
```

2) Variant table:

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldhap; df=ldhap(snps=['rs3','rs4'], pop='CEU', table_type='variant', genome_build='grch38', token=None); print(df.head().to_string(index=False))"
```

3) Both tables:

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldhap; out=ldhap(snps=['rs3','rs4'], pop=['CEU','YRI'], table_type='both', genome_build='grch37', token=None); print('Variant table:'); print(out['variant'].head().to_string(index=False)); print(''); print('Haplotype table:'); print(out['haplotype'].head().to_string(index=False))"
```

4) Merged table:

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldhap; df=ldhap(snps=['rs3','rs4'], pop=['CEU','YRI'], table_type='merged', genome_build='grch37', token=None); print(df.head().to_string(index=False))"
```

```

Notes:

- `snps` supports 1–30 variants (rsID or chromosome coordinate like `chr7:24966446`).
- `pop` accepts a string or a list of valid 1000G population codes.
- `genome_build` supports `grch37`, `grch38`, and `grch38_high_coverage`.
- `table_type` supports `haplotype`, `variant`, `both`, and `merged`.

### `ldpop` command-line examples (1–4)

Set your token once in your shell:

```bash
export LDLINK_TOKEN="YOUR_TOKEN_HERE"
```

1) Quick test (defaults: `pop='CEU'`, `r2d='r2'`, `genome_build='grch37'`):

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldpop; df=ldpop(var1='rs3', var2='rs4', token=None); print(df.to_string(index=False))"
```

2) Multiple populations + D-prime output:

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldpop; df=ldpop(var1='rs3', var2='rs4', pop=['CEU','YRI','CHB'], r2d='d', token=None); print(df.to_string(index=False))"
```

3) Coordinate input + GRCh38 (using a variant present in 1000G):

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldpop; df=ldpop(var1='chr13:31872705', var2='rs4', pop='CEU', r2d='r2', genome_build='grch38', token=None); print(df.to_string(index=False))"
```

4) Save output to a TSV file:

```bash
PYTHONPATH=. python -c "from ldlinkpython import ldpop; ldpop(var1='rs3', var2='rs4', pop='CEU', token=None, file='tmp/ldpop_rs3_rs4.tsv'); print('saved tmp/ldpop_rs3_rs4.tsv')"
```

