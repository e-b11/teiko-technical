import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu
import os


DB_FILE = "cell-count.db"
OUTPUT_DIR = "outputs"
PLOT_DIR = "outputs/plots"

def create_summary(conn):

    query = """
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
    ORDER BY samples.sample_name, cell_measurements.measurement
    """

    summary = pd.read_sql_query(query, conn)

    print("\n=== SUMMARY TABLE ===")
    print(summary)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    summary.to_csv(
        f"{OUTPUT_DIR}/summary.csv",
        index=False
    )

    return summary

#Task 3

def response_analysis(conn, summary):

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

    analysis_df = summary.merge(
        metadata,
        on="sample"
    )

    analysis_df = analysis_df[
        (analysis_df["condition"] == "melanoma") &
        (analysis_df["treatment"] == "miraclib") &
        (analysis_df["sample_type"] == "PBMC")
    ].copy()

    print("\n=== RESPONSE ANALYSIS DATA ===")
    print(analysis_df)

    os.makedirs(PLOT_DIR, exist_ok=True)

    plt.figure(figsize=(12, 6))

    sns.boxplot(
        data=analysis_df,
        x="population",
        y="percentage",
        hue="response"
    )

    plt.xlabel("Immune Cell Population")
    plt.ylabel("Relative Frequency (%)")
    plt.title(
        "Cell Population Relative Frequencies: "
        "Responders vs Non-Responders"
    )

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        f"{PLOT_DIR}/response_boxplot.png",
        dpi=300
    )

    plt.close()

    populations = analysis_df["population"].unique()

    results = []

    for population in populations:

        responder = analysis_df[
            (analysis_df["population"] == population) &
            (analysis_df["response"] == "yes")
        ]["percentage"]

        non_responder = analysis_df[
            (analysis_df["population"] == population) &
            (analysis_df["response"] == "no")
        ]["percentage"]

        statistic, p_value = mannwhitneyu(
            responder,
            non_responder,
            alternative="two-sided"
        )

        results.append({
            "population": population,
            "responder_median": responder.median(),
            "non_responder_median": non_responder.median(),
            "U_statistic": statistic,
            "p_value": p_value
        })

    stats_df = pd.DataFrame(results)

    print("\n=== STATISTICS ===")
    print(stats_df)

    stats_df.to_csv(
        f"{OUTPUT_DIR}/response_statistics.csv",
        index=False
    )

#Task 4

def baseline_analysis(conn):

    subset_query = """
    SELECT
        projects.project_name AS project,
        subjects.subject_id,
        subjects.subject_name AS subject,
        treatments.treatment,
        treatments.response,
        subjects.sex,
        samples.sample_id,
        samples.sample_name AS sample,
        samples.sample_type,
        samples.time_from_treatment_start
    FROM samples
    JOIN subjects
        ON samples.subject_id = subjects.subject_id
    JOIN projects
        ON subjects.project_id = projects.project_id
    JOIN treatments
        ON subjects.subject_id = treatments.subject_id
    WHERE subjects.condition = 'melanoma'
      AND samples.sample_type = 'PBMC'
      AND samples.time_from_treatment_start = 0
      AND treatments.treatment = 'miraclib'
    """

    baseline_df = pd.read_sql_query(
        subset_query,
        conn
    )

    print("\n=== BASELINE DATA ===")
    print(baseline_df)

    baseline_df.to_csv(
        f"{OUTPUT_DIR}/baseline.csv",
        index=False
    )

    project_counts = (
        baseline_df
        .groupby("project")["sample_id"]
        .nunique()
        .reset_index(name="sample_count")
    )

    print("\n=== PROJECT COUNTS ===")
    print(project_counts)

    response_counts = (
        baseline_df
        .groupby("response")["subject_id"]
        .nunique()
        .reset_index(name="subject_count")
    )

    print("\n=== RESPONSE COUNTS ===")
    print(response_counts)

    sex_counts = (
        baseline_df
        .groupby("sex")["subject_id"]
        .nunique()
        .reset_index(name="subject_count")
    )

    print("\n=== SEX COUNTS ===")
    print(sex_counts)

    b_cell_query = """
    SELECT
        AVG(cell_measurements.count) AS average_b_cells
    FROM cell_measurements
    JOIN samples
        ON cell_measurements.sample_id = samples.sample_id
    JOIN subjects
        ON samples.subject_id = subjects.subject_id
    JOIN projects
        ON subjects.project_id = projects.project_id
    JOIN treatments
        ON subjects.subject_id = treatments.subject_id
    WHERE subjects.condition = 'melanoma'
      AND subjects.sex = 'M'
      AND treatments.response = 'yes'
      AND samples.time_from_treatment_start = 0
      AND cell_measurements.measurement = 'b_cell'
    """

    result = pd.read_sql_query(
        b_cell_query,
        conn
    )

    average_b_cells = result.iloc[0]["average_b_cells"]

    print(
        f"\nAverage number of B cells: "
        f"{average_b_cells:.2f}"
    )

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PLOT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)

    summary = create_summary(conn)

    response_analysis(
        conn,
        summary
    )

    baseline_analysis(conn)

    conn.close()

    print("\nAnalysis completed successfully!")


if __name__ == "__main__":
    main()