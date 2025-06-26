
import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Executive Operations Dashboard", layout="wide")

st.title("📊 Executive Operations Dashboard")

uploaded_file1 = st.file_uploader("Upload Construction File", type=["xlsx"], key="file1")
uploaded_file2 = st.file_uploader("Upload Talley File", type=["xlsx"], key="file2")

if uploaded_file1:
    df_construction = pd.read_excel(uploaded_file1)
    df_construction["Date"] = pd.to_datetime(df_construction["Date"], errors="coerce")

    st.subheader("🔧 Construction Overview")

    st.subheader("🔗 Open Full Construction Dashboard")
    st.markdown(
        '[🛠️ Click here to open the full construction dashboard](https://pwnconstruction.streamlit.app/)',
        unsafe_allow_html=True
    )


    def get_work_type(desc):
        if pd.isna(desc): return "Unknown"
        if "Strand" in desc: return "Strand"
        elif "Fiber($0.02)" in desc: return "Fiber Pull"
        elif "Lashed" in desc: return "Lashing"
        return "Other"

    df_construction["Work Type"] = df_construction["What did you do."].apply(get_work_type)

    techs = df_construction["Who filled this out?"].dropna().unique()
    tech_filter = st.multiselect("Filter by Tech", techs, default=techs)
    date_min, date_max = df_construction["Date"].min(), df_construction["Date"].max()
    date_range = st.date_input("Select Date Range", [date_min, date_max])
    df_filtered = df_construction[
        (df_construction["Who filled this out?"].isin(tech_filter)) &
        (df_construction["Date"] >= pd.to_datetime(date_range[0])) &
        (df_construction["Date"] <= pd.to_datetime(date_range[1]))
    ]

    footage_bonus = {
        "Strand": 0.02,
        "Fiber Pull": 0.02,
        "Lashing": 0.02
    }
    df_filtered["Bonus"] = df_filtered["Work Type"].apply(lambda wt: footage_bonus.get(wt, 0.0) * 1000)

    st.metric("Total Construction Records", len(df_filtered))
    st.metric("Estimated Bonus", f"${df_filtered['Bonus'].sum():,.2f}")

    df_filtered["Week"] = df_filtered["Date"].dt.to_period("W").astype(str)
    weekly_summary = df_filtered.groupby(["Week", "Work Type"]).size().reset_index(name="Count")
    st.subheader("📆 Weekly Construction Trends")
    week_chart = alt.Chart(weekly_summary).mark_bar().encode(
        x="Week", y="Count", color="Work Type"
    ).properties(width=900)
    st.altair_chart(week_chart)

    st.subheader("📋 Construction Drill-down Filters")

    # Employee/Status filters (based on available columns)
    available_techs = df_filtered["Who filled this out?"].dropna().unique()
    selected_tech = st.selectbox("Filter by Technician", ["All"] + list(available_techs))

    if selected_tech != "All":
        df_filtered = df_filtered[df_filtered["Who filled this out?"] == selected_tech]

    # Group by Technician (if not already filtered)
    st.subheader("👷 Bonus by Technician")
    tech_group = df_filtered.groupby("Who filled this out?")["Bonus"].sum().reset_index()
    tech_group.columns = ["Technician", "Total Bonus"]
    st.dataframe(tech_group)

    # Optional grouping by Work Type
    st.subheader("📌 Work Type Breakdown")
    worktype_group = df_filtered["Work Type"].value_counts().reset_index()
    worktype_group.columns = ["Work Type", "Count"]
    st.dataframe(worktype_group)

    # Export current drill-down
    csv_filtered_construction = df_filtered.to_csv(index=False).encode()
    st.download_button("Download Filtered Construction Drill-down", csv_filtered_construction, "construction_drilldown.csv", "text/csv")


    bonus_summary = df_filtered.groupby("Who filled this out?")["Bonus"].sum().reset_index()
    bonus_summary.columns = ["Technician", "Total Bonus"]
    st.subheader("👷 Per-Tech Bonus Breakdown")
    st.dataframe(bonus_summary)
    bonus_csv = bonus_summary.to_csv(index=False).encode()
    st.download_button("Download Per-Tech Bonus", bonus_csv, "bonus_by_tech.csv", "text/csv")

    if "Project or labor?" in df_filtered.columns:
        project_summary = df_filtered.groupby("Project or labor?")["Bonus"].sum().reset_index()
        st.subheader("📁 Project-Level Rollups")
        st.dataframe(project_summary)
        project_csv = project_summary.to_csv(index=False).encode()
        st.download_button("Download Project Rollups", project_csv, "project_rollup.csv", "text/csv")

    st.subheader("📋 Construction Detail Table")
    st.dataframe(df_filtered)
    csv = df_filtered.to_csv(index=False).encode()
    st.download_button("Download Filtered Construction Data", csv, "construction_filtered.csv", "text/csv")

if uploaded_file2:

    employees = df_talley["Employee"].dropna().unique()
    emp_filter = st.multiselect("Filter by Employee", employees, default=employees)
    date_min2, date_max2 = df_talley["Date"].min(), df_talley["Date"].max()
    date_range2 = st.date_input("Select Talley Date Range", [date_min2, date_max2], key="talley_date")

    df_tfiltered = df_talley[
        (df_talley["Employee"].isin(emp_filter)) &
        (df_talley["Date"] >= pd.to_datetime(date_range2[0])) &
        (df_talley["Date"] <= pd.to_datetime(date_range2[1]))
    ]

    df_tfiltered["Month"] = df_tfiltered["Date"].dt.to_period("M").astype(str)
    available_months = sorted(df_tfiltered["Month"].dropna().unique())
    selected_months = st.multiselect("Filter by Month", available_months, default=available_months)
    df_tfiltered = df_tfiltered[df_tfiltered["Month"].isin(selected_months)]

    st.metric("Total Talley Records", len(df_tfiltered))
    if "MRC" in df_tfiltered.columns:
        df_tfiltered["MRC"] = pd.to_numeric(df_tfiltered["MRC"], errors="coerce")
        st.metric("Total MRC", f"${df_tfiltered['MRC'].sum():,.2f}")
    else:
        st.warning("MRC column not found in Talley data.")

    if "Reason" in df_tfiltered.columns:
        reason_grouped = df_tfiltered["Reason"].value_counts().reset_index()
        reason_grouped.columns = ["Reason", "Count"]
        st.subheader("📊 Reason Breakdown")
        reason_chart = alt.Chart(reason_grouped).mark_bar().encode(
            x="Reason", y="Count"
        ).properties(width=800)
        st.altair_chart(reason_chart)

        total_reason_mrc = df_tfiltered.groupby("Reason")["MRC"].sum(numeric_only=True).reset_index()
        total_reason_mrc.columns = ["Reason", "Total MRC"]
        st.dataframe(total_reason_mrc)

        # Drill-down filters
        selected_reason = st.selectbox("Drill down by Reason", ["All"] + list(reason_grouped["Reason"]))
        selected_status = st.selectbox("Drill down by Status", ["All"] + list(df_tfiltered["Status"].dropna().unique()))
        selected_employee = st.selectbox("Drill down by Employee", ["All"] + list(df_tfiltered["Employee"].dropna().unique()))

        if selected_reason != "All":
            df_tfiltered = df_tfiltered[df_tfiltered["Reason"] == selected_reason]
        if selected_status != "All":
            df_tfiltered = df_tfiltered[df_tfiltered["Status"] == selected_status]
        if selected_employee != "All":
            df_tfiltered = df_tfiltered[df_tfiltered["Employee"] == selected_employee]

    if "Category" in df_tfiltered.columns:
        mrc_chart_data = df_tfiltered.groupby("Category")["MRC"].sum().reset_index()
        mrc_chart = alt.Chart(mrc_chart_data).mark_bar().encode(
            x="Category", y="MRC"
        ).properties(width=600)
        st.altair_chart(mrc_chart)

    reason_chart_data = df_tfiltered["Status"].value_counts().reset_index()
    reason_chart_data.columns = ["Status", "Count"]
    chart2 = alt.Chart(reason_chart_data).mark_bar().encode(
        x="Status", y="Count"
    ).properties(width=600)
    st.altair_chart(chart2)

    st.subheader("📋 Talley Detail Table")
    st.dataframe(df_tfiltered)
    csv2 = df_tfiltered.to_csv(index=False).encode()
    st.download_button("Download Filtered Talley Data", csv2, "talley_filtered.csv", "text/csv")

if uploaded_file1 and uploaded_file2:
    st.subheader("📈 Combined Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Construction Records", len(df_filtered))
        st.metric("Bonus Total", f"${df_filtered['Bonus'].sum():,.2f}")
    with col2:
        st.metric("Talley Records", len(df_tfiltered))
        if "MRC" in df_tfiltered.columns:
            st.metric("Talley MRC", f"${df_tfiltered['MRC'].sum():,.2f}")


# Placeholder for future: Scheduled reporting automation
# You could use Streamlit's scheduling with cron + cloud storage + PDF export
st.markdown("📬 **Scheduled Reports** (coming soon: auto-generated PDF or email summaries)")
