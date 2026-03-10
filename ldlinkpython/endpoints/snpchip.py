# ldlinkpython/endpoints/snpchip.py

from __future__ import annotations

import re
from io import StringIO
from typing import Sequence

import pandas as pd

from ldlinkpython import DEFAULT_API_ROOT
from ldlinkpython.exceptions import ValidationError
from ldlinkpython.http import request as http_request
from ldlinkpython.validators import ensure_token

_RSID_RE = re.compile(r"^rs\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)

_AVAIL_GENOME_BUILD = {"grch37", "grch38", "grch38_high_coverage"}

_ILLUMINA_CHIPS: list[str] = [
    "I_100", "I_1M", "I_1M-D", "I_240S", "I_300", "I_300-D", "I_550v1", "I_550v3", "I_610-Q", "I_650Y", "I_660W-Q",
    "I_CNV-12", "I_CNV370-D", "I_CNV370-Q", "I_CVD", "I_CardioMetab", "I_Core-12", "I_CoreE-12v1", "I_CoreE-12v1.1",
    "I_CoreE-24v1", "I_CoreE-24v1.1", "I_Cyto-12v2", "I_Cyto-12v2.1", "I_Cyto-12v2.1f", "I_Cyto850", "I_Exome-12",
    "I_Exon510S", "I_GSA-v1", "I_GSA-v2", "I_Immuno-24v1", "I_Immuno-24v2", "I_Linkage-12", "I_Linkage-24", "I_ME-Global-8",
    "I_MEGA", "I_NS-12", "I_O1-Q", "I_O1S-8", "I_O2.5-4", "I_O2.5-8", "I_O2.5E-8v1", "I_O2.5E-8v1.1", "I_O2.5E-8v1.2",
    "I_O2.5S-8", "I_O5-4", "I_O5E-4", "I_OE-12", "I_OE-12f", "I_OE-24", "I_OEE-8v1", "I_OEE-8v1.1", "I_OEE-8v1.2",
    "I_OEE-8v1.3", "I_OZH-8v1", "I_OZH-8v1.1", "I_OZH-8v1.2", "I_OncoArray", "I_Psyc-24v1", "I_Psyc-24v1.1",
]

_AFFY_CHIPS: list[str] = [
    "A_10X", "A_250N", "A_250S", "A_50H", "A_50X", "A_AFR", "A_ASI", "A_CHB2", "A_DMETplus", "A_EAS", "A_EUR", "A_Exome1A",
    "A_Exome319", "A_Hu", "A_Hu-CHB", "A_LAT", "A_Onco", "A_OncoCNV", "A_PMRA", "A_SNP5.0", "A_SNP6.0", "A_UKBA",
]

_AVAIL_CHIP = set(_ILLUMINA_CHIPS + _AFFY_CHIPS + ["ALL_Illumina", "ALL_Affy", "ALL"])

_ARRAY_TO_ABBREV = {
    "Illumina Infinium Human100kv1": "I_100",
    "Illumina Human1Mv1": "I_1M",
    "Illumina Human1M-Duov3": "I_1M-D",
    "Illumina HumanHap240S": "I_240S",
    "Illumina HumanHap300v1": "I_300",
    "Illumina HumanHap300-Duov2": "I_300-D",
    "Illumina HumanHap550v1": "I_550v1",
    "Illumina HumanHap550v3": "I_550v3",
    "Illumina Human610-Quadv1": "I_610-Q",
    "Illumina HumanHap650Yv3": "I_650Y",
    "Illumina Human660W-Quadv1": "I_660W-Q",
    "Illumina HumanCNV-12": "I_CNV-12",
    "Illumina HumanCNV370-Duov1": "I_CNV370-D",
    "Illumina HumanCNV370-Quadv3": "I_CNV370-Q",
    "Illumina HumanCVDv1": "I_CVD",
    "Illumina Cardio-MetaboChip": "I_CardioMetab",
    "Illumina HumanCore-12v1": "I_Core-12",
    "Illumina HumanCoreExome-12v1": "I_CoreE-12v1",
    "Illumina HumanCoreExome-12v1.1": "I_CoreE-12v1.1",
    "Illumina HumanCoreExome-24v1": "I_CoreE-24v1",
    "Illumina HumanCoreExome-24v1.1": "I_CoreE-24v1.1",
    "Illumina HumanCytoSNP-12v2": "I_Cyto-12v2",
    "Illumina HumanCytoSNP-12v2.1": "I_Cyto-12v2.1",
    "Illumina HumanCytoSNP-12v2.1 FFPE": "I_Cyto-12v2.1f",
    "Illumina Infinium CytoSNP-850K": "I_Cyto850",
    "Illumina HumanExome-12v1.1": "I_Exome-12",
    "Illumina HumanExon510Sv1": "I_Exon510S",
    "Illumina Global Screening version 1": "I_GSA-v1",
    "Illumina Global Screening version 2": "I_GSA-v2",
    "Illumina HumanImmuno-24v1": "I_Immuno-24v1",
    "Illumina HumanImmuno-24v2": "I_Immuno-24v2",
    "Illumina HumanLinkage-12": "I_Linkage-12",
    "Illumina HumanLinkage-24": "I_Linkage-24",
    "Illumina Infinium Multi-Ethnic Global-8": "I_ME-Global-8",
    "Illumina Multi-Ethnic Global": "I_MEGA",
    "Illumina HumanNS-12": "I_NS-12",
    "Illumina HumanOmni1-Quadv1": "I_O1-Q",
    "Illumina HumanOmni1S-8v1": "I_O1S-8",
    "Illumina HumanOmni2.5-4v1": "I_O2.5-4",
    "Illumina HumanOmni2.5-8v1.2": "I_O2.5-8",
    "Illumina HumanOmni2.5Exome-8v1": "I_O2.5E-8v1",
    "Illumina HumanOmni2.5Exome-8v1.1": "I_O2.5E-8v1.1",
    "Illumina HumanOmni2.5Exome-8v1.2": "I_O2.5E-8v1.2",
    "Illumina HumanOmni2.5S-8v1": "I_O2.5S-8",
    "Illumina HumanOmni5-4v1": "I_O5-4",
    "Illumina HumanOmni5Exome-4v1": "I_O5E-4",
    "Illumina HumanOmniExpress-12v1": "I_OE-12",
    "Illumina HumanOmniExpress-12v1 FFPE": "I_OE-12f",
    "Illumina HumanOmniExpress-24v1": "I_OE-24",
    "Illumina HumanOmniExpressExome-8v1": "I_OEE-8v1",
    "Illumina HumanOmniExpressExome-8v1.1": "I_OEE-8v1.1",
    "Illumina HumanOmniExpressExome-8v1.2": "I_OEE-8v1.2",
    "Illumina HumanOmniExpressExome-8v1.3": "I_OEE-8v1.3",
    "Illumina HumanOmniZhongHua-8v1": "I_OZH-8v1",
    "Illumina HumanOmniZhongHua-8v1.1": "I_OZH-8v1.1",
    "Illumina HumanOmniZhongHua-8v1.2": "I_OZH-8v1.2",
    "Illumina Infinium OncoArray-500K": "I_OncoArray",
    "Illumina Infinium PsychArray-24v1": "I_Psyc-24v1",
    "Illumina Infinium PsychArray-24v1.1": "I_Psyc-24v1.1",
    "Affymetrix Mapping 10K Xba142": "A_10X",
    "Affymetrix Mapping 250K Nsp": "A_250N",
    "Affymetrix Mapping 250K Sty": "A_250S",
    "Affymetrix Mapping 50K Hind240": "A_50H",
    "Affymetrix Mapping 50K Xba240": "A_50X",
    "Affymetrix Axiom GW AFR": "A_AFR",
    "Affymetrix Axiom GW ASI": "A_ASI",
    "Affymetrix Axiom GW CHB2": "A_CHB2",
    "Affymetrix DMET Plus": "A_DMETplus",
    "Affymetrix Axiom GW EAS": "A_EAS",
    "Affymetrix Axiom GW EUR": "A_EUR",
    "Affymetrix Axiom Exome 1A": "A_Exome1A",
    "Affymetrix Axiom Exome 319": "A_Exome319",
    "Affymetrix Axiom GW Hu": "A_Hu",
    "Affymetrix Axiom GW Hu-CHB": "A_Hu-CHB",
    "Affymetrix Axiom GW LAT": "A_LAT",
    "Affymetrix OncoScan": "A_Onco",
    "Affymetrix OncoScan CNV": "A_OncoCNV",
    "Affymetrix Axiom Precision Medicine Research": "A_PMRA",
    "Affymetrix SNP 5.0": "A_SNP5.0",
    "Affymetrix SNP 6.0": "A_SNP6.0",
    "Affymetrix Axiom UK Biobank": "A_UKBA",
}


def _to_list(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _normalize_snps(snps: str | Sequence[str]) -> list[str]:
    vals = [str(s).strip() for s in _to_list(snps) if str(s).strip()]
    if not (1 <= len(vals) <= 5000):
        raise ValidationError("Input is between 1 to 5000 variants.")

    for v in vals:
        if not (_RSID_RE.match(v) or _CHR_COORD_RE.match(v)):
            raise ValidationError(f"Invalid query format for variant: {v}.")

    return vals


def _normalize_chip(chip: str | Sequence[str]) -> list[str]:
    vals = [str(c).strip() for c in _to_list(chip) if str(c).strip()]
    if not vals:
        raise ValidationError("Invalid SNP chip array platform code.")

    if len(vals) == 1:
        if vals[0] == "ALL":
            return _ILLUMINA_CHIPS + _AFFY_CHIPS
        if vals[0] == "ALL_Illumina":
            return _ILLUMINA_CHIPS
        if vals[0] == "ALL_Affy":
            return _AFFY_CHIPS

    if not all(c in _AVAIL_CHIP for c in vals):
        raise ValidationError("Invalid SNP chip array platform code.")

    return vals


def _normalize_genome_build(genome_build: str) -> str:
    v = str(genome_build).strip().lower()
    if v not in _AVAIL_GENOME_BUILD:
        raise ValidationError("Not an available genome build.")
    return v


def _normalize_return_type(return_type: str) -> str:
    v = str(return_type).strip().lower()
    if v not in {"dataframe", "raw"}:
        raise ValidationError("return_type must be 'dataframe' or 'raw'.")
    return v


def _count_snp_rows(data_out: pd.DataFrame) -> int:
    if data_out.empty:
        return 0
    first_col = data_out.iloc[:, 0].astype("string")
    return int(first_col.str.match(_RSID_RE).sum())


def _format_tbl(out_raw: pd.DataFrame) -> pd.DataFrame:
    snp_count = _count_snp_rows(out_raw)
    out = out_raw.iloc[:snp_count, :2].copy()
    out.columns = [re.sub(r"_$", "", re.sub(r"(\.)+", "_", str(c))) for c in out.columns]

    if out_raw.shape[1] <= 2:
        return out

    arrays = out_raw.iloc[:snp_count, 2]

    for i, val in enumerate(arrays.tolist()):
        if pd.isna(val):
            continue
        for arr_name in [v.strip() for v in str(val).split(",") if v.strip()]:
            abbrev = _ARRAY_TO_ABBREV.get(arr_name)
            if not abbrev:
                continue
            if abbrev not in out.columns:
                out[abbrev] = 0
            out.iloc[i, out.columns.get_loc(abbrev)] = 1

    return out


def snpchip(
    snps: str | Sequence[str],
    chip: str | Sequence[str] = "ALL",
    genome_build: str = "grch37",
    token: str | None = None,
    api_root: str = DEFAULT_API_ROOT,
    return_type: str = "dataframe",
):
    snp_list = _normalize_snps(snps)
    chip_list = _normalize_chip(chip)
    genome_build_norm = _normalize_genome_build(genome_build)
    return_type_norm = _normalize_return_type(return_type)
    token_value = ensure_token(token)

    body = {
        "snps": "\n".join(snp_list),
        "platforms": "+".join(chip_list),
        "genome_build": genome_build_norm,
    }

    data = http_request(
        endpoint="snpchip",
        api_root=api_root,
        token=token_value,
        method="POST",
        json_body=body,
        timeout=120.0,
    )

    if return_type_norm == "raw":
        return data

    if not isinstance(data, str):
        data = str(data)

    data_out = pd.read_csv(StringIO(data), sep="\t", dtype="string")
    snp_count = _count_snp_rows(data_out)

    if snp_count < len(data_out):
        msg = str(data_out.iloc[snp_count, 0])
        if "error" in msg.lower():
            raise RuntimeError(msg)

    return _format_tbl(data_out)
