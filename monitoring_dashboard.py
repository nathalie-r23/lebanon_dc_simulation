import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Lebanon Data Center Simulation", layout="wide")

# -----------------------------
# GLOBAL STYLE (fonts + layout)
# -----------------------------
st.markdown("""
<style>

/* General font size */
html, body, [class*="css"] {
    font-size: 16px;
}

/* Titles */
h1 {font-size: 32px !important;}
h2 {font-size: 26px !important;}
h3 {font-size: 20px !important;}

/* Metric numbers */
[data-testid="stMetricValue"] {
    font-size: 24px !important;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    font-size: 14px !important;
}

/* Sidebar smaller text so it fits */
section[data-testid="stSidebar"] * {
    font-size: 14px !important;
}

section[data-testid="stSidebar"] label {
    font-size: 13px !important;
}

/* Reduce spacing between sidebar elements */
section[data-testid="stSidebar"] .stSlider {
    margin-bottom: 6px !important;
}

/* Improve tab visibility */
button[data-baseweb="tab"] {
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* Highlight active tab */
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid #ff4b4b !important;
}

/* Mobile adjustments */
@media (max-width: 768px) {

    h1 {font-size: 26px !important;}
    h2 {font-size: 22px !important;}
    h3 {font-size: 18px !important;}

    [data-testid="stMetricValue"] {
        font-size: 20px !important;
    }

}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Title
# -----------------------------
st.title("Lebanon Data Center Power Outage Simulation")

st.write(
"""
This interactive dashboard demonstrates how different data center strategies
perform during a power outage in Lebanon.

The goal is to understand which infrastructure approach provides the
highest resilience under unstable electricity conditions.
"""
)

st.info(
"Main idea: when electricity fails in Lebanon, local infrastructure must rely on "
"UPS batteries, generators, and fuel. Strategies less dependent on local power "
"tend to be more resilient."
)

st.markdown("---")

# -----------------------------
# Sidebar controls
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
1,
180,
60
)

generator_start_delay = st.sidebar.slider(
"Generator Startup Delay (minutes)",
1,
20,
5
)

generator_failure = st.sidebar.checkbox(
"Simulate Generator Failure",
False
)

initial_fuel = st.sidebar.slider(
"Available Generator Fuel (%)",
0,
100,
80
)

fuel_price_factor = st.sidebar.slider(
"Fuel Price Stress Factor",
1.0,
3.0,
1.5,
0.1
)

# -----------------------------
# Strategy parameters
# -----------------------------
if scenario == "New Tier III in Lebanon":
    ups_capacity = 15
    fuel_rate = 0.7
    exposure = "High"
    cloud_resilience = False
    note = "Strong infrastructure but still dependent on Lebanese power and fuel logistics."

elif scenario == "Expand Existing Facility":
    ups_capacity = 8
    fuel_rate = 1.0
    exposure = "High"
    cloud_resilience = False
    note = "Lower upfront cost but higher operational vulnerability."

elif scenario == "Colocation Facility":
    ups_capacity = 10
    fuel_rate = 0.6
    exposure = "Medium"
    cloud_resilience = False
    note = "Shared infrastructure reduces operational burden."

else:
    ups_capacity = 5
    fuel_rate = 0.3
    exposure = "Low"
    cloud_resilience = True
    note = "Main infrastructure hosted outside Lebanon."

# -----------------------------
# Simulation logic
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
# Tabs navigation
# -----------------------------
#st.markdown("### 👇 Click the sections below to explore the simulation")

tab1, tab2, tab3 = st.tabs([
"📊 Overview",
"🔎 Detailed Results",
"📘 Assumptions"
])

# -----------------------------
# TAB 1
# -----------------------------
with tab1:

    st.subheader("Simulation Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric("Outage Duration", f"{outage_duration} min")
    c2.metric("UPS Backup", f"{ups_capacity} min")
    c3.metric("Fuel Available", f"{initial_fuel}%")

    st.write(note)

    if downtime == 0:
        st.success("Service stayed online during the outage.")
        risk = "Low"
    elif downtime < 5:
        st.warning("Short service disruption occurred.")
        risk = "Medium"
    else:
        st.error("Major service disruption occurred.")
        risk = "High"

    st.metric("Total Downtime", f"{downtime} minutes")
    st.metric("Operational Risk", risk)

# -----------------------------
# TAB 2
# -----------------------------
with tab2:

    st.subheader("Incident Timeline")

    st.write(
"""
1. Power grid fails  
2. UPS supplies temporary power  
3. Generator attempts to start  
4. Generator takes over or fails  
"""
)

    col1, col2 = st.columns(2)

    with col1:

        fig1, ax1 = plt.subplots()
        ax1.plot(df["Minute"], df["UPS Remaining (min)"])
        ax1.set_title("UPS Battery Over Time")
        ax1.set_xlabel("Minute")
        ax1.set_ylabel("Minutes Remaining")
        st.pyplot(fig1)

    with col2:

        fig2, ax2 = plt.subplots()
        ax2.plot(df["Minute"], df["Fuel Remaining (%)"])
        ax2.set_title("Fuel Level Over Time")
        ax2.set_xlabel("Minute")
        ax2.set_ylabel("Fuel (%)")
        st.pyplot(fig2)

    with st.expander("Show detailed simulation table"):
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download results",
            csv,
            "simulation_results.csv",
            "text/csv"
        )

# -----------------------------
# TAB 3
# -----------------------------
with tab3:

    st.subheader("Model Assumptions")

    assumptions = pd.DataFrame({

"Assumption":[
"Grid outage starts at minute 1",
"UPS provides short-term backup",
"Generator consumes fuel while running",
"Cloud-first infrastructure remains operational outside Lebanon"
],

"Purpose":[
"Simulate outage event",
"Model battery backup behavior",
"Represent generator fuel dependence",
"Represent external hosting resilience"
]

})

    st.dataframe(assumptions)

    st.subheader("Conclusion")

    st.success(
"""
Strategies that rely heavily on local electricity and generators
face higher operational risk in Lebanon.

Cloud-first approaches reduce exposure to local infrastructure
instability and generally offer stronger resilience.
"""
)
