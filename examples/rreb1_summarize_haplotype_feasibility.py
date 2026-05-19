#!/usr/bin/env python3
"""Summarize local RREB1 haplotype feasibility example outputs.

This script is a post-processing/reporting layer for
``rreb1_haplotype_feasibility_grch37.py``. It reads local CSV files only.
It does not call LDlink, does not require ``LDLINK_TOKEN``, and does not use
external annotations.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_NAME = "examples/rreb1_summarize_haplotype_feasibility.py"
DEFAULT_INPUT_DIR = Path("examples/output/rreb1_haplotype_feasibility_grch37")
DEFAULT_OUT_DIR_NAME = "summary"
CORE_VARIANTS = ["rs7742053", "rs17142617", "rs74781311", "rs2876045"]
HAPLOTYPE_SNPS = ["rs17142617", "rs74781311", "rs2876045"]
POPULATIONS = ["EUR", "AFR", "AMR", "EAS", "SAS"]
GENOME_BUILD = "grch37"

VARIANT_ROLES = {
    "rs7742053": "published lead GWAS SNP",
    "rs17142617": "published high-LD surrogate/tag SNP and 3-SNP haplotype marker",
    "rs74781311": "published 3-SNP haplotype marker",
    "rs2876045": "published 3-SNP haplotype marker",
}

VARIANT_NOTES = {
    "rs7742053": "Lead 6p25.1/RREB1 Ewing sarcoma GWAS SNP.",
    "rs17142617": (
        "Published surrogate SNP in high LD with rs7742053; part of the "
        "3-SNP haplotype."
    ),
    "rs74781311": (
        "Part of the published 3-SNP haplotype associated with longer GGAA "
        "microsatellite alleles."
    ),
    "rs2876045": (
        "Part of the published 3-SNP haplotype associated with longer GGAA "
        "microsatellite alleles."
    ),
}


@dataclass
class ReportContext:
    input_dir: Path
    out_dir: Path
    created_at: str
    warnings: list[str] = field(default_factory=list)
    plot_paths: list[Path] = field(default_factory=list)
    skipped_plots: list[str] = field(default_factory=list)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize local CSV outputs from the RREB1 haplotype feasibility "
            "example. No LDlink API calls are made."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory containing first-script outputs. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Summary output directory. Default: <input-dir>/summary",
    )
    parser.add_argument(
        "--make-plots",
        action="store_true",
        help="Optionally create simple PNG plots with matplotlib if available.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Accepted for explicit workflows. Summary outputs are deterministic "
            "and are safely replaced."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print details about detected files and written outputs.",
    )
    return parser.parse_args(argv)


def normalized_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).strip().lower())


def find_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    lookup = {normalized_name(col): str(col) for col in df.columns}
    for candidate in candidates:
        found = lookup.get(normalized_name(candidate))
        if found is not None:
            return found
    return None


def read_csv(path: Path, warnings: list[str]) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        warnings.append(f"Could not read {path.name}: {exc}")
        return None


def write_csv(df: pd.DataFrame, path: Path, verbose: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    if verbose:
        print(f"Wrote {path}")


def population_from_filename(path: Path) -> str:
    stem = path.stem
    for pop in POPULATIONS + ["ALL", "EUR"]:
        if stem.endswith(f"_{pop}"):
            return pop
    parts = stem.split("_")
    return parts[-1].upper() if parts else ""


def variants_from_pair_filename(path: Path) -> tuple[str, str]:
    matches = re.findall(r"rs\d+", path.name, flags=re.IGNORECASE)
    if len(matches) >= 2:
        return matches[0], matches[1]
    return "", ""


def detect_source_files(input_dir: Path) -> dict[str, list[Path]]:
    return {
        "ldpair": sorted(input_dir.glob("ldpair_*.csv")),
        "ldpop": sorted(input_dir.glob("ldpop_*.csv")),
        "ldmatrix": sorted(input_dir.glob("ldmatrix_*.csv")),
        "ldhap": sorted(input_dir.glob("ldhap_*.csv")),
        "snpchip": sorted(input_dir.glob("snpchip_*.csv")),
        "metadata": sorted(input_dir.glob("rreb1_variant_metadata.*")),
        "manifest": sorted(input_dir.glob("manifest.json")),
    }


def validate_input_files(input_dir: Path, files: Mapping[str, list[Path]]) -> None:
    if not input_dir.exists():
        raise SystemExit(
            f"Input directory does not exist: {input_dir}\n"
            "First run: python examples/rreb1_haplotype_feasibility_grch37.py"
        )

    required_kinds = ["ldpair", "ldpop", "ldmatrix", "ldhap"]
    if not any(files[kind] for kind in required_kinds):
        raise SystemExit(
            f"No RREB1 endpoint CSV files were detected in {input_dir}.\n"
            "First run: python examples/rreb1_haplotype_feasibility_grch37.py"
        )


def load_manifest(paths: Sequence[Path], warnings: list[str]) -> dict[str, Any]:
    if not paths:
        return {}
    try:
        return json.loads(paths[0].read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append(f"Could not read {paths[0].name}: {exc}")
        return {}


def create_variant_summary(
    metadata_paths: Sequence[Path],
    warnings: list[str],
) -> pd.DataFrame:
    metadata: dict[str, dict[str, str]] = {}
    if metadata_paths:
        path = metadata_paths[0]
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                rows = payload if isinstance(payload, list) else payload.get("variants", [])
                metadata = {str(row.get("variant", "")): dict(row) for row in rows}
            except Exception as exc:
                warnings.append(f"Could not parse {path.name}: {exc}")
        else:
            df = read_csv(path, warnings)
            if df is not None and "variant" in df.columns:
                metadata = {
                    str(row["variant"]): {str(k): str(v) for k, v in row.items()}
                    for row in df.to_dict(orient="records")
                }

    rows = []
    for variant in CORE_VARIANTS:
        row = metadata.get(variant, {})
        rows.append(
            {
                "variant": variant,
                "role": row.get("role", VARIANT_ROLES[variant]),
                "genome_build": row.get("genome_build", GENOME_BUILD),
                "included_in_4snp_ld_matrix": variant in CORE_VARIANTS,
                "included_in_3snp_haplotype": variant in HAPLOTYPE_SNPS,
                "notes": row.get("notes", VARIANT_NOTES[variant]),
            }
        )
    return pd.DataFrame(rows)


def create_pairwise_ld_summary(
    ldpair_paths: Sequence[Path],
    ldpop_paths: Sequence[Path],
    warnings: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for path in ldpair_paths:
        df = read_csv(path, warnings)
        var1_file, var2_file = variants_from_pair_filename(path)
        if df is None or df.empty:
            rows.append(
                {
                    "source_endpoint": "LDpair",
                    "source_file": path.name,
                    "variant_1": var1_file,
                    "variant_2": var2_file,
                    "notes": "File could not be read or contained no rows.",
                }
            )
            continue

        cols = {
            "variant_1": find_column(df, ["SNP_A", "variant_1", "var1"]),
            "variant_2": find_column(df, ["SNP_B", "variant_2", "var2"]),
            "population": find_column(df, ["Population", "pop"]),
            "r2": find_column(df, ["R2", "R_squared", "r2", "r²"]),
            "dprime": find_column(df, ["Dprime", "D_prime", "D'", "D’", "dprime"]),
            "correlated_alleles": find_column(df, ["Correlated_Alleles", "correlated alleles"]),
        }
        for _, record in df.iterrows():
            rows.append(
                {
                    "source_endpoint": "LDpair",
                    "source_file": path.name,
                    "variant_1": record.get(cols["variant_1"], var1_file) if cols["variant_1"] else var1_file,
                    "variant_2": record.get(cols["variant_2"], var2_file) if cols["variant_2"] else var2_file,
                    "population": record.get(cols["population"], population_from_filename(path)) if cols["population"] else population_from_filename(path),
                    "r2": record.get(cols["r2"], "") if cols["r2"] else "",
                    "dprime": record.get(cols["dprime"], "") if cols["dprime"] else "",
                    "correlated_alleles": record.get(cols["correlated_alleles"], "") if cols["correlated_alleles"] else "",
                    "notes": "" if cols["r2"] else "R2 column could not be confidently parsed.",
                }
            )

    for path in ldpop_paths:
        df = read_csv(path, warnings)
        var1_file, var2_file = variants_from_pair_filename(path)
        if df is None or df.empty:
            rows.append(
                {
                    "source_endpoint": "LDpop",
                    "source_file": path.name,
                    "variant_1": var1_file,
                    "variant_2": var2_file,
                    "notes": "File could not be read or contained no rows.",
                }
            )
            continue

        pop_col = find_column(df, ["Abbrev", "Population", "pop", "population"])
        r2_col = find_column(df, ["R2", "R_squared", "r2", "r²"])
        dprime_col = find_column(df, ["Dprime", "D_prime", "D'", "D’", "dprime"])
        for _, record in df.iterrows():
            rows.append(
                {
                    "source_endpoint": "LDpop",
                    "source_file": path.name,
                    "variant_1": var1_file,
                    "variant_2": var2_file,
                    "population": record.get(pop_col, "") if pop_col else "",
                    "r2": record.get(r2_col, "") if r2_col else "",
                    "dprime": record.get(dprime_col, "") if dprime_col else "",
                    "correlated_alleles": "",
                    "notes": "" if r2_col else "R2 column could not be confidently parsed.",
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "source_endpoint",
            "source_file",
            "variant_1",
            "variant_2",
            "population",
            "r2",
            "dprime",
            "correlated_alleles",
            "notes",
        ],
    )


def create_ldmatrix_summaries(
    ldmatrix_paths: Sequence[Path],
    warnings: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    index_rows = []
    long_rows = []

    for path in ldmatrix_paths:
        df = read_csv(path, warnings)
        population = population_from_filename(path)
        if df is None or df.empty:
            index_rows.append(
                {
                    "population": population,
                    "source_file": path.name,
                    "variants_included": "",
                    "n_variants_detected": 0,
                    "notes": "File could not be read or contained no rows.",
                }
            )
            continue

        first_col = str(df.columns[0])
        variant_rows = [str(v) for v in df[first_col].tolist()]
        matrix_cols = [str(c) for c in df.columns[1:]]
        variants = sorted(set(variant_rows).union(matrix_cols))
        notes = ""
        if set(variant_rows) != set(matrix_cols):
            notes = "Row and column variant sets differ; long-format values may be incomplete."

        index_rows.append(
            {
                "population": population,
                "source_file": path.name,
                "variants_included": "; ".join(variants),
                "n_variants_detected": len(variants),
                "notes": notes,
            }
        )

        for _, record in df.iterrows():
            variant_1 = str(record[first_col])
            for variant_2 in matrix_cols:
                long_rows.append(
                    {
                        "population": population,
                        "variant_1": variant_1,
                        "variant_2": variant_2,
                        "ld_value": record.get(variant_2, ""),
                        "metric": "R2",
                        "source_file": path.name,
                    }
                )

    index_df = pd.DataFrame(
        index_rows,
        columns=[
            "population",
            "source_file",
            "variants_included",
            "n_variants_detected",
            "notes",
        ],
    )
    long_df = pd.DataFrame(long_rows) if long_rows else None
    return index_df, long_df


def create_haplotype_summary(
    ldhap_paths: Sequence[Path],
    warnings: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for path in ldhap_paths:
        df = read_csv(path, warnings)
        population = population_from_filename(path)
        if df is None or df.empty:
            rows.append(
                {
                    "population": population,
                    "haplotype": "",
                    "frequency": "",
                    "count": "",
                    "source_file": path.name,
                    "notes": "File could not be read or contained no rows.",
                }
            )
            continue

        frequency_col = find_column(df, ["Frequency", "freq", "haplotype_frequency"])
        count_col = find_column(df, ["Count", "haplotype_count", "n"])
        explicit_hap_col = find_column(df, ["Haplotype", "haplotype", "alleles"])
        allele_cols = [
            col
            for col in df.columns
            if col not in {frequency_col, count_col} and normalized_name(col) not in {"notes"}
        ]

        for _, record in df.iterrows():
            if explicit_hap_col:
                haplotype = record.get(explicit_hap_col, "")
            else:
                haplotype = "_".join(str(record.get(col, "")) for col in allele_cols)
            rows.append(
                {
                    "population": population,
                    "haplotype": haplotype,
                    "frequency": record.get(frequency_col, "") if frequency_col else "",
                    "count": record.get(count_col, "") if count_col else "",
                    "source_file": path.name,
                    "notes": "" if frequency_col else "Frequency column could not be confidently parsed.",
                }
            )

    return pd.DataFrame(
        rows,
        columns=["population", "haplotype", "frequency", "count", "source_file", "notes"],
    )


def create_snpchip_summary(
    snpchip_paths: Sequence[Path],
    warnings: list[str],
) -> pd.DataFrame | None:
    if not snpchip_paths:
        return None

    rows = []
    for path in snpchip_paths:
        df = read_csv(path, warnings)
        if df is None or df.empty:
            continue

        variant_col = find_column(df, ["RS Number", "RS_Number", "variant", "snp"])
        position_col = find_column(df, ["Position (GRCh37)", "Coord", "position"])
        if not variant_col:
            warnings.append(f"Could not identify variant column in {path.name}.")
            continue

        non_chip_cols = {variant_col}
        if position_col:
            non_chip_cols.add(position_col)

        chip_cols = [col for col in df.columns if col not in non_chip_cols]
        for _, record in df.iterrows():
            for chip_col in chip_cols:
                rows.append(
                    {
                        "variant": record.get(variant_col, ""),
                        "chip_or_array": chip_col,
                        "present_or_status": record.get(chip_col, ""),
                        "source_file": path.name,
                        "notes": "",
                    }
                )

    if not rows:
        return None
    return pd.DataFrame(
        rows,
        columns=["variant", "chip_or_array", "present_or_status", "source_file", "notes"],
    )


def create_practical_feasibility_summary(
    pairwise_df: pd.DataFrame,
    ldmatrix_index_df: pd.DataFrame,
    haplotype_df: pd.DataFrame,
    snpchip_df: pd.DataFrame | None,
) -> pd.DataFrame:
    rows = []

    lead_surrogate = pairwise_df[
        (pairwise_df["variant_1"].astype(str).eq("rs7742053"))
        & (pairwise_df["variant_2"].astype(str).eq("rs17142617"))
    ]
    r2_values = pd.to_numeric(lead_surrogate["r2"], errors="coerce").dropna()
    lead_text = "Lead/surrogate LD rows were detected."
    if not r2_values.empty:
        lead_text = (
            "Lead/surrogate LD evidence is available; observed R2 values range "
            f"from {r2_values.min():.4g} to {r2_values.max():.4g} across available "
            "LDpair/LDpop summaries."
        )
    rows.append(
        {
            "question": "Does the published surrogate rs17142617 have LD evidence with the lead SNP rs7742053?",
            "summary": lead_text,
            "supporting_files": "; ".join(sorted(lead_surrogate["source_file"].dropna().astype(str).unique())),
            "caveats": "LD evidence supports SNP-tag feasibility only; it does not identify causal alleles or measure GGAA repeat length.",
        }
    )

    hap_variants_present = all(
        haplotype_df["haplotype"].astype(str).str.contains("_").any()
        for _ in HAPLOTYPE_SNPS
    )
    rows.append(
        {
            "question": "Are the 3 haplotype SNPs represented in the LDhap outputs?",
            "summary": (
                "LDhap output files were parsed into 3-SNP haplotype strings."
                if hap_variants_present and not haplotype_df.empty
                else "LDhap outputs were missing or could not be confidently parsed."
            ),
            "supporting_files": "; ".join(sorted(haplotype_df["source_file"].dropna().astype(str).unique())),
            "caveats": "LDhap summarizes SNP haplotypes, not GGAA microsatellite alleles.",
        }
    )

    hap_pops = sorted(set(haplotype_df["population"].dropna().astype(str)))
    rows.append(
        {
            "question": "Are haplotype frequencies available across EUR, AFR, AMR, EAS, and SAS?",
            "summary": f"Haplotype summaries were detected for: {', '.join(hap_pops) or 'none'}.",
            "supporting_files": "; ".join(sorted(haplotype_df["source_file"].dropna().astype(str).unique())),
            "caveats": "Population coverage depends on the first-script LDhap outputs.",
        }
    )

    matrix_pops = sorted(set(ldmatrix_index_df["population"].dropna().astype(str)))
    rows.append(
        {
            "question": "Are LDmatrix outputs available across EUR, AFR, AMR, EAS, and SAS?",
            "summary": f"LDmatrix summaries were detected for: {', '.join(matrix_pops) or 'none'}.",
            "supporting_files": "; ".join(sorted(ldmatrix_index_df["source_file"].dropna().astype(str).unique())),
            "caveats": "LD matrices provide source data for LD heatmaps or tables only.",
        }
    )

    if snpchip_df is None or snpchip_df.empty:
        chip_summary = "SNPchip output was not detected."
        chip_files = ""
    else:
        present = pd.to_numeric(snpchip_df["present_or_status"], errors="coerce").fillna(0)
        chip_summary = (
            f"SNPchip coverage rows were detected; {int((present > 0).sum())} "
            "variant-platform entries are marked present."
        )
        chip_files = "; ".join(sorted(snpchip_df["source_file"].dropna().astype(str).unique()))
    rows.append(
        {
            "question": "Is SNPchip coverage available for the 4-SNP set?",
            "summary": chip_summary,
            "supporting_files": chip_files,
            "caveats": "Array coverage is practical feasibility information, not functional annotation.",
        }
    )

    return pd.DataFrame(rows)


def write_workflow_diagram(out_dir: Path, verbose: bool = False) -> Path:
    diagram = """flowchart TD
    A[Published RREB1/EwS SNP tags] --> B[LDpair: key pairwise LD]
    A --> C[LDpop: population-specific pairwise LD]
    A --> D[LDmatrix: 4-SNP LD structure]
    A --> E[LDhap: 3-SNP haplotype frequencies]
    A --> F[Optional SNPchip: array coverage]
    B --> G[Summary CSV tables]
    C --> G
    D --> G
    E --> G
    F --> G
    G --> H[Markdown report]
    H --> I[Future manuscript tables and figures]
"""
    path = out_dir / "workflow_diagram.mmd"
    path.write_text(diagram, encoding="utf-8")
    if verbose:
        print(f"Wrote {path}")
    return path


def markdown_table(df: pd.DataFrame, max_rows: int = 8) -> str:
    if df.empty:
        return "_No rows available._"

    small = df.head(max_rows).fillna("")
    columns = [str(col) for col in small.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in small.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in small.columns]
        lines.append("| " + " | ".join(values) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines)


def make_plots(
    out_dir: Path,
    ldmatrix_paths: Sequence[Path],
    haplotype_df: pd.DataFrame,
    context: ReportContext,
    verbose: bool = False,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        msg = "matplotlib is not installed; skipping optional PNG plots."
        print(msg)
        context.skipped_plots.append(msg)
        return

    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    for path in ldmatrix_paths:
        population = population_from_filename(path)
        try:
            df = pd.read_csv(path, index_col=0)
            numeric_df = df.apply(pd.to_numeric, errors="coerce")
            fig, ax = plt.subplots(figsize=(5.5, 4.5))
            image = ax.imshow(numeric_df.values, vmin=0, vmax=1, cmap="viridis")
            ax.set_xticks(range(len(numeric_df.columns)))
            ax.set_xticklabels(numeric_df.columns, rotation=45, ha="right")
            ax.set_yticks(range(len(numeric_df.index)))
            ax.set_yticklabels(numeric_df.index)
            ax.set_title(f"RREB1 4-SNP LD matrix ({population})")
            fig.colorbar(image, ax=ax, label="R2")
            fig.tight_layout()
            out_path = figures_dir / f"rreb1_ld_heatmap_{population}.png"
            fig.savefig(out_path, dpi=180)
            plt.close(fig)
            context.plot_paths.append(out_path)
            if verbose:
                print(f"Wrote {out_path}")
        except Exception as exc:
            context.skipped_plots.append(f"Skipped LD heatmap for {path.name}: {exc}")

    try:
        plot_df = haplotype_df.copy()
        plot_df["frequency_numeric"] = pd.to_numeric(plot_df["frequency"], errors="coerce")
        top_haps = (
            plot_df.groupby("haplotype", dropna=False)["frequency_numeric"]
            .max()
            .sort_values(ascending=False)
            .head(5)
            .index.tolist()
        )
        plot_df = plot_df[plot_df["haplotype"].isin(top_haps)]
        pivot = plot_df.pivot_table(
            index="population",
            columns="haplotype",
            values="frequency_numeric",
            aggfunc="first",
        ).reindex(POPULATIONS)
        ax = pivot.plot(kind="bar", figsize=(8, 4.5))
        ax.set_ylabel("Haplotype frequency")
        ax.set_xlabel("1000 Genomes population")
        ax.set_title("RREB1 3-SNP haplotype frequencies")
        ax.legend(title="Haplotype", bbox_to_anchor=(1.02, 1), loc="upper left")
        ax.figure.tight_layout()
        out_path = figures_dir / "rreb1_haplotype_frequencies_by_population.png"
        ax.figure.savefig(out_path, dpi=180)
        plt.close(ax.figure)
        context.plot_paths.append(out_path)
        if verbose:
            print(f"Wrote {out_path}")
    except Exception as exc:
        context.skipped_plots.append(f"Skipped haplotype frequency plot: {exc}")


def relative_link(target: Path, base_dir: Path) -> str:
    try:
        return target.relative_to(base_dir).as_posix()
    except ValueError:
        return target.as_posix()


def create_report(
    context: ReportContext,
    files: Mapping[str, list[Path]],
    variant_summary_df: pd.DataFrame,
    pairwise_df: pd.DataFrame,
    ldmatrix_index_df: pd.DataFrame,
    long_matrix_created: bool,
    haplotype_df: pd.DataFrame,
    snpchip_df: pd.DataFrame | None,
    feasibility_df: pd.DataFrame,
) -> str:
    source_counts = {
        "LDpair": len(files["ldpair"]),
        "LDpop": len(files["ldpop"]),
        "LDmatrix": len(files["ldmatrix"]),
        "LDhap": len(files["ldhap"]),
        "SNPchip": len(files["snpchip"]),
        "metadata": len(files["metadata"]),
    }
    source_counts_df = pd.DataFrame(
        [{"source_type": key, "files_detected": value} for key, value in source_counts.items()]
    )

    ldpair_preview = pairwise_df[pairwise_df["source_endpoint"].eq("LDpair")].copy()
    ldpop_super = pairwise_df[
        pairwise_df["source_endpoint"].eq("LDpop")
        & pairwise_df["population"].astype(str).isin(["ALL", *POPULATIONS])
    ].copy()
    pairwise_preview = pd.concat([ldpair_preview, ldpop_super], ignore_index=True)
    pairwise_preview = pairwise_preview[
        [
            "source_endpoint",
            "variant_1",
            "variant_2",
            "population",
            "r2",
            "dprime",
        ]
    ]

    hap_preview = haplotype_df.copy()
    hap_preview["frequency_numeric"] = pd.to_numeric(hap_preview["frequency"], errors="coerce")
    hap_preview = (
        hap_preview.sort_values(["population", "frequency_numeric"], ascending=[True, False])
        .groupby("population", as_index=False)
        .head(3)
    )
    hap_preview = hap_preview[["population", "haplotype", "frequency", "count"]]

    snpchip_section = "SNPchip output was not detected and this part was skipped."
    if snpchip_df is not None and not snpchip_df.empty:
        present = pd.to_numeric(snpchip_df["present_or_status"], errors="coerce").fillna(0)
        counts = (
            snpchip_df.assign(present_numeric=present)
            .groupby("variant", as_index=False)["present_numeric"]
            .sum()
            .rename(columns={"present_numeric": "platforms_with_variant"})
        )
        snpchip_section = (
            "SNPchip output was detected. The parsed summary is available in "
            "`rreb1_snpchip_summary.csv`.\n\n"
            + markdown_table(counts, max_rows=8)
        )

    plot_lines = []
    if context.plot_paths:
        plot_lines.append("Generated PNG plots:")
        for path in context.plot_paths:
            rel = relative_link(path, context.out_dir)
            plot_lines.append(f"- ![{path.stem}]({rel})")
    if context.skipped_plots:
        plot_lines.append("Skipped plot notes:")
        for note in context.skipped_plots:
            plot_lines.append(f"- {note}")
    plot_text = "\n".join(plot_lines) if plot_lines else "No PNG plots were requested or generated."

    warnings_text = ""
    if context.warnings:
        warnings_text = "\n\nWarnings noted while reading files:\n" + "\n".join(
            f"- {warning}" for warning in context.warnings
        )

    long_matrix_text = (
        "A long-format LD matrix table was created as `rreb1_ldmatrix_long_format.csv`."
        if long_matrix_created
        else "A long-format LD matrix table could not be created from the available files."
    )

    report = f"""# RREB1 haplotype feasibility report

## Scope

This report summarizes LDlinkPy output files for published SNP tags at the Ewing sarcoma 6p25.1/RREB1 locus.

LDlinkPy evaluates SNP linkage disequilibrium, haplotype structure, and related LDlink outputs. It does not directly measure, infer, or reproduce GGAA microsatellite length.

The RREB1 paper's biological result depends on targeted long-read sequencing of the GGAA microsatellite and functional follow-up. This report only summarizes LDlinkPy outputs for published SNP tags around the RREB1 locus. It does not make causal claims.

The key practical question is: Can the published RREB1 SNP tags be evaluated as practical SNP-based markers across 1000 Genomes populations using LDlinkPy outputs alone?

## How this report was generated

- Input directory: `{context.input_dir}`
- Output directory: `{context.out_dir}`
- Date/time: `{context.created_at}`
- Script name: `{SCRIPT_NAME}`
- No LDlink API calls were made.
- No `LDLINK_TOKEN` was required.

## Variant set

The variant summary table is available as `rreb1_variant_summary.csv`.

{markdown_table(variant_summary_df, max_rows=8)}

## Available source files

{markdown_table(source_counts_df, max_rows=8)}

## Pairwise LD summary

LDpair and LDpop outputs summarize pairwise LD among the lead SNP, surrogate SNP, and 3-SNP haplotype markers. LDpair provides key pairwise LD in EUR, while LDpop provides population-specific pairwise LD summaries across 1000 Genomes populations.

The parsed pairwise LD table is available as `rreb1_pairwise_ld_summary.csv`.

{markdown_table(pairwise_preview, max_rows=18)}

## LD matrix summaries

LDmatrix files provide source data for possible ancestry-specific LD matrices or heatmaps for the RREB1 4-SNP set.

The LDmatrix file index is available as `rreb1_ldmatrix_file_index.csv`. {long_matrix_text}

{markdown_table(ldmatrix_index_df, max_rows=8)}

{plot_text}

## Haplotype frequency summaries

LDhap files summarize the 3-SNP haplotypes for `rs17142617`, `rs74781311`, and `rs2876045`.

The parsed haplotype frequency table is available as `rreb1_haplotype_frequency_summary.csv`.

{markdown_table(hap_preview, max_rows=18)}

## Optional SNPchip coverage

{snpchip_section}

## Practical feasibility summary

The practical feasibility table is available as `rreb1_practical_feasibility_summary.csv`.

{markdown_table(feasibility_df, max_rows=8)}

The available files can support cautious SNP-based feasibility summaries for the published RREB1 SNP tags. They can describe LD, haplotype structure, population differences, and optional array coverage. They cannot establish causality or directly characterize the GGAA microsatellite allele lengths reported in the RREB1 study.

## Possible downstream figures and tables

- LDlinkPy workflow diagram
- ancestry-specific LD matrices or heatmaps for the RREB1 4-SNP set
- haplotype frequency summaries across EUR, AFR, AMR, EAS, and SAS
- tables comparing pairwise LD among published RREB1 SNP tags
- practical SNP-based feasibility table with optional chip coverage

## Limitations

- This report uses only LDlinkPy output files.
- This report does not use external annotations.
- This report does not query RegulomeDB, GTEx, ENCODE, LDexpress, LDtrait, GWAS Catalog, or other outside resources.
- This report does not infer GGAA microsatellite length directly.
- This report does not reproduce targeted long-read sequencing or functional experiments.
- Values depend on the LDlink reference data and the output files generated by the first script.
{warnings_text}
"""
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    input_dir = args.input_dir
    out_dir = args.out_dir or input_dir / DEFAULT_OUT_DIR_NAME
    context = ReportContext(
        input_dir=input_dir,
        out_dir=out_dir,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    files = detect_source_files(input_dir)
    validate_input_files(input_dir, files)
    if args.verbose:
        for kind, paths in files.items():
            print(f"Detected {len(paths)} {kind} file(s)")

    out_dir.mkdir(parents=True, exist_ok=True)
    _ = args.overwrite

    manifest = load_manifest(files["manifest"], context.warnings)
    if manifest and args.verbose:
        print(f"Loaded manifest for {manifest.get('example', 'unknown example')}")

    variant_summary_df = create_variant_summary(files["metadata"], context.warnings)
    pairwise_df = create_pairwise_ld_summary(files["ldpair"], files["ldpop"], context.warnings)
    ldmatrix_index_df, ldmatrix_long_df = create_ldmatrix_summaries(
        files["ldmatrix"],
        context.warnings,
    )
    haplotype_df = create_haplotype_summary(files["ldhap"], context.warnings)
    snpchip_df = create_snpchip_summary(files["snpchip"], context.warnings)
    feasibility_df = create_practical_feasibility_summary(
        pairwise_df,
        ldmatrix_index_df,
        haplotype_df,
        snpchip_df,
    )

    write_csv(variant_summary_df, out_dir / "rreb1_variant_summary.csv", args.verbose)
    write_csv(pairwise_df, out_dir / "rreb1_pairwise_ld_summary.csv", args.verbose)
    write_csv(ldmatrix_index_df, out_dir / "rreb1_ldmatrix_file_index.csv", args.verbose)
    write_csv(
        haplotype_df,
        out_dir / "rreb1_haplotype_frequency_summary.csv",
        args.verbose,
    )
    write_csv(
        feasibility_df,
        out_dir / "rreb1_practical_feasibility_summary.csv",
        args.verbose,
    )
    if ldmatrix_long_df is not None:
        write_csv(
            ldmatrix_long_df,
            out_dir / "rreb1_ldmatrix_long_format.csv",
            args.verbose,
        )
    if snpchip_df is not None:
        write_csv(snpchip_df, out_dir / "rreb1_snpchip_summary.csv", args.verbose)

    write_workflow_diagram(out_dir, args.verbose)

    if args.make_plots:
        make_plots(out_dir, files["ldmatrix"], haplotype_df, context, args.verbose)

    report = create_report(
        context=context,
        files=files,
        variant_summary_df=variant_summary_df,
        pairwise_df=pairwise_df,
        ldmatrix_index_df=ldmatrix_index_df,
        long_matrix_created=ldmatrix_long_df is not None,
        haplotype_df=haplotype_df,
        snpchip_df=snpchip_df,
        feasibility_df=feasibility_df,
    )
    report_path = out_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")
    if args.verbose:
        print(f"Wrote {report_path}")

    print(f"Summary report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
