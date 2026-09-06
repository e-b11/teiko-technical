# Teiko Technical

## How to Run
I have included a Makefile for running the following commands:  

`make setup`: Installs the necessary packages from `requirements.txt`  

`make pipeline`: Runs `load_data.py` to create the database and `analysis.py` for the different data analysis tasks  

`make dashboard`: Starts the Streamlit dashboard at http://localhost:8501/

## Database Schema
The database schema has five tables: projects, subjects, samples, treatments, and cell_measurements. I chose this structure so that as that database needed to be scaled, 
there would be fewer duplicates since not all of the data would need its own row. Especially with each project having many subjects, samples, and treatments, it seemed necessary to
move them into their own tables. I also put cell_measurements into its own table since each sample requires multiple measurements. This data is stored in a long format, with columns
for the measurement_id, sample_id, measurement, and count. This will also work well in the future if different measurements need to be used without having to totally change the format of the table. 

The different tables are also helpful for future analytics since there are foreign keys to be able to join the tables together if necessary depending on which projects or samples are needed. 

## Code Structure
The structure of the code is fairly straightforward. `load_data.py` creates the database, transforms the CSV data, and loads it into the correct tables. `analysis.py` contains functions for the different tasks to generate the necessary tables and plots, and saves them in the `outputs` directory. `dashboard.py` uses Streamlit to create an interactive dashboard with various filters to look at the summary data. I designed it that way so that it would still be readable for looking at the different tasks for the data analysis and still easy to run using the Makefile. 

## Dashboard
Streamlit runs the dashboard on a local server at http://localhost:8501/
