from __future__ import annotations

import re
import warnings
from typing import List, Sequence, Union

import pandas as pd

from .. import DEFAULT_API_ROOT
from ..exceptions import LDlinkError, ValidationError
from ..http import request
from ..parsing import parse_tsv
from ..validators import ensure_token, validate_genome_build, validate_r2d, validate_threshold

# Population codes from LDlinkR `list_pop` utility (pop_code column)
_AVAIL_POP: set[str] = {
    "ALL",
    "AFR",
    "YRI",
    "LWK",
    "GWD",
    "MSL",
    "ESN",
    "ASW",
    "ACB",
    "AMR",
    "MXL",
    "PUR",
    "CLM",
    "PEL",
    "EAS",
    "CHB",
    "JPT",
    "CHS",
    "CDX",
    "KHV",
    "EUR",
    "CEU",
    "TSI",
    "FIN",
    "GBR",
    "IBS",
    "SAS",
    "GIH",
    "PJL",
    "BEB",
    "STU",
    "ITU",
}

# GTEx v8 non-diseased tissues (LDlink /ldexpress accepted values)
_TISSUE_NAMES: List[str] = [
    "Adipose_Subcutaneous",
    "Adipose_Visceral_Omentum",
    "Adrenal_Gland",
    "Artery_Aorta",
    "Artery_Coronary",
    "Artery_Tibial",
    "Bladder",
    "Brain_Amygdala",
    "Brain_Anterior_cingulate_cortex_BA24",
    "Brain_Caudate_basal_ganglia",
    "Brain_Cerebellar_Hemisphere",
    "Brain_Cerebellum",
    "Brain_Cortex",
    "Brain_Frontal_Cortex_BA9",
    "Brain_Hippocampus",
    "Brain_Hypothalamus",
    "Brain_Nucleus_accumbens_basal_ganglia",
    "Brain_Putamen_basal_ganglia",
    "Brain_Spinal_cord_cervical_c-1",
    "Brain_Substantia_nigra",
    "Breast_Mammary_Tissue",
    "Cells_Cultured_fibroblasts",
    "Cells_EBV_transformed_lymphocytes",
    "Cervix_Ectocervix",
    "Cervix_Endocervix",
    "Colon_Sigmoid",
    "Colon_Transverse",
    "Esophagus_Gastroesophageal_Junction",
    "Esophagus_Mucosa",
    "Esophagus_Muscularis",
    "Fallopian_Tube",
    "Heart_Atrial_Appendage",
    "Heart_Left_Ventricle",
    "Kidney_Cortex",
    "Kidney_Medulla",
    "Liver",
    "Lung",
    "Minor_Salivary_Gland",
    "Muscle_Skeletal",
    "Nerve_Tibial",
    "Ovary",
    "Pancreas",
    "Pituitary",
    "Prostate",
    "Skin_Not_Sun_Exposed_Suprapubic",
    "Skin_Sun_Exposed_Lower_leg",
    "Small_Intestine_Terminal_Ileum",
    "Spleen",
    "Stomach",
    "Testis",
    "Thyroid",
    "Uterus",
    "Vagina",
    "Whole_Blood",
]

_TISSUE_ABBREV_TO_NAME: dict[str, str] = {
    "ADI_SUB": "Adipose_Subcutaneous",
    "ADI_VIS_OME": "Adipose_Visceral_Omentum",
    "ADR_GLA": "Adrenal_Gland",
    "ART_AOR": "Artery_Aorta",
    "ART_COR": "Artery_Coronary",
    "ART_TIB": "Artery_Tibial",
    "BLA": "Bladder",
    "BRA_AMY": "Brain_Amygdala",
    "BRA_ANT_CIN_COR_BA2": "Brain_Anterior_cingulate_cortex_BA24",
    "BRA_CAU_BAS_GAN": "Brain_Caudate_basal_ganglia",
    "BRA_CER_HEM": "Brain_Cerebellar_Hemisphere",
    "BRA_CER": "Brain_Cerebellum",
    "BRA_COR": "Brain_Cortex",
    "BRA_FRO_COR_BA9": "Brain_Frontal_Cortex_BA9",
    "BRA_HIP": "Brain_Hippocampus",
    "BRA_HYP": "Brain_Hypothalamus",
    "BRA_NUC_ACC_BAS_GAN": "Brain_Nucleus_accumbens_basal_ganglia",
    "BRA_PUT_BAS_GAN": "Brain_Putamen_basal_ganglia",
    "BRA_SPI_COR_CER_C-1": "Brain_Spinal_cord_cervical_c-1",
    "BRA_SUB_NIG": "Brain_Substantia_nigra",
    "BRE_MAM_MAM_TIS": "Breast_Mammary_Tissue",
    "CEL_CUL_FIB": "Cells_Cultured_fibroblasts",
    "CEL_EBV_TRA_LYN": "Cells_EBV_transformed_lymphocytes",
    "CER_ECT": "Cervix_Ectocervix",
    "CER_END": "Cervix_Endocervix",
    "COL_SIG": "Colon_Sigmoid",
    "COL_TRA": "Colon_Transverse",
    "ESO_GAS_JUN": "Esophagus_Gastroesophageal_Junction",
    "ESO_MUC": "Esophagus_Mucosa",
    "ESO_MUS": "Esophagus_Muscularis",
    "FAL_TUB": "Fallopian_Tube",
    "HEA_ATR": "Heart_Atrial_Appendage",
    "HEA_LEF": "Heart_Left_Ventricle",
    "KID_COR": "Kidney_Cortex",
    "KID_MED": "Kidney_Medulla",
    "LIV": "Liver",
    "LUN": "Lung",
    "MIN_SAL_GLA": "Minor_Salivary_Gland",
    "MUS_SKE": "Muscle_Skeletal",
    "NER_TIB": "Nerve_Tibial",
    "OVA": "Ovary",
    "PAN": "Pancreas",
    "PIT": "Pituitary",
    "PRO": "Prostate",
    "SKI_NOT_SUN_EXP_SUP": "Skin_Not_Sun_Exposed_Suprapubic",
    "SKI_SUN_EXP_LOW_LEG": "Skin_Sun_Exposed_Lower_leg",
    "SMA_INT_TER_ILE": "Small_Intestine_Terminal_Ileum",
    "SPL": "Spleen",
    "STO": "Stomach",
    "TES": "Testis",
    "THY": "Thyroid",
    "UTE": "Uterus",
    "VAG": "Vagina",
    "WHO_BLO": "Whole_Blood",
    "ALL": "ALL",
}

_RSID_RE = re.compile(r"^rs\d+$", flags=re.IGNORECASE)
_CHR_COORD_RE = re.compile(r"^chr(\d{1,2}|x|y):(\d{1,9})$", flags=re.IGNORECASE)


def _to_list(value: Union[str, Sequence[str]]) -> List[str]:
    if isinstance(value, str):
        return [value]
    return list(value)


def _normalize_variants(snps: Union[str, Sequence[str]]) -> List[str]:
    items = [str(s).strip() for s in _to_list(snps) if str(s).strip() != ""]
    if not (1 <= len(items) <= 10):
        raise ValidationError("snps must contain between 1 and 10 variants.")
    for v in items:
        if not (_RSID_RE.match(v) or _CHR_COORD_RE.match(v)):
            raise ValidationError(f"Invalid query format for variant: {v}.")
    return items


def _normalize_pop(pop: Union[str, Sequence[str]]) -> str:
    items = [str(p).strip() for p in _to_list(pop) if str(p).strip() != ""]
    if not items:
        raise ValidationError("pop cannot be empty.")
    if not all(p in _AVAIL_POP for p in items):
        raise ValidationError("Not a valid population code.")
    return "+".join(items)


def _normalize_tissues(tissue: Union[str, Sequence[str], None]) -> List[str]:
    if tissue is None:
        raise ValidationError("tissue cannot be None. Use a valid tissue type (or 'ALL').")

    items = [str(t).strip() for t in _to_list(tissue) if str(t).strip() != ""]
    if not items:
        raise ValidationError("tissue cannot be empty. Use a valid tissue type (or 'ALL').")

    if len(items) == 1 and items[0] == "ALL":
        return list(_TISSUE_NAMES)

    out: List[str] = []
    tissue_name_set = set(_TISSUE_NAMES)
    for t in items:
        if t in tissue_name_set:
            out.append(t)
        elif t in _TISSUE_ABBREV_TO_NAME:
            mapped = _TISSUE_ABBREV_TO_NAME[t]
            if mapped == "ALL":
                out.extend(_TISSUE_NAMES)
            else:
                out.append(mapped)
        else:
            raise ValidationError(
                f"'{t}' is an invalid input for tissue type. Select input from either "
                "'tissue_name_ldexpress' or 'tissue_abbrev' (case sensitive)."
            )

    seen: set[str] = set()
    deduped: List[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def _validate_window_size(win_size: int) -> int:
    try:
        w = int(win_size)
    except Exception as e:  # noqa: BLE001
        raise ValidationError(f"win_size must be an integer (0 to 1000000). Got: {win_size!r}") from e
    if not (0 <= w <= 1_000_000):
        raise ValidationError(f"Window size must be between 0 and 1000000 bp. Input window size was {w} bp.")
    return w


def _coerce_clean_output(df: pd.DataFrame, genome_build: str) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.rename(columns={"D.": "D'"})

    if "Position" in df.columns:
        df = df.rename(columns={"Position": f"Position_{genome_build}"})

    df.columns = [re.sub(r"(\.)+", "_", str(c)) for c in df.columns]
    df = df.astype(str)

    flattened = df.to_numpy().astype(str).ravel()
    has_error = any(re.search(r"error", x, flags=re.IGNORECASE) for x in flattened)
    has_warning = any(re.search(r"warning", x, flags=re.IGNORECASE) for x in flattened)

    if has_error:
        msgs: List[str] = []
        first_col = df.iloc[:, 0].astype(str)
        for v in first_col:
            if re.search(r"error", v, flags=re.IGNORECASE):
                msgs.append(v)
        msg = " ".join(msgs).strip() if msgs else "LDexpress returned an error."
        raise LDlinkError(msg)

    if has_warning:
        first_col = df.iloc[:, 0].astype(str)
        warn_lines = [v for v in first_col if "warning" in v.lower()]
        for wl in warn_lines:
            warnings.warn(wl, RuntimeWarning)

    return df


def ldexpress(
    snps: Union[str, Sequence[str]],
    pop: Union[str, Sequence[str]] = "CEU",
    tissue: Union[str, Sequence[str]] = "ALL",
    r2d: str = "r2",
    r2d_threshold: float = 0.1,
    p_threshold: float = 0.1,
    win_size: int = 500000,
    genome_build: str = "grch37",
    token: str | None = None,
) -> pd.DataFrame:
    """
    Query LDlink LDexpress (GTEx eQTL) endpoint.
    """
    tok = ensure_token(token)

    variants = _normalize_variants(snps)
    pop_str = _normalize_pop(pop)
    tissues = _normalize_tissues(tissue)

    validate_r2d(r2d)
    validate_threshold("r2d_threshold", r2d_threshold)
    validate_threshold("p_threshold", p_threshold)
    validate_genome_build(genome_build)
    win = _validate_window_size(win_size)

    json_body = {
        "snps": "\n".join(variants),
        "pop": pop_str,
        "tissues": "+".join(tissues),
        "r2_d": r2d,
        "r2_d_threshold": str(float(r2d_threshold)),
        "p_threshold": str(float(p_threshold)),
        "window": str(win),
        "genome_build": genome_build,
    }

    text = request(
        endpoint="/ldexpress",
        method="POST",
        api_root=DEFAULT_API_ROOT,
        token=tok,
        params={"token": tok},
        json_body=json_body,
    )

    df = parse_tsv(text)
    return _coerce_clean_output(df, genome_build=genome_build)