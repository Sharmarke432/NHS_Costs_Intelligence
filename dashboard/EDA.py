"""Exploratory analysis for NHS National Cost Collection data.

Purpose:
    Create presentation-ready descriptive figures without cleaning or changing
    the source data. The script only filters records for individual analyses,
    reports those choices, and preserves the original dataset.

Usage:
    python nhs_cost_eda.py --input data/processed/your_file.csv --output figures/eda

The script expects columns resembling:
    Provider, Mapping_Pot, Service, Department, Activity, Unit_Cost,
    Actual_Cost, Expected_Cost, Variance, NCCI
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid", context="talk")

MIN_PROVIDER_ACTIVITY = 5
MIN_SERVICE_ACTIVITY = 50
MIN_SERVICE_PROVIDERS = 3
LOWER_QUANTILE = 0.01
UPPER_QUANTILE = 0.99
TOP_N = 15


ALIASES = {
    "provider": ["Provider", "provider", "provider_name"],
    "mapping_pot": ["Mapping_Pot", "mapping_pot", "Mapping Pot"],
    "service": ["Service", "service"],
    "department": ["Department", "department"],
    "activity": ["Activity", "activity"],
    "unit_cost": ["Unit_Cost", "unit_cost", "Unit Cost"],
    "actual_cost": ["Actual_Cost", "actual_cost", "Actual Cost"],
    "expected_cost": ["Expected_Cost", "expected_cost", "Expected Cost"],
    "variance": ["Variance", "variance"],
    "ncci": ["NCCI", "ncci"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the source CSV")
    parser.add_argument("--output", default="figures/eda", help="Output directory")
    return parser.parse_args()


def resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    resolved: dict[str, str] = {}
    lower_columns = {str(column).strip().lower(): column for column in df.columns}
    for standard_name, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in df.columns:
                resolved[standard_name] = candidate
                break
            if candidate.lower() in lower_columns:
                resolved[standard_name] = lower_columns[candidate.lower()]
                break
    required = {"service", "activity", "unit_cost"}
    missing = required - resolved.keys()
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return resolved


def numeric_series(df: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series(index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce")


def safe_filename(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_")
    return text[:80] or "unknown"


def save_figure(fig: plt.Figure, output: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(output / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_csv(df: pd.DataFrame, output: Path, name: str) -> None:
    df.to_csv(output / f"{name}.csv", index=False)


def describe_data(df: pd.DataFrame, columns: dict[str, str], output: Path) -> None:
    summary = {
        "rows": int(len(df)),
        "columns": list(map(str, df.columns)),
        "numeric_summary": {},
        "missing_values": {str(k): int(v) for k, v in df.isna().sum().items()},
        "analysis_thresholds": {
            "min_provider_activity": MIN_PROVIDER_ACTIVITY,
            "min_service_activity": MIN_SERVICE_ACTIVITY,
            "min_service_providers": MIN_SERVICE_PROVIDERS,
            "display_lower_quantile": LOWER_QUANTILE,
            "display_upper_quantile": UPPER_QUANTILE,
        },
    }
    for standard_name, source_column in columns.items():
        series = numeric_series(df, source_column)
        if series.notna().any():
            summary["numeric_summary"][standard_name] = {
                "source_column": source_column,
                "count": int(series.notna().sum()),
                "missing": int(series.isna().sum()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "min": float(series.min()),
                "max": float(series.max()),
                "p01": float(series.quantile(LOWER_QUANTILE)),
                "p99": float(series.quantile(UPPER_QUANTILE)),
                "non_positive": int((series <= 0).sum()),
                "negative": int((series < 0).sum()),
                "zero": int((series == 0).sum()),
            }
    (output / "eda_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def plot_overview_distributions(df: pd.DataFrame, columns: dict[str, str], output: Path) -> None:
    available = [
        key for key in ["activity", "unit_cost", "actual_cost", "expected_cost", "variance", "ncci"]
        if key in columns
    ]
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.ravel()
    for ax, key in zip(axes, available):
        values = numeric_series(df, columns[key]).dropna()
        if not values.empty:
            lower, upper = values.quantile([LOWER_QUANTILE, UPPER_QUANTILE])
            values = values[(values >= lower) & (values <= upper)]
            sns.histplot(values, bins=40, kde=True, ax=ax, color="#3976a5")
            ax.axvline(values.median(), color="black", linestyle="--", linewidth=1.5)
            ax.set_title(f"{key.replace('_', ' ').title()}\n1st–99th percentile")
            ax.set_xlabel(key.replace("_", " ").title())
            ax.set_ylabel("Record count")
    for ax in axes[len(available):]:
        ax.remove()
    fig.suptitle("Distribution overview: descriptive only", y=1.02)
    save_figure(fig, output, "01_distribution_overview")


def build_service_summary(df: pd.DataFrame, c: dict[str, str]) -> pd.DataFrame:
    activity = numeric_series(df, c["activity"])
    unit_cost = numeric_series(df, c["unit_cost"])
    working = pd.DataFrame({
        "service": df[c["service"]].astype(str),
        "activity": activity,
        "unit_cost": unit_cost,
    })
    if "provider" in c:
        working["provider"] = df[c["provider"]].astype(str)
    else:
        working["provider"] = np.nan
    grouped = working.groupby("service", dropna=False)
    summary = grouped.agg(
        total_activity=("activity", "sum"),
        provider_count=("provider", "nunique"),
        record_count=("unit_cost", "count"),
        simple_mean_unit_cost=("unit_cost", "mean"),
        median_unit_cost=("unit_cost", "median"),
        q25_unit_cost=("unit_cost", lambda x: x.quantile(0.25)),
        q75_unit_cost=("unit_cost", lambda x: x.quantile(0.75)),
    ).reset_index()
    weighted = (
        working.assign(weighted_cost=working["unit_cost"] * working["activity"])
        .groupby("service", dropna=False)[["weighted_cost", "activity"]]
        .sum()
        .assign(activity_weighted_unit_cost=lambda x: x["weighted_cost"] / x["activity"])
        [["activity_weighted_unit_cost"]]
        .reset_index()
    )
    summary = summary.merge(weighted, on="service", how="left")
    summary["robust_variation_iqr_over_median"] = np.where(
        summary["median_unit_cost"] != 0,
        (summary["q75_unit_cost"] - summary["q25_unit_cost"]) / summary["median_unit_cost"],
        np.nan,
    )
    return summary


def plot_service_costs(summary: pd.DataFrame, output: Path) -> None:
    eligible = summary[
        (summary["total_activity"] >= MIN_SERVICE_ACTIVITY)
        & (summary["provider_count"] >= MIN_SERVICE_PROVIDERS)
        & summary["activity_weighted_unit_cost"].notna()
    ].copy()
    selected = eligible.nlargest(TOP_N, "activity_weighted_unit_cost").sort_values("activity_weighted_unit_cost")
    write_csv(selected, output, "service_cost_benchmarks_top15")
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.barh(selected["service"], selected["activity_weighted_unit_cost"], color="#3976a5")
    for index, row in enumerate(selected.itertuples()):
        ax.text(row.activity_weighted_unit_cost, index, f"  Activity: {row.total_activity:,.0f}", va="center", fontsize=9)
    ax.set_title("Services with highest activity-weighted reported unit cost")
    ax.set_xlabel("Activity-weighted unit cost (£)")
    ax.set_ylabel("Service")
    save_figure(fig, output, "02_top_services_weighted_cost")


def plot_metric_sensitivity(summary: pd.DataFrame, output: Path) -> None:
    summary = summary.copy()
    summary["metric_gap"] = summary[["simple_mean_unit_cost", "median_unit_cost", "activity_weighted_unit_cost"]].max(axis=1) - summary[["simple_mean_unit_cost", "median_unit_cost", "activity_weighted_unit_cost"]].min(axis=1)
    selected = summary[
        (summary["total_activity"] >= MIN_SERVICE_ACTIVITY)
        & (summary["provider_count"] >= MIN_SERVICE_PROVIDERS)
    ].nlargest(TOP_N, "metric_gap")
    selected = selected.sort_values("metric_gap")
    write_csv(selected, output, "service_metric_sensitivity_top15")
    plot_data = selected.set_index("service")[["simple_mean_unit_cost", "median_unit_cost", "activity_weighted_unit_cost"]]
    fig, ax = plt.subplots(figsize=(15, 10))
    plot_data.plot.barh(ax=ax, color=["#5878a6", "#d28b61", "#5b9b70"])
    ax.set_title("How the choice of cost metric changes the comparison")
    ax.set_xlabel("Unit cost (£)")
    ax.set_ylabel("Service")
    ax.legend(["Simple mean", "Median", "Activity-weighted mean"], title="Cost metric")
    save_figure(fig, output, "03_cost_metric_sensitivity")


def plot_provider_activity(df: pd.DataFrame, c: dict[str, str], output: Path, service: str | None = None) -> None:
    if "provider" not in c:
        return
    selected_service = service or str(df[c["service"]].dropna().iloc[0])
    subset = df[df[c["service"]].astype(str) == selected_service].copy()
    activity = numeric_series(subset, c["activity"])
    unit_cost = numeric_series(subset, c["unit_cost"])
    actual = numeric_series(subset, c.get("actual_cost"))
    plot_data = pd.DataFrame({
        "provider": subset[c["provider"]].astype(str),
        "activity": activity,
        "unit_cost": unit_cost,
        "actual_cost": actual,
    }).dropna(subset=["activity", "unit_cost"])
    plot_data = plot_data[plot_data["activity"] >= MIN_PROVIDER_ACTIVITY]
    if plot_data.empty:
        return
    benchmark = np.average(plot_data["unit_cost"], weights=plot_data["activity"])
    sizes = plot_data["actual_cost"].abs().fillna(1).clip(lower=1)
    size_scale = max(float(sizes.quantile(0.95)), 1.0)
    sizes = 30 + 700 * sizes / size_scale
    sizes = sizes.clip(lower=30, upper=1000)
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.scatter(plot_data["activity"], plot_data["unit_cost"], s=sizes, alpha=0.65, color="#3976a5", edgecolor="white", linewidth=0.5)
    ax.axhline(benchmark, color="red", linestyle="--", label=f"Activity-weighted benchmark: £{benchmark:,.0f}")
    ax.set_xscale("log")
    ax.set_title(f"Provider unit costs become more variable at low activity\n{selected_service}")
    ax.set_xlabel("Provider activity (log scale)")
    ax.set_ylabel("Provider activity-weighted unit cost (£)")
    ax.legend()
    save_figure(fig, output, "04_provider_cost_vs_activity")
    write_csv(plot_data, output, f"provider_cost_activity_{safe_filename(selected_service)}")


def plot_robust_variation(summary: pd.DataFrame, output: Path) -> None:
    selected = summary[
        (summary["total_activity"] >= MIN_SERVICE_ACTIVITY)
        & (summary["provider_count"] >= MIN_SERVICE_PROVIDERS)
        & summary["robust_variation_iqr_over_median"].notna()
        & (summary["median_unit_cost"] > 0)
        & ~summary["service"].str.contains("unknown", case=False, na=False)
    ].nlargest(TOP_N, "robust_variation_iqr_over_median").sort_values("robust_variation_iqr_over_median")
    write_csv(selected, output, "service_robust_variation_top15")
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.barh(selected["service"], selected["robust_variation_iqr_over_median"], color="#9a5b08")
    for index, row in enumerate(selected.itertuples()):
        ax.text(row.robust_variation_iqr_over_median, index, f"  Activity: {row.total_activity:,.0f}; Providers: {row.provider_count:,.0f}", va="center", fontsize=9)
    ax.set_title("Services with greatest relative variation in reported unit cost")
    ax.set_xlabel("IQR / median unit cost")
    ax.set_ylabel("Service")
    save_figure(fig, output, "05_robust_cost_variation")


def plot_ncci(df: pd.DataFrame, c: dict[str, str], output: Path) -> None:
    if "ncci" not in c:
        return
    values = numeric_series(df, c["ncci"]).dropna()
    if values.empty:
        return
    p01, p99 = values.quantile([LOWER_QUANTILE, UPPER_QUANTILE])
    trimmed = values[(values >= p01) & (values <= p99)]
    write_csv(pd.DataFrame({"ncci": values}), output, "ncci_values_audit")
    fig, ax = plt.subplots(figsize=(15, 9))
    sns.histplot(trimmed, bins=45, kde=True, ax=ax, color="#6c4b9e")
    ax.axvline(values.median(), color="black", linestyle="--", label=f"Median: {values.median():,.2f}")
    ax.set_title(f"NCCI distribution: 1st–99th percentile range\nDisplay only; p99 = {p99:,.2f}")
    ax.set_xlabel("NCCI")
    ax.set_ylabel("Record count")
    ax.legend()
    save_figure(fig, output, "06_ncci_trimmed_distribution")
    positive = values[values > 0]
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.hist(positive, bins=np.logspace(np.log10(positive.min()), np.log10(positive.max()), 45), color="#6c4b9e", alpha=0.8)
    ax.set_xscale("log")
    ax.set_title("Positive NCCI values span a wide range\nZero and negative values excluded from this logarithmic view")
    ax.set_xlabel("NCCI (log scale)")
    ax.set_ylabel("Record count")
    save_figure(fig, output, "07_ncci_log_distribution")


def plot_ncci_expected(df: pd.DataFrame, c: dict[str, str], output: Path) -> None:
    if not {"ncci", "expected_cost"}.issubset(c):
        return
    ncci = numeric_series(df, c["ncci"])
    expected = numeric_series(df, c["expected_cost"])
    valid = pd.DataFrame({"ncci": ncci, "expected_cost": expected}).dropna()
    valid = valid[(valid["ncci"] >= 0) & (valid["expected_cost"] > 0)]
    if valid.empty:
        return
    p99 = valid["ncci"].quantile(UPPER_QUANTILE)
    valid["ncci_display"] = valid["ncci"].clip(upper=p99)
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.scatter(valid["expected_cost"], valid["ncci_display"], s=10, alpha=0.18, color="#3976a5")
    ax.set_xscale("log")
    ax.set_title("NCCI dispersion across expected cost\nNCCI capped at p99 for visual clarity")
    ax.set_xlabel("Expected cost (£, log scale)")
    ax.set_ylabel("NCCI (capped at p99)")
    save_figure(fig, output, "08_ncci_vs_expected_cost")


def plot_variance(df: pd.DataFrame, c: dict[str, str], output: Path) -> None:
    if "variance" not in c:
        return
    values = numeric_series(df, c["variance"]).dropna()
    if values.empty:
        return
    lower, upper = values.quantile([LOWER_QUANTILE, UPPER_QUANTILE])
    trimmed = values[(values >= lower) & (values <= upper)]
    fig, ax = plt.subplots(figsize=(15, 9))
    sns.histplot(trimmed, bins=50, ax=ax, color="#4eb39b")
    ax.axvline(0, color="black", linestyle="--", linewidth=1.5, label="Zero: actual cost = expected cost")
    ax.axvline(values.median(), color="red", linestyle="--", label=f"Median: £{values.median():,.0f}")
    ax.set_title("Most records are close to expected cost, but extreme variances remain\nDisplayed between the 1st and 99th percentiles")
    ax.set_xlabel("Variance (£): actual cost − expected cost")
    ax.set_ylabel("Record count")
    ax.legend()
    save_figure(fig, output, "09_variance_distribution")


def plot_mapping_pot(df: pd.DataFrame, c: dict[str, str], output: Path) -> None:
    if "mapping_pot" not in c:
        return
    activity = numeric_series(df, c["activity"])
    unit_cost = numeric_series(df, c["unit_cost"])
    working = pd.DataFrame({"group": df[c["mapping_pot"]].astype(str), "activity": activity, "unit_cost": unit_cost}).dropna()
    grouped = working.assign(weighted=working["activity"] * working["unit_cost"]).groupby("group").agg(total_activity=("activity", "sum"), weighted_cost=("weighted", "sum"), activity_count=("activity", "count"))
    grouped["activity_weighted_unit_cost"] = grouped["weighted_cost"] / grouped["total_activity"]
    grouped = grouped.sort_values("activity_weighted_unit_cost", ascending=False)
    write_csv(grouped.reset_index(), output, "mapping_pot_descriptive_summary")
    fig, ax = plt.subplots(figsize=(15, 9))
    ax2 = ax.twinx()
    bars = ax.bar(grouped.index, grouped["activity_weighted_unit_cost"], color="#3976a5", alpha=0.9)
    ax2.plot(grouped.index, grouped["total_activity"], color="#d16600", marker="o", linewidth=2)
    ax.set_title("Descriptive cost and activity differences across Mapping_Pot groups\nGroups may differ in service mix, provider mix and case complexity")
    ax.set_xlabel("Mapping_Pot group")
    ax.set_ylabel("Activity-weighted unit cost (£)")
    ax2.set_ylabel("Total activity", color="#d16600")
    ax.tick_params(axis="x", rotation=35)
    save_figure(fig, output, "10_mapping_pot_cost_activity")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    columns = resolve_columns(df)
    describe_data(df, columns, output)
    plot_overview_distributions(df, columns, output)

    service_summary = build_service_summary(df, columns)
    write_csv(service_summary, output, "service_summary_descriptive")
    plot_service_costs(service_summary, output)
    plot_metric_sensitivity(service_summary, output)
    plot_robust_variation(service_summary, output)

    plot_provider_activity(df, columns, output)
    plot_ncci(df, columns, output)
    plot_ncci_expected(df, columns, output)
    plot_variance(df, columns, output)
    plot_mapping_pot(df, columns, output)

    print(f"Created exploratory outputs in: {output}")
    print("No source rows were modified or dropped from the loaded dataframe.")
    print("Filters are applied only within individual figures and are documented in eda_summary.json.")


if __name__ == "__main__":
    main()