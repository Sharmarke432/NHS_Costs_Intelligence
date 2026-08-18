from pathlib import Path
import streamlit as st


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NHS Cost Collection: EDA Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
FIGURES_DIR = BASE_DIR / "figures"

FIGURES = {
    "Top services by average unit cost": "top15_services_avg_cost.png",
    "Provider costs vs national average": "provider_vs_national_sample.png",
    "Services with highest cost variation": "top15_cv_services.png",
    "NCCI distribution": "ncci_distribution.png",
    "Average unit cost by MFF group": "mff_impact.png",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def show_figure(title: str, filename: str, explanation: str, interpretation: str, caution: str):
    """Show a saved EDA figure with an explanation and interpretation."""
    st.subheader(title)

    figure_path = FIGURES_DIR / filename
    if figure_path.exists():
        st.image(str(figure_path), use_container_width=True)
    else:
        st.warning(
            f"Figure not found: `{figure_path}`. "
            "Run the EDA script first and ensure the PNG is saved in `figures/`."
        )

    left, right = st.columns(2)
    with left:
        st.markdown("### What this shows")
        st.write(explanation)
    with right:
        st.markdown("### How to interpret it")
        st.write(interpretation)

    st.info(f"**Important caveat:** {caution}")
    st.divider()


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
st.sidebar.title("🏥 NHS Cost EDA")
st.sidebar.markdown("**National Cost Collection 2024/25**")
st.sidebar.markdown(
    "This dashboard presents exploratory analysis of provider and service-level unit costs."
)
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Average service costs",
        "Provider comparison",
        "Cost variation",
        "NCCI distribution",
        "MFF groups",
        "Presentation notes",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("### Data notes")
st.sidebar.markdown(
    "- Costs are shown in GBP (£).\n"
    "- The data is MFF-unadjusted.\n"
    "- High cost does not automatically mean inefficiency.\n"
    "- Results are descriptive, not causal."
)


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------
if page == "Overview":
    st.title("NHS National Cost Collection: EDA Dashboard")
    st.markdown(
        "This dashboard summarises exploratory data analysis of the **2024/25 NHS National Cost Collection** dataset. "
        "It helps identify high-cost services, variation between providers, extreme NCCI values, and differences across MFF-related groups."
    )

    st.subheader("How to use this dashboard")
    st.markdown(
        "Use the navigation menu to view each EDA figure together with a plain-English explanation. "
        "The purpose is to identify patterns and questions for deeper analysis—not to label providers as efficient or inefficient."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Analysis level", "Provider × Service")
    with col2:
        st.metric("Financial year", "2024/25")
    with col3:
        st.metric("Cost basis", "MFF-unadjusted")

    st.subheader("Key questions")
    st.markdown(
        "- Which services have the highest average unit costs?\n"
        "- Which services have the largest differences in cost across providers?\n"
        "- Are there unusual provider-level cost outliers?\n"
        "- Does the NCCI variable contain extreme values requiring validation?\n"
        "- How do average costs differ between the available MFF-related groups?"
    )

    st.warning(
        "Before making benchmarking claims, investigate activity volumes, provider type, patient complexity, service mix, "
        "costing methodology and extreme values."
    )

elif page == "Average service costs":
    st.title("Average Unit Cost by Service")
    show_figure(
        title="Top 15 Services by National Average Unit Cost",
        filename=FIGURES["Top services by average unit cost"],
        explanation=(
            "This horizontal bar chart ranks the 15 services with the highest average unit cost in the dataset. "
            "Each bar represents the average cost of delivering one recorded unit of activity for that service across providers."
        ),
        interpretation=(
            "Old Age Psychiatry is the highest average-cost service shown, at roughly £40,000 per unit in this analysis. "
            "Other high-cost services include Child and Adolescent Psychiatry, cardiothoracic transplantation, and specialist paediatric surgery. "
            "These are clinically complex or specialist services, so high unit cost is expected and is not itself evidence of poor efficiency."
        ),
        caution=(
            "The chart uses unweighted mean unit cost. A service with a few low-volume, high-cost records can have a large mean. "
            "Compare activity volume, median cost and weighted average cost before drawing conclusions."
        ),
    )

elif page == "Provider comparison":
    st.title("Provider Costs vs National Average")
    show_figure(
        title="Provider Unit Costs: Old Age Psychiatry",
        filename=FIGURES["Provider costs vs national average"],
        explanation=(
            "This histogram shows the distribution of provider unit costs for the selected service, Old Age Psychiatry. "
            "The dashed red line represents the average unit cost across the providers in the dataset."
        ),
        interpretation=(
            "The distribution is strongly right-skewed: most observations are at the low end, while a small number are much higher. "
            "Those high-cost observations pull the national average to approximately £39,818. The chart is useful for identifying outliers "
            "that may deserve further review."
        ),
        caution=(
            "Do not assume high-cost providers are inefficient. The values may reflect low activity, specialist case mix, different care models, "
            "or costing/reporting differences. Investigate the underlying activity and actual-cost values first."
        ),
    )

elif page == "Cost variation":
    st.title("Cost Variation by Service")
    show_figure(
        title="Top 15 Services by Coefficient of Variation",
        filename=FIGURES["Services with highest cost variation"],
        explanation=(
            "This chart ranks services by their coefficient of variation (CV), calculated as standard deviation divided by mean unit cost. "
            "A higher CV means provider costs vary more relative to the average cost for that service."
        ),
        interpretation=(
            "The Unknown category has the highest variation, followed by Paediatric Dermatology, Chemical Pathology, Community Dental Services, "
            "Dietetics and Podiatry. These services are candidates for deeper investigation because their costs differ greatly across providers."
        ),
        caution=(
            "High variation is a signal for investigation, not proof of inefficiency. It can be caused by small volumes, patient complexity, "
            "different delivery models, data-quality issues or inconsistent costing. The '999 - Unknown' category should be reviewed separately."
        ),
    )

elif page == "NCCI distribution":
    st.title("NCCI Distribution")
    show_figure(
        title="Distribution of National Cost Collection Index",
        filename=FIGURES["NCCI distribution"],
        explanation=(
            "This histogram displays the spread of NCCI values across the dataset. NCCI is intended to compare costs relative to an expected or benchmark cost."
        ),
        interpretation=(
            "The figure is extremely right-skewed. Most values cluster close to zero on this scale, while a small number of very large values stretch the x-axis. "
            "This suggests that extreme observations are dominating the visualisation."
        ),
        caution=(
            "Validate the definition and scale of NCCI in this file before interpreting it as an efficiency measure. Check minimum, maximum, median, "
            "the 99th percentile, zero values and whether very small expected costs create artificially large ratios. A log-scale or percentile-trimmed chart would be clearer."
        ),
    )

elif page == "MFF groups":
    st.title("Average Unit Cost by MFF Group")
    show_figure(
        title="Average Unit Cost by MFF-Related Group",
        filename=FIGURES["Average unit cost by MFF group"],
        explanation=(
            "This bar chart compares average unit costs across the `Mapping_Pot` groups in the data. "
            "It provides a descriptive view of how recorded costs differ across the available MFF-related categories."
        ),
        interpretation=(
            "The groups labelled `02_NEI` and `01_EI` show the highest average unit costs in this analysis, while categories such as `10_PAR`, `11_A&E` and `05_OP` are lower. "
            "This indicates meaningful differences between groups, potentially due to service mix, location-related pressures or the way activity is grouped."
        ),
        caution=(
            "`Mapping_Pot` is not necessarily a binary MFF indicator. This chart does not prove that MFF causes the cost differences; it does not control for service type, provider type, activity or patient complexity."
        ),
    )

elif page == "Presentation notes":
    st.title("Mentor Presentation Notes")

    st.subheader("Suggested opening")
    st.markdown(
        "> “I conducted exploratory analysis on the 2024/25 NHS National Cost Collection data at provider and service level. "
        "The goal was to identify high-cost services, services with large cost variation between providers, and data patterns that need deeper validation before benchmarking.”"
    )

    st.subheader("Headline findings")
    st.markdown(
        "1. Specialist mental-health, transplant and paediatric surgery services have the highest average unit costs.\n"
        "2. Several services show substantial provider-level variation, especially Paediatric Dermatology, Chemical Pathology and Community Dental Services.\n"
        "3. Old Age Psychiatry has a right-skewed provider-cost distribution, with a few very high values affecting the average.\n"
        "4. NCCI has extreme values, so it needs data validation before being used for efficiency conclusions.\n"
        "5. Average costs differ across the available Mapping_Pot/MFF-related groups, but this is descriptive rather than causal."
    )

    st.subheader("Important limitations")
    st.markdown(
        "- A high cost may be clinically appropriate for complex care.\n"
        "- Mean unit cost can be distorted by outliers and low-volume records.\n"
        "- Provider comparisons should account for activity volume, case mix and provider type.\n"
        "- The current data is MFF-unadjusted.\n"
        "- The `999 - Unknown` service category requires data-quality review."
    )

    st.subheader("Recommended next steps")
    st.markdown(
        "1. Add activity-volume thresholds before ranking providers or services.\n"
        "2. Calculate median, weighted mean and percentile-based unit costs.\n"
        "3. Investigate extreme NCCI values and document the NCCI calculation.\n"
        "4. Segment providers into comparable groups before benchmarking.\n"
        "5. Build interactive filters around provider, department, service, activity and cost metrics."
    )

st.caption("Data source: NHS National Cost Collection 2024/25. This dashboard is exploratory and should not be used as a standalone performance assessment.")