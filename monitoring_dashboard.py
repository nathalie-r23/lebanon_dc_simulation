import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Lebanon Data Center Simulation", layout="wide")


# -----------------------------
# UI STYLE IMPROVEMENTS
# -----------------------------
st.markdown("""
<style>

/* Increase normal text readability */
html, body, [class*="css"]  {
    font-size: 18px;
}

/* Make titles slightly bigger */
h1 {
    font-size: 36px !important;
}

h2 {
    font-size: 28px !important;
}

h3 {
    font-size: 22px !important;
}

/* Reduce metric numbers (they are too big by default) */
[data-testid="stMetricValue"] {
    font-size: 28px !important;
}

/* Make metric labels readable */
[data-testid="stMetricLabel"] {
    font-size: 16px !important;
}

/* Improve paragraph readability */
p {
    font-size: 18px;
}

/* Improve sidebar readability */
section[data-testid="stSidebar"] * {
    font-size: 16px;
}

/* Make layout nicer on phones */
@media (max-width: 768px) {

    h1 {
        font-size: 28px !important;
    }

    h2 {
        font-size: 24px !important;
    }

    h3 {
        font-size: 20px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 24px !important;
    }

    p {
        font-size: 16px;
    }

}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# Title + intro
# -----------------------------
st.title("Lebanon Data Center Power Outage Simulation")

st.write(
    """
This dashboard helps explain how different data center strategies perform during a power outage in Lebanon.

It compares four strategies:
- **New Tier III Data Center**
- **Expand Existing Facility**
- **Colocation Facility**
- **Cloud-First Strategy**

The goal is to show which strategy is more resilient when local electricity fails.
"""
)

st.info(
    "Main idea: if Lebanon's electricity fails, local infrastructure depends on UPS batteries, "
    "generators, and fuel. Strategies that depend less on local power are usually more resilient."
)

st.markdown("---")

# -----------------------------
# Sidebar inputs
# -----------------------------
st.sidebar.header("Choose the Simulation Scenario")

scenario = st.sidebar.selectbox(
    "Infrastructure Strategy",
    [
        "New Tier III in Lebanon",
        "Expand Existing Facility",
        "Colocation Facility",
        "Cloud-First Strategy"
    ]
)

outage_duration = st.sidebar.slider(
    "Grid Outage Duration (minutes)",
    min_value=1,
    max_value=180,
    value=60,
    help="How long the Lebanese power grid is unavailable."
)

generator_start_delay = st.sidebar.slider(
    "Generator Startup Delay (minutes)",
    min_value=1,
    max_value=20,
    value=5,
    help="How many minutes the generator takes to start after the outage begins."
)

generator_failure = st.sidebar.checkbox(
    "Simulate generator failure",
    value=False
)

initial_fuel = st.sidebar.slider(
    "Available Generator Fuel (%)",
    min_value=0,
    max_value=100,
    value=80
)

fuel_price_factor = st.sidebar.slider(
    "Fuel Price Stress Factor",
    min_value=1.0,
    max_value=3.0,
    value=1.5,
    step=0.1,
    help="Higher values represent higher fuel-cost pressure in Lebanon."
)

# -----------------------------
# Scenario parameters
# -----------------------------
if scenario == "New Tier III in Lebanon":
    ups_capacity = 15
    fuel_rate = 0.7
    local_exposure = "High"
    cloud_resilience = False
    scenario_note = (
        "This option has stronger backup design and better resilience, "
        "but it still depends heavily on Lebanese electricity, generators, and fuel."
    )

elif scenario == "Expand Existing Facility":
    ups_capacity = 8
    fuel_rate = 1.0
    local_exposure = "High"
    cloud_resilience = False
    scenario_note = (
        "This option is cheaper upfront, but it is more vulnerable because older or weaker "
        "local infrastructure may have less redundancy."
    )

elif scenario == "Colocation Facility":
    ups_capacity = 10
    fuel_rate = 0.6
    local_exposure = "Medium"
    cloud_resilience = False
    scenario_note = (
        "This option shares infrastructure responsibility with a third-party provider. "
        "It is usually more resilient than managing a weak local facility yourself."
    )

else:
    ups_capacity = 5
    fuel_rate = 0.3
    local_exposure = "Low"
    cloud_resilience = True
    scenario_note = (
        "This option hosts the main infrastructure outside Lebanon, so local power outages "
        "have much less effect on core service availability."
    )

# -----------------------------
# Simulation
# -----------------------------
time_points = []
grid_status = []
ups_remaining = []
generator_status = []
fuel_remaining = []
server_status = []

ups_left = float(ups_capacity)
fuel_left = float(initial_fuel)
downtime = 0

for minute in range(outage_duration + 1):
    time_points.append(minute)

    if minute == 0:
        grid = "ON"
        generator = "OFF"
        server = "NORMAL"
    else:
        grid = "OFF"

        if cloud_resilience:
            if minute <= generator_start_delay:
                generator = "STARTING"
            else:
                generator = "FAILED" if generator_failure else "ON"

            server = "NORMAL"

            if not generator_failure and minute > generator_start_delay and fuel_left > 0:
                fuel_left -= fuel_rate
                if fuel_left < 0:
                    fuel_left = 0

        else:
            if minute <= generator_start_delay:
                generator = "STARTING"
                ups_left -= 1

                if ups_left > 0:
                    server = "AT RISK"
                else:
                    server = "DOWN"
                    downtime += 1
            else:
                if generator_failure:
                    generator = "FAILED"
                    ups_left -= 1

                    if ups_left > 0:
                        server = "AT RISK"
                    else:
                        server = "DOWN"
                        downtime += 1
                else:
                    if fuel_left > 0:
                        generator = "ON"
                        fuel_left -= fuel_rate
                        if fuel_left < 0:
                            fuel_left = 0
                        server = "NORMAL"
                    else:
                        generator = "FAILED"
                        server = "DOWN"
                        downtime += 1

    grid_status.append(grid)
    generator_status.append(generator)
    ups_remaining.append(max(ups_left, 0))
    fuel_remaining.append(max(fuel_left, 0))
    server_status.append(server)

df = pd.DataFrame({
    "Minute": time_points,
    "Grid": grid_status,
    "UPS Remaining (min)": ups_remaining,
    "Generator": generator_status,
    "Fuel Remaining (%)": fuel_remaining,
    "Server Status": server_status
})

# -----------------------------
# Result interpretation
# -----------------------------
if downtime == 0:
    operational_risk = "Low"
    plain_result = "The service stayed online during the outage."
elif downtime < 5:
    operational_risk = "Medium"
    plain_result = "There was a short service disruption."
else:
    operational_risk = "High"
    plain_result = "There was a major service disruption."

risk_score = 0

if outage_duration >= 60:
    risk_score += 30
elif outage_duration >= 30:
    risk_score += 20
else:
    risk_score += 10

if initial_fuel <= 30:
    risk_score += 30
elif initial_fuel <= 60:
    risk_score += 20
else:
    risk_score += 10

if generator_failure:
    risk_score += 30
else:
    risk_score += 10

if scenario == "Expand Existing Facility":
    risk_score += 15
elif scenario == "New Tier III in Lebanon":
    risk_score += 10
elif scenario == "Colocation Facility":
    risk_score += 8
else:
    risk_score += 5

risk_score = min(risk_score, 100)

if risk_score <= 30:
    risk_text = "Low"
elif risk_score <= 60:
    risk_text = "Moderate"
elif risk_score <= 80:
    risk_text = "High"
else:
    risk_text = "Critical"

if scenario == "Cloud-First Strategy":
    recommendation_text = "Best resilience under Lebanese grid instability."
    recommendation_type = "success"
elif scenario == "Colocation Facility":
    recommendation_text = "Good compromise between resilience and control."
    recommendation_type = "info"
elif scenario == "New Tier III in Lebanon":
    recommendation_text = "Works well only if backup systems perform correctly."
    recommendation_type = "warning"
else:
    recommendation_text = "Higher operational risk under Lebanese power instability."
    recommendation_type = "error"

# -----------------------------
# Top summary card
# -----------------------------
st.subheader("Current Scenario Summary")

st.write(f"**Selected strategy:** {scenario}")
st.write(f"**Why it matters:** {scenario_note}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Outage Duration", f"{outage_duration} min")
c2.metric("Generator Delay", f"{generator_start_delay} min")
c3.metric("Fuel Available", f"{initial_fuel}%")
c4.metric("Local Exposure", local_exposure)

st.markdown("---")

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["Overview", "Detailed Results", "Assumptions"])

# =============================
# TAB 1 - OVERVIEW
# =============================
with tab1:
    st.subheader("Overall Result")

    a1, a2, a3 = st.columns(3)
    a1.metric("Downtime", f"{downtime} min")
    a2.metric("Operational Risk", operational_risk)
    a3.metric("Lebanon Risk Score", f"{risk_score}/100")

    if downtime == 0:
        st.success(plain_result)
    elif downtime < 5:
        st.warning(plain_result)
    else:
        st.error(plain_result)

    if recommendation_type == "success":
        st.success(f"Recommendation: {recommendation_text}")
    elif recommendation_type == "info":
        st.info(f"Recommendation: {recommendation_text}")
    elif recommendation_type == "warning":
        st.warning(f"Recommendation: {recommendation_text}")
    else:
        st.error(f"Recommendation: {recommendation_text}")

    st.subheader("Simple Explanation of What Happened")
    st.write(
        f"""
- The power grid failed after the simulation started.
- The system then depended on **UPS batteries** and the **generator**.
- The selected strategy was **{scenario}**.
- Final result: **{plain_result}**
- Final fuel remaining: **{fuel_left:.1f}%**
"""
    )

    st.subheader("Status Legend")
    st.write(
        """
- **Grid ON** = utility electricity available  
- **Grid OFF** = power outage  
- **Generator STARTING** = backup generator is not ready yet  
- **Generator ON** = backup generator is supplying power  
- **Generator FAILED** = backup generator did not start  
- **Server NORMAL** = service available  
- **Server AT RISK** = service still on, but dependent on backup  
- **Server DOWN** = service interrupted
"""
    )

    st.subheader("Quick Strategy Comparison")
    comparison_df = pd.DataFrame({
        "Strategy": ["New Tier III", "Expand Existing", "Colocation", "Cloud-First"],
        "Dependence on Local Power": ["High", "High", "Medium", "Low"],
        "Expected Resilience": ["High if backup works", "Low-Moderate", "Moderate-High", "High"],
        "Main Weakness": [
            "Fuel and generator dependence",
            "Weaker local resilience",
            "Still partly locally exposed",
            "Possible regulation / latency constraints"
        ]
    })
    st.dataframe(comparison_df, use_container_width=True)

# =============================
# TAB 2 - DETAILED RESULTS
# =============================
with tab2:
    st.subheader("Incident Timeline")
    st.write(
        """
1. Grid outage begins  
2. UPS immediately supports the load  
3. Generator attempts to start  
4. If generator starts in time, service stabilizes  
5. If generator fails or fuel runs out, service may go down
"""
    )

    st.subheader("Event Summary")
    event_log = []

    if outage_duration > 0:
        event_log.append("Minute 1: Utility grid outage begins.")

    event_log.append(
        f"Minute 1 to {generator_start_delay}: UPS supports the IT load while generator startup is in progress."
    )

    if generator_failure:
        event_log.append("The generator failed to start.")
    else:
        event_log.append(f"At minute {generator_start_delay + 1}, the generator starts successfully.")

    if fuel_left <= 0 and scenario != "Cloud-First Strategy":
        event_log.append("Fuel is depleted, so generator support cannot continue.")

    if downtime == 0:
        event_log.append("The service remained online during the whole event.")
    elif downtime < 5:
        event_log.append("A short interruption occurred.")
    else:
        event_log.append("A major interruption occurred.")

    for event in event_log:
        st.write(f"- {event}")

    st.subheader("Charts")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig1, ax1 = plt.subplots()
        ax1.plot(df["Minute"], df["UPS Remaining (min)"])
        ax1.set_xlabel("Minute")
        ax1.set_ylabel("UPS Remaining (min)")
        ax1.set_title("UPS Backup Over Time")
        st.pyplot(fig1)

    with col_chart2:
        fig2, ax2 = plt.subplots()
        ax2.plot(df["Minute"], df["Fuel Remaining (%)"])
        ax2.set_xlabel("Minute")
        ax2.set_ylabel("Fuel Remaining (%)")
        ax2.set_title("Fuel Level Over Time")
        st.pyplot(fig2)

    st.subheader("Final Status")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Grid", df["Grid"].iloc[-1])
    s2.metric("UPS Left", f"{df['UPS Remaining (min)'].iloc[-1]:.1f} min")
    s3.metric("Generator", df["Generator"].iloc[-1])
    s4.metric("Server", df["Server Status"].iloc[-1])

    with st.expander("Show minute-by-minute simulation table"):
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name="lebanon_dc_simulation_results.csv",
            mime="text/csv"
        )

    st.subheader("Presentation Comparison Table")
    scenario_summary = pd.DataFrame({
        "Test Scenario": ["1-hour outage", "2-hour outage", "Generator failure"],
        "New Tier III": ["Low-Medium risk", "Medium risk", "High risk"],
        "Expand Existing": ["Medium risk", "High risk", "Critical risk"],
        "Colocation": ["Low-Medium risk", "Medium risk", "Medium-High risk"],
        "Cloud-First": ["Low risk", "Low risk", "Low risk"]
    })
    st.table(scenario_summary)

# =============================
# TAB 3 - ASSUMPTIONS
# =============================
with tab3:
    st.subheader("Assumptions Used in This Simulation")

    assumptions_df = pd.DataFrame({
        "Assumption": [
            "Grid outage starts at minute 1",
            "UPS supports the servers before generator takeover",
            "Generator consumes fuel while operating",
            "Cloud-first keeps core compute available during local Lebanese outages",
            "New Tier III has the strongest local backup design",
            "Expand Existing has weaker local resilience",
            "Colocation has medium local exposure"
        ],
        "Why This Assumption Was Used": [
            "To simulate a clear outage event",
            "To model short-term battery backup",
            "To reflect backup dependency on fuel",
            "To represent external cloud hosting resilience",
            "To represent stronger engineered redundancy",
            "To represent weaker local infrastructure",
            "To represent a compromise option"
        ]
    })

    st.dataframe(assumptions_df, use_container_width=True)

    st.subheader("Economic Interpretation")
    operating_stress = initial_fuel * fuel_rate * fuel_price_factor
    st.metric("Backup Power Cost Stress Indicator", f"{operating_stress:.1f}")
    st.write(
        """
This is a simple indicator of how stressful backup power operation becomes when:
- fuel use is high
- fuel prices are volatile
- the strategy depends heavily on local generators

Higher values suggest more operating pressure under Lebanese conditions.
"""
    )

    st.subheader("Final Engineering Conclusion")
    st.success(
        """
Under Lebanese conditions, strategies that depend heavily on local electricity
usually face higher operational risk.

Cloud-first reduces dependence on local grid instability the most.
Colocation can also be a strong compromise when some hosted infrastructure control is needed.
"""
    )