#Task 2

import sqlite3
import pandas as pd

db_file = "cell-count.db"
conn = sqlite3.connect(db_file)

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

print(summary)

#Task 3

metadata_query = """
SELECT
    samples.sample_name AS sample,
    projects.project_name AS project,
    subjects.subject_name AS subject,
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

metadata = pd.read_sql_query(metadata_query, conn)

analysis_df = summary.merge(
    metadata,
    on="sample"
)

# analysis_df = analysis_df[
#     (analysis_df["project"] == "melanoma") &
#     (analysis_df["treatment"] == "miraclib") &
#     (analysis_df["sample_type"] == "PBMC")
# ]

print(analysis_df)

conn.close()