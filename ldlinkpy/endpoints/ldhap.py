# ldlinkpy/endpoints/ldhap.py
# Codex implementation

from __future__ import annotations

import re
from io import StringIO
from typing import Sequence

import pandas as pd

from ldlinkpy import DEFAULT_API_ROOT
from ldlinkpy.exceptions import ParseError, ValidationError
from ldlinkpy.http import request as http_request
from ldlinkpy.validators import ensure_token

_AVAIL_POP: set[str] = {
    "YRI",
    "LWK",
    "GWD",
    "MSL",
    "ESN",
    "ASW",
    "ACB",
    "MXL",
    "PUR",
    "CLM",
    "PEL",
    "CHB",
    "JPT",
    "CHS",
    "CDX",
    "KHV",
    "CEU",
    "TSI",
    "FIN",
    "GBR",
    "IBS",
    "GIH",
    "PJL",
    "BEB",
    "STU",
    "ITU",
    "ALL",
    "AFR",
    "AMR",
    "EAS",
    "EUR",
    "SAS",
}

_AVAIL_TABLE_TYPE = {"haplotype", "variant", "both", "merged"}
_AVAIL_GENOME_BUILD = {"grch37", "grch38", "grch38_high_coverage"}

_RSID_RE = re.compile(r"^rs\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)


def _to_list(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _normalize_snps(snps: str | Sequence[str]) -> list[str]:
    vals = [str(s).strip() for s in _to_list(snps) if str(s).strip()]
    if not (1 <= len(vals) <= 30):
        raise ValidationError("Input is between 1 to 30 variants only.")
    for v in vals:
        if not (_RSID_RE.match(v) or _CHR_COORD_RE.match(v)):
            raise ValidationError(f"Invalid query format for variant: {v}.")
    return vals


def _normalize_pop(pop: str | Sequence[str]) -> str:
    vals = [str(p).strip() for p in _to_list(pop) if str(p).strip()]
    if not vals:
        raise ValidationError("Not a valid population code.")

    vals = [v.upper() for v in vals]
    if not all(v in _AVAIL_POP for v in vals):
        raise ValidationError("Not a valid population code.")
    return "+".join(vals)


def _normalize_table_type(table_type: str) -> str:
    v = str(table_type).strip().lower()
    if v not in _AVAIL_TABLE_TYPE:
        raise ValidationError("Not a valid option for table_type.")
    return v


def _normalize_genome_build(genome_build: str) -> str:
    v = str(genome_build).strip().lower()
    if v not in _AVAIL_GENOME_BUILD:
        raise ValidationError("Not an available genome build.")
    return v




class LDhapBothResult(dict):
    """Container for table_type='both' output with a convenient .head() helper."""

    @property
    def variant(self) -> pd.DataFrame:
        return self["variant"]

    @property
    def haplotype(self) -> pd.DataFrame:
        return self["haplotype"]

    def head(self, n: int = 5) -> dict[str, pd.DataFrame]:
        return {
            "variant": self["variant"].head(n),
            "haplotype": self["haplotype"].head(n),
        }

def _df_merge(data_out: pd.DataFrame, table_type: str, genome_build: str):
    if data_out.empty:
        raise ParseError("LDhap returned an empty response.")

    first_col = data_out.iloc[:, 0].astype(str)
    marker_idx = None
    for i, val in enumerate(first_col.tolist()):
        if val.startswith("#"):
            marker_idx = i
            break

    if marker_idx is None:
        raise ParseError("Unable to locate haplotype section separator in LDhap response.")

    num_of_snps = marker_idx
    data_out_var = data_out.iloc[:num_of_snps, :].copy()

    data_out2 = data_out.iloc[num_of_snps + 1 :, :].copy()
    if data_out2.empty:
        raise ParseError("LDhap response missing haplotype table section.")

    data_out2.columns = [str(x) for x in data_out2.iloc[0].tolist()]
    data_out2 = data_out2.iloc[1:, :].reset_index(drop=True)

    if num_of_snps == 1:
        data_out_hap = data_out2.copy()
        rs_col = "RS_Number" if "RS_Number" in data_out_var.columns else data_out_var.columns[0]
        data_out_hap = data_out_hap.rename(columns={data_out_hap.columns[0]: str(data_out_var.iloc[0][rs_col])})
    else:
        if "Haplotype" not in data_out2.columns:
            raise ParseError("LDhap response missing expected 'Haplotype' column.")
        split_cols = data_out2["Haplotype"].astype(str).str.split("_", expand=True)
        data_out_hap = pd.concat([split_cols, data_out2.iloc[:, 1:3].reset_index(drop=True)], axis=1)

        rs_col = "RS_Number" if "RS_Number" in data_out_var.columns else data_out_var.columns[0]
        rs_names = [str(x) for x in data_out_var[rs_col].tolist()]
        renamed = list(data_out_hap.columns)
        for idx in range(min(num_of_snps, len(renamed), len(rs_names))):
            renamed[idx] = rs_names[idx]
        data_out_hap.columns = renamed

    data_out_var.columns = [
        re.sub(r"Position[^<>]+", f"Position_{genome_build}", c) for c in data_out_var.columns.astype(str)
    ]
    data_out_var.columns = [re.sub(r"Allele[^<>]+", "Allele_Frequency", c) for c in data_out_var.columns.astype(str)]

    if table_type == "variant":
        return data_out_var.reset_index(drop=True)
    if table_type == "haplotype":
        return data_out_hap.reset_index(drop=True)
    if table_type == "both":
        return LDhapBothResult(
            variant=data_out_var.reset_index(drop=True),
            haplotype=data_out_hap.reset_index(drop=True),
        )

    data_out_hap_t = data_out_hap.transpose().copy()
    hap_cols = [f"H{i + 1}" for i in range(data_out_hap_t.shape[1])]
    data_out_hap_t.columns = hap_cols

    left = data_out_var.reset_index(drop=True)
    right = data_out_hap_t.iloc[:num_of_snps, :].reset_index(drop=True)
    df_all = pd.concat([left, right], axis=1)
    if df_all.shape[1] >= 4:
        cols = list(df_all.columns)
        cols[3] = "Haplotypes"
        df_all.columns = cols

    df1 = data_out_hap_t.iloc[num_of_snps:, :].copy()
    new_index = []
    for idx in df1.index.astype(str):
        if idx == "Count":
            new_index.append("Haplotype_Count")
        elif idx == "Frequency":
            new_index.append("Haplotype_Frequency")
        else:
            new_index.append(idx)
    df1.index = new_index
    df1 = df1.reset_index().rename(columns={"index": "Metric"})

    df2 = pd.DataFrame("   ", index=range(df1.shape[0]), columns=["Spacer1", "Spacer2"])
    df3 = pd.concat([df2, df1], axis=1)

    # Mirror LDlinkR positional column stacking semantics used by:
    #   data.frame(mapply(c, df_all, df3))
    # i.e., stack column i from df_all with column i from df3 regardless of labels.
    if df3.shape[1] != df_all.shape[1]:
        if df3.shape[1] < df_all.shape[1]:
            for i in range(df3.shape[1], df_all.shape[1]):
                df3[f"pad_{i}"] = ""
        else:
            df3 = df3.iloc[:, : df_all.shape[1]]

    stacked_cols = {}
    for i, col_name in enumerate(df_all.columns):
        stacked_cols[col_name] = pd.concat(
            [df_all.iloc[:, i], df3.iloc[:, i]],
            ignore_index=True,
        )
    data_out_merged = pd.DataFrame(stacked_cols)
    if data_out_merged.shape[1] >= 5:
        cols = list(data_out_merged.columns)
        for i in range(4, len(cols)):
            cols[i] = "  "
        data_out_merged.columns = cols

    return data_out_merged


def ldhap(
    snps: str | Sequence[str],
    pop: str | Sequence[str] = "CEU",
    token: str | None = None,
    table_type: str = "haplotype",
    genome_build: str = "grch37",
    api_root: str = DEFAULT_API_ROOT,
):
    """
    Query LDhap from the NIH LDlink REST API.

    Parameters
    ----------
    snps
        List of 1-30 variants (rsIDs or chr coordinates like "chr7:24966446").
    pop
        One or more 1000G population codes, default "CEU".
    token
        LDlink API token.
    table_type
        One of: "haplotype", "variant", "both", "merged".
    genome_build
        One of: "grch37", "grch38", "grch38_high_coverage".
    api_root
        Base API root URL.

    Returns
    -------
    pandas.DataFrame or LDhapBothResult
    """
    snp_list = _normalize_snps(snps)
    pop_norm = _normalize_pop(pop)
    table_type_norm = _normalize_table_type(table_type)
    genome_build_norm = _normalize_genome_build(genome_build)
    token_value = ensure_token(token)

    params = {
        "snps": "\n".join(snp_list),
        "pop": pop_norm,
        "genome_build": genome_build_norm,
        "token": token_value,
    }

    payload = http_request(
        endpoint="ldhap",
        api_root=api_root,
        token=token_value,
        method="GET",
        params=params,
        timeout=120.0,
    )

    if not isinstance(payload, str):
        payload = str(payload)

    data_out = pd.read_csv(
        StringIO(payload),
        sep="\t",
        dtype="string",
        keep_default_na=False,
        na_values=[],
    )

    if data_out.apply(lambda col: col.astype(str).str.contains("error", case=False, na=False).any()).any():
        first_col = data_out.iloc[:, 0].astype(str)
        errors = first_col[first_col.str.contains("error", case=False, na=False)].tolist()
        raise RuntimeError(" ".join(errors))

    return _df_merge(data_out, table_type_norm, genome_build_norm)
