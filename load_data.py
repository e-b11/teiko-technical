import os
import sqlite3
import pandas as pd

#Task 1

csv_file = "cell-count.csv"
df = pd.read_csv(csv_file)

db_file = "cell-count.db"
if os.path.exists(db_file):
    os.remove(db_file)
conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()


#Tables

#Projects
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS projects ( 
  project_id INTEGER PRIMARY KEY, 
  project_name TEXT NOT NULL UNIQUE 
) 
""")

#Subjects
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS subjects ( 
  subject_id INTEGER PRIMARY KEY, 
  project_id INTEGER NOT NULL, 
  subject_name TEXT NOT NULL, 
  condition TEXT, 
  age INTEGER, 
  sex TEXT, 
  
  FOREIGN KEY (project_id) 
    REFERENCES projects(project_id), 
    
  UNIQUE (project_id, subject_name) 
) 
""")

#Treatments
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS treatments ( 
  treatment_id INTEGER PRIMARY KEY, 
  subject_id INTEGER NOT NULL, 
  treatment TEXT NOT NULL, 
  response TEXT, 
  
  FOREIGN KEY (subject_id) 
    REFERENCES subjects(subject_id), 
    
  UNIQUE (subject_id, treatment) 
) 
""")

#Samples
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS samples ( 
  sample_id INTEGER PRIMARY KEY, 
  subject_id INTEGER NOT NULL, 
  sample_name TEXT NOT NULL, 
  sample_type TEXT, 
  time_from_treatment_start REAL, 
  
  FOREIGN KEY (subject_id) 
    REFERENCES subjects(subject_id), 
    
  UNIQUE (subject_id, sample_name) 
) 
""")

# Cell measurements
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS cell_measurements ( 
  measurement_id INTEGER PRIMARY KEY, 
  sample_id INTEGER NOT NULL, 
  measurement TEXT NOT NULL,
  count INTEGER,
  
  FOREIGN KEY (sample_id) 
    REFERENCES samples(sample_id), 
    
  UNIQUE (sample_id, measurement) 
) 
""")

conn.commit()

#Load in data from dataframe

#Projects
for project_name in df["project"].unique():

    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (project_name)
        VALUES (?)
        """,
        (project_name,)
    )

#Subjects
for _, row in df.iterrows():

    cursor.execute(
        """
        INSERT OR IGNORE INTO subjects (
            project_id,
            subject_name,
            condition,
            age,
            sex
        )
        SELECT
            project_id,
            ?,
            ?,
            ?,
            ?
        FROM projects
        WHERE project_name = ?
        """,
        (
            row["subject"],
            row["condition"],
            row["age"],
            row["sex"],
            row["project"]
        )
    )

#Treatments
for _, row in df.iterrows():

    cursor.execute(
        """
        INSERT OR IGNORE INTO treatments (
            subject_id,
            treatment,
            response
        )
        SELECT
            subject_id,
            ?,
            ?
        FROM subjects
        JOIN projects
            ON subjects.project_id = projects.project_id
        WHERE subjects.subject_name = ?
          AND projects.project_name = ?
        """,
        (
            row["treatment"],
            row["response"],
            row["subject"],
            row["project"]
        )
    )


#Samples
for _, row in df.iterrows():

    cursor.execute(
        """
        INSERT OR IGNORE INTO samples (
            subject_id,
            sample_name,
            sample_type,
            time_from_treatment_start
        )
        SELECT
            subject_id,
            ?,
            ?,
            ?
        FROM subjects
        JOIN projects
            ON subjects.project_id = projects.project_id
        WHERE subjects.subject_name = ?
          AND projects.project_name = ?
        """,
        (
            row["sample"],
            row["sample_type"],
            row["time_from_treatment_start"],
            row["subject"],
            row["project"]
        )
    )

#Cell measurements

measurements = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte"
]

for _, row in df.iterrows():

    for measurement in measurements:

        cursor.execute(
            """
            INSERT OR IGNORE INTO cell_measurements (
                sample_id,
                measurement,
                count
            )
            SELECT
                samples.sample_id,
                ?,
                ?
            FROM samples
            JOIN subjects
                ON samples.subject_id = subjects.subject_id
            JOIN projects
                ON subjects.project_id = projects.project_id
            WHERE samples.sample_name = ?
              AND subjects.subject_name = ?
              AND projects.project_name = ?
            """,
            (
                measurement,
                row[measurement],
                row["sample"],
                row["subject"],
                row["project"]
            )
        )

conn.commit()

conn.close()

print(f"Successfully converted {csv_file} to {db_file}!")