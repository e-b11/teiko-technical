import sqlite3
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt


# Page title
st.title("Cell Count Dashboard")

st.write(
    "Explore immune cell populations across samples."
)

conn = sqlite3.connect("cell-count.db")


#Summary
summary_query = """
SELECT
    samples.sample_name AS sample,
    SUM(cell_measurements.count) OVER (
        PARTITION BY cell_measurements.sample_id
    ) AS total_count,
    cell_measurements.measurement AS population,
    cell_measurements.count AS count,
    ROUND(
        cell_measurements.count * 100.0 /
        SUM(cell_measurements.count) OVER (
            PARTITION BY cell_measurements.sample_id
        ),
        2
    ) AS percentage
FROM cell_measurements
JOIN samples
    ON cell_measurements.sample_id = samples.sample_id
"""

summary = pd.read_sql_query(
    summary_query,
    conn
)


#Metadata
metadata_query = """
SELECT
    samples.sample_name AS sample,
    projects.project_name AS project,
    subjects.subject_name AS subject,
    subjects.condition AS condition,
    treatments.treatment,
    treatments.response,
    samples.sample_type
FROM samples
JOIN subjects
    ON samples.subject_id = subjects.subject_id
JOIN projects
    ON subjects.project_id = projects.project_id
JOIN treatments
    ON subjects.subject_id = treatments.subject_id
"""

metadata = pd.read_sql_query(
    metadata_query,
    conn
)

conn.close()

data = summary.merge(
    metadata,
    on="sample"
)


#Filters
st.sidebar.header("Filters")

projects = st.sidebar.multiselect(
    "Project",
    options=sorted(data["project"].unique()),
    default=sorted(data["project"].unique())
)

treatments = st.sidebar.multiselect(
    "Treatment",
    options=sorted(data["treatment"].unique()),
    default=sorted(data["treatment"].unique())
)

responses = st.sidebar.multiselect(
    "Response",
    options=sorted(data["response"].dropna().unique()),
    default=sorted(data["response"].dropna().unique())
)

sample_types = st.sidebar.multiselect(
    "Sample Type",
    options=sorted(data["sample_type"].unique()),
    default=sorted(data["sample_type"].unique())
)

conditions = st.sidebar.multiselect(
    "Condition",
    options=sorted(data["condition"].unique()),
    default=sorted(data["condition"].unique())
)


# Apply filters
filtered_data = data[
    data["project"].isin(projects) &
    data["treatment"].isin(treatments) &
    data["response"].isin(responses) &
    data["sample_type"].isin(sample_types) &
    data["condition"].isin(conditions)
]


# Summary table

st.header("Cell Population Summary")

st.dataframe(
    filtered_data[
        [
            "sample",
            "total_count",
            "population",
            "count",
            "percentage"
        ]
    ],
    width="stretch"
)


# Boxplot

st.header("Cell Population Frequencies")

if not filtered_data.empty:

    fig, ax = plt.subplots(figsize=(12, 6))

    sns.boxplot(
        data=filtered_data,
        x="population",
        y="percentage",
        hue="response",
        ax=ax
    )

    ax.set_xlabel("Immune Cell Population")
    ax.set_ylabel("Relative Frequency (%)")
    ax.set_title(
        "Cell Population Relative Frequencies"
    )

    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

else:
    st.warning("No data match the selected filters.")