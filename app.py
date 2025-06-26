
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
    df_talley = pd.read_excel(uploaded_file2)
    df_talley["Date"] = pd.to_datetime(df_talley["Date"], errors="coerce")

    st.subheader("📦 Talley Status Overview")

    employees = df_talley["Employee"].dropna().unique()
    emp_filter = st.multiselect("Filter by Employee", employees, default=employees)
    date_min2, date_max2 = df_talley["Date"].min(), df_talley["Date"].max()
    date_range2 = st.date_input("Select Talley Date Range", [date_min2, date_max2], key="talley_date")

    df_tfiltered = df_talley[
        (df_talley["Employee"].isin(emp_filter)) &
        (df_talley["Date"] >= pd.to_datetime(date_range2[0])) &
        (df_talley["Date"] <= pd.to_datetime(date_range2[1]))
    ]

    st.metric("Total Talley Records", len(df_tfiltered))
    if "MRC" in df_tfiltered.columns:
        df_tfiltered["MRC"] = pd.to_numeric(df_tfiltered["MRC"], errors="coerce")
        st.metric("Total MRC", f"${df_tfiltered['MRC'].sum():,.2f}")
    else:
        st.warning("MRC column not found in Talley data.")

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
