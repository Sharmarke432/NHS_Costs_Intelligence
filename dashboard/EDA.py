import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


# Paths
PROC = Path("data/processed")
FIGS = Path("figures")
PROC.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)


# ---- Load cleaned data ----
print(f"Looking for CSV files in: {PROC.absolute()}")
csv_files = list(PROC.glob("*.csv"))
print(f"Found {len(csv_files)} CSV file(s):")
for f in csv_files:
    print(f"  - {f.name}")

if len(csv_files) == 0:
    raise FileNotFoundError(f"No CSV files found in {PROC}. Please place your cleaned data file there.")

# Use the first CSV file found
data_file = csv_files[0]
print(f"\nLoading data from: {data_file.name}")

df = pd.read_csv(data_file)


# ---- Map to your actual column names ----
# Based on your columns:
# Index(['Provider', 'Mapping_Pot', 'Service', 'Department', 'Activity',
#        'Unit_Cost', 'Actual_Cost', 'Expected_Cost', 'Variance', 'NCCI',
#        'Variance_Percent'], dtype='object')

provider = 'Provider'
service = 'Service'
activity = 'Activity'
unit_cost = 'Unit_Cost'
total_cost = 'Actual_Cost'  # or 'Expected_Cost' depending on your preference
ncci = 'NCCI'
mff = 'Mapping_Pot'  # This might be your MFF flag

print(f"\n=== Column Mapping ===")
print(f"Provider: {provider}")
print(f"Service: {service}")
print(f"Activity: {activity}")
print(f"Unit Cost: {unit_cost}")
print(f"Total Cost: {total_cost}")
print(f"NCCI: {ncci}")
print(f"MFF: {mff}")


# ---- National averages by service ----
print("\n=== National Averages by Service ===")
service_avg = (
    df.groupby(service)
    .agg(
        national_avg_unit_cost=(unit_cost, "mean"),
        median_unit_cost=(unit_cost, "median"),
        total_activity=(activity, "sum"),
        total_cost=(total_cost, "sum"),
        providers_count=(provider, "nunique"),
    )
    .sort_values("national_avg_unit_cost", ascending=False)
    .reset_index()
)
service_avg.to_csv(PROC / "service_avg.csv", index=False)
print(f"✓ Service averages saved: {service_avg.shape}")
print(service_avg.head(10))


# ---- Provider-level summaries ----
print("\n=== Provider-Level Summaries ===")
provider_summary = (
    df.groupby([provider])
    .agg(
        total_activity=(activity, "sum"),
        avg_unit_cost=(unit_cost, "mean"),
        services_count=(service, "nunique"),
        total_cost=(total_cost, "sum"),
    )
    .reset_index()
)
provider_summary.to_csv(PROC / "provider_summary.csv", index=False)
print(f"✓ Provider summaries saved: {provider_summary.shape}")
print(provider_summary.head())


# ---- Variation analysis: coefficient of variation by service ----
print("\n=== Cost Variation by Service ===")
cv_by_service = (
    df.groupby(service)
    .agg(
        mean_cost=(unit_cost, "mean"),
        std_cost=(unit_cost, "std"),
    )
    .assign(cv=lambda d: d["std_cost"] / d["mean_cost"])
    .sort_values("cv", ascending=False)
    .reset_index()
)
cv_by_service.to_csv(PROC / "cv_by_service.csv", index=False)
print(f"✓ Cost variation saved: {cv_by_service.shape}")
print(cv_by_service.head(10))


# ---- NCCI distribution ----
print("\n=== NCCI Distribution ===")
ncci_dist = df[ncci].describe()
print(ncci_dist)


# ---- MFF impact ----
print("\n=== MFF Impact ===")
mff_impact = (
    df.groupby(mff)
    .agg(avg_unit_cost=(unit_cost, "mean"), rows=(unit_cost, "count"))
    .reset_index()
)
mff_impact.to_csv(PROC / "mff_impact.csv", index=False)
print(f"✓ MFF impact saved: {mff_impact.shape}")
print(mff_impact)


# ---- Provider vs national average comparison ----
print("\n=== Provider vs National Average ===")
df_with_nat = df.merge(
    service_avg[[service, "national_avg_unit_cost"]],
    on=service,
    suffixes=("", "_national")
)
df_with_nat["cost_diff"] = df_with_nat[unit_cost] - df_with_nat["national_avg_unit_cost"]
df_with_nat["cost_diff_pct"] = (df_with_nat["cost_diff"] / df_with_nat["national_avg_unit_cost"]) * 100
df_with_nat.to_csv(PROC / "schedule_with_comparison.csv", index=False)
print(f"✓ Provider vs national comparison saved: {df_with_nat.shape}")


# ---- Figures ----
print("\n=== Generating Figures ===")
sns.set_style("whitegrid")


# 1) Top 15 services by national average unit cost
plt.figure(figsize=(10, 6))
top15 = service_avg.head(15)
sns.barplot(data=top15, x="national_avg_unit_cost", y=service)
plt.title("Top 15 Services by National Average Unit Cost (2024/25)")
plt.xlabel("Average Unit Cost (£)")
plt.ylabel("Service")
plt.tight_layout()
plt.savefig(FIGS / "top15_services_avg_cost.png", dpi=150)
plt.close()
print("✓ Saved: top15_services_avg_cost.png")


# 2) NCCI distribution histogram
plt.figure(figsize=(8, 5))
sns.histplot(df[ncci].dropna(), bins=50, kde=True)
plt.title("Distribution of National Cost Collection Index (NCCI)")
plt.xlabel("NCCI Score")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(FIGS / "ncci_distribution.png", dpi=150)
plt.close()
print("✓ Saved: ncci_distribution.png")


# 3) Provider vs national average for a sample service
sample_service = service_avg.iloc[0][service]
sample_rows = df[df[service] == sample_service]
nat_avg = sample_rows[unit_cost].mean()

plt.figure(figsize=(8, 5))
sns.histplot(sample_rows[unit_cost], bins=40, kde=True)
plt.axvline(nat_avg, color="red", linestyle="--", label=f"National Avg: £{nat_avg:,.0f}")
plt.title(f"Provider Unit Costs vs National Average: {sample_service[:50]}")
plt.xlabel("Unit Cost (£)")
plt.ylabel("Count")
plt.legend()
plt.tight_layout()
plt.savefig(FIGS / "provider_vs_national_sample.png", dpi=150)
plt.close()
print("✓ Saved: provider_vs_national_sample.png")


# 4) Coefficient of variation by service (top 15 most variable)
plt.figure(figsize=(10, 6))
top15_cv = cv_by_service.head(15)
sns.barplot(data=top15_cv, x="cv", y=service)
plt.title("Top 15 Services by Cost Variation (Coefficient of Variation)")
plt.xlabel("Coefficient of Variation")
plt.ylabel("Service")
plt.tight_layout()
plt.savefig(FIGS / "top15_cv_services.png", dpi=150)
plt.close()
print("✓ Saved: top15_cv_services.png")


# 5) MFF impact
plt.figure(figsize=(6, 5))
sns.barplot(data=mff_impact, x=mff, y="avg_unit_cost")
plt.title("Average Unit Cost by MFF Flag")
plt.xlabel("MFF Flag")
plt.ylabel("Average Unit Cost (£)")
plt.tight_layout()
plt.savefig(FIGS / "mff_impact.png", dpi=150)
plt.close()
print("✓ Saved: mff_impact.png")


print("\n" + "="*50)
print("EDA COMPLETE")
print("="*50)
print(f"Summary tables saved to: {PROC}")
print(f"Figures saved to: {FIGS}")