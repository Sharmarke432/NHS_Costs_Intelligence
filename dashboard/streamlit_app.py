from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="What Can NHS Cost Data Tell Us?",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent.parent
FIGURES_DIR = BASE_DIR / "Figures"

FIGURES = {
    "Activity-weighted service costs": {
        "file": "02_top_services_weighted_cost.jpg",
        "description": (
            "Services with the highest activity-weighted reported unit cost. "
            "This is a descriptive cost benchmark, not an efficiency ranking."
        ),
    },
    "Distribution overview": {
        "file": "01_distribution_overview.jpg",
        "description": (
            "Activity, unit cost, actual cost, expected cost, variance and NCCI "
            "are strongly skewed and contain influential extreme observations."
        ),
    },
    "Cost-metric sensitivity": {
        "file": "03_cost_metric_sensitivity.jpg",
        "description": (
            "Service comparisons change depending on whether the simple mean, "
            "median or activity-weighted mean is used."
        ),
    },
    "Provider cost versus activity": {
        "file": "04_provider_cost_vs_activity.jpg",
        "description": (
            "Lower-activity providers show greater reported cost variability. "
            "Potential outliers require investigation rather than automatic judgement."
        ),
    },
    "Robust relative cost variation": {
        "file": "05_robust_cost_variation.jpg",
        "description": (
            "Relative variation is measured using IQR divided by the median, "
            "reducing sensitivity to extreme values."
        ),
    },
    "Trimmed NCCI distribution": {
        "file": "06_ncci_trimmed_distribution.jpg",
        "description": (
            "The 1st–99th percentile display shows the typical NCCI range. "
            "Extreme values should remain available for audit."
        ),
    },
    "Positive NCCI on a log scale": {
        "file": "07_ncci_log_distribution.jpg",
        "description": (
            "Positive NCCI values span several orders of magnitude. "
            "Zero and negative values require separate validation."
        ),
    },
    "NCCI versus expected cost": {
        "file": "08_ncci_vs_expected_cost.jpg",
        "description": (
            "NCCI appears more dispersed at lower expected costs, suggesting "
            "a possible denominator or small-volume effect."
        ),
    },
    "Variance distribution": {
        "file": "09_variance_distribution.jpg",
        "description": (
            "Most records are close to zero variance, but substantial positive "
            "and negative tails remain."
        ),
    },
    "Mapping_Pot comparison": {
        "file": "10_mapping_pot_cost_activity.jpg",
        "description": (
            "Mapping_Pot groups differ in cost and total activity. This is a "
            "descriptive comparison and does not establish a causal MFF effect."
        ),
    },
}


@st.cache_data
def figure_path(filename: str) -> Path:
    return FIGURE_DIR / filename


def render_figure(name: str) -> None:
    figure = FIGURES[name]
    path = figure_path(figure["file"])

    if path.exists():
        st.image(str(path), use_container_width=True)
        st.caption(figure["description"])
    else:
        st.error(f"Figure not found: {path}")
        st.code(f"Place the image at figures/{figure['file']}")


def render_disclaimer() -> None:
    st.warning(
        "This dashboard presents descriptive evidence. It does not establish "
        "provider efficiency, causality or poor performance. High cost and high "
        "variation should be treated as signals for further investigation."
    )


st.title("What Can NHS Cost Data Tell Us About Variation in Service Costs?")
st.markdown(
    "**NHS National Cost Collection 2024/25**  \n"
    "An exploratory analysis of activity-weighted benchmarks, provider variation, "
    "cost metrics and NCCI distributions."
)

with st.sidebar:
    st.header("Dashboard navigation")
    page = st.radio(
        "Go to",
        [
            "Overview",
            "Service costs",
            "Provider variation",
            "NCCI and variance",
            "Mapping_Pot groups",
            "Evidence and limitations",
        ],
    )

    st.divider()
    st.caption("Data scope")
    st.write("Cleaned NCC 2024/25 data")
    st.write("MFF-unadjusted")
    st.write("Approximately 38,562 numeric records")

if page == "Overview":
    st.header("Overview")
    st.write(
        "This dashboard investigates how reported NHS service costs vary across "
        "services, providers and descriptive grouping variables. It focuses on "
        "robust summaries rather than relying on simple means alone."
    )

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Numeric records", "~38,562")
    metric_2.metric("Median NCCI", "96")
    metric_3.metric("NCCI p99", "~419")
    metric_4.metric("Median variance", "−£3,295")

    st.subheader("Questions explored")
    questions = [
        "Which services have the highest activity-weighted reported unit costs?",
        "How much do service comparisons change when the cost metric changes?",
        "Does reported provider cost become more variable at low activity?",
        "Which services show the greatest relative variation?",
        "How dispersed are NCCI and actual-versus-expected cost values?",
        "How do Mapping_Pot groups differ descriptively in cost and activity?",
    ]
    for question in questions:
        st.markdown(f"- {question}")

    st.subheader("Main descriptive findings")
    findings = [
        "Activity, cost and NCCI distributions are strongly right-skewed.",
        "Simple means can be substantially different from medians and activity-weighted means.",
        "Low-activity providers tend to have more unstable reported unit costs.",
        "Specialist services often appear among high-cost or high-variation categories.",
        "NCCI has a long right tail and needs validation before being used as an efficiency measure.",
    ]
    for finding in findings:
        st.markdown(f"- {finding}")

    render_disclaimer()

elif page == "Service costs":
    st.header("Service cost benchmarks")
    st.write(
        "These figures compare reported service costs using activity-weighted "
        "benchmarks and show how the choice of metric changes the comparison."
    )

    tabs = st.tabs(["Weighted costs", "Metric sensitivity", "Distributions"])
    with tabs[0]:
        render_figure("Activity-weighted service costs")
    with tabs[1]:
        render_figure("Cost-metric sensitivity")
    with tabs[2]:
        render_figure("Distribution overview")

    st.subheader("Interpretation")
    st.write(
        "Activity-weighted cost is the preferred high-level benchmark because it "
        "reflects the contribution of activity volume. The median remains useful "
        "for describing a typical provider-record observation. A simple mean is "
        "best treated as a diagnostic because extreme values can dominate it."
    )
    render_disclaimer()

elif page == "Provider variation":
    st.header("Provider activity and cost variation")
    st.write(
        "The provider-level figure examines whether reported unit costs become "
        "more dispersed when providers have low activity."
    )

    render_figure("Provider cost versus activity")
    render_figure("Robust relative cost variation")

    st.subheader("Interpretation")
    st.write(
        "The figures suggest that low activity is associated with greater cost "
        "instability. This is consistent with a denominator effect, where a small "
        "number of cases can substantially change a reported unit cost. It does "
        "not demonstrate that higher-cost providers are inefficient."
    )
    render_disclaimer()

elif page == "NCCI and variance":
    st.header("NCCI and actual-versus-expected cost")
    st.write(
        "This section treats NCCI and variance as validation and diagnostic "
        "variables rather than direct efficiency scores."
    )

    tabs = st.tabs(["NCCI distribution", "NCCI scale", "NCCI and expected cost", "Variance"])
    with tabs[0]:
        render_figure("Trimmed NCCI distribution")
    with tabs[1]:
        render_figure("Positive NCCI on a log scale")
    with tabs[2]:
        render_figure("NCCI versus expected cost")
    with tabs[3]:
        render_figure("Variance distribution")

    st.subheader("Interpretation")
    st.write(
        "NCCI has a typical central range but a long positive tail. The wider "
        "dispersion at lower expected costs suggests that small denominators may "
        "contribute to unstable index values. This hypothesis requires validation "
        "using the underlying formula and record-level data."
    )

    st.subheader("Validation checks required")
    checks = [
        "Confirm the exact NCCI formula and scale.",
        "Count missing, zero and negative NCCI values.",
        "Review the highest NCCI records individually.",
        "Assess sensitivity to small expected costs.",
        "Reconcile Actual_Cost, Expected_Cost and Variance definitions.",
    ]
    for check in checks:
        st.markdown(f"- {check}")
    render_disclaimer()

elif page == "Mapping_Pot groups":
    st.header("Descriptive Mapping_Pot comparison")
    st.write(
        "This figure compares activity-weighted unit cost and total activity across "
        "Mapping_Pot groups. Differences should be interpreted descriptively only."
    )

    render_figure("Mapping_Pot comparison")

    st.subheader("What may explain group differences?")
    explanations = [
        "Different service mixes.",
        "Different provider mixes.",
        "Differences in patient complexity.",
        "Regional or organisational variation.",
        "Different activity distributions.",
        "Cost allocation and reporting differences.",
    ]
    for explanation in explanations:
        st.markdown(f"- {explanation}")

    st.info(
        "Mapping_Pot is used here as a descriptive grouping variable. The figure "
        "does not establish that an MFF-related factor causes the observed cost differences."
    )

elif page == "Evidence and limitations":
    st.header("Evidence and limitations")

    st.subheader("Conclusions supported by the figures")
    supported = [
        "Reported NHS cost variables are highly skewed and contain extreme observations.",
        "Cost comparisons are sensitive to the chosen summary statistic.",
        "Activity-weighted benchmarks and medians are more informative than simple means alone.",
        "Low-activity provider costs appear more variable.",
        "NCCI has a long right tail and appears more dispersed at lower expected costs.",
    ]
    for item in supported:
        st.markdown(f"- {item}")

    st.subheader("Conclusions not supported by the figures")
    unsupported = [
        "That a high-cost service or provider is inefficient.",
        "That high variation proves poor performance.",
        "That Mapping_Pot differences represent a causal MFF effect.",
        "That raw NCCI rankings are validated efficiency scores.",
        "That negative or extreme values are necessarily genuine clinical costs.",
    ]
    for item in unsupported:
        st.markdown(f"- {item}")

    st.subheader("Data-quality issues to review")
    quality_items = [
        "Negative Unit_Cost and Actual_Cost values.",
        "Zero or negative NCCI values.",
        "Very small Expected_Cost denominators.",
        "Extreme NCCI and cost observations.",
        "The 999 - Unknown service category.",
        "Differences between weighted Unit_Cost and Actual_Cost divided by Activity.",
    ]
    for item in quality_items:
        st.markdown(f"- {item}")

    st.subheader("Presentation-ready conclusion")
    st.success(
        "The analysis shows that reported NHS service costs vary substantially and "
        "that comparisons are sensitive to activity volume and the selected cost "
        "metric. Activity-weighted and robust measures provide more informative "
        "descriptive benchmarks than simple means alone. However, specialist case "
        "mix, provider context and data-quality issues mean that high cost or high "
        "variation cannot be interpreted as inefficiency. NCCI has a long right tail "
        "and requires further validation before it can be used as an efficiency "
        "measure. The figures therefore identify areas for investigation rather than "
        "making provider-performance judgements."
    )

    render_disclaimer()

st.divider()
st.caption(
    "Exploratory analysis only | NHS NCC 2024/25 | Validate data definitions and account for case mix before making stronger claims"
)
st.caption("Data source: NHS National Cost Collection 2024/25. This dashboard is exploratory and should not be used as a standalone performance assessment.")
