This md file is a summary of whats done for this task, things to improve upon and how to run the project.

Note this project is not vibe coded, AI was used for sure in certain areas but not as a "here's the requirements go do this and that". All the decisions made are my own and most of the code is written or at the very least cleaned up and completely adjusted by me.

Another note regarding automated testing, honestly it'll take a lot more time to finish doing unit, integration and end to end tests. I do have the knowledge to do testing in all its forms so maybe we can discuss that during the interview.

One last note, if you rerun docker then make sure you clear the cookies for airflow otherwise it will give you internal server error.

# Summary
The entire system is built using python and docker, it is a scraper that scrapes the website https://www.workplacerelations.ie and stores the data in mongoDB and minio then transforms the data and stores it in another bucket in minio.

The system runs airflow for orchestration. Now the orchestrator uses BashOperator to run the python scripts, this is not ideal in a production environment but due to time constraints it was not possible to implement a more complex system. (A better way is to call external cloud functions, or maybe host the python script in a container and call it from airflow... There are many other ways to run this).

The environment variables are pushed through example.env as is since this should run locally with ease and its only a task made for local testing.

Now to get into more detials about the system components:

## Scraper
The scraper is made with python, it takes the following arguments:

- q: search query
- from_date: from date (dd/mm/yyyy)
- to_date: to date (dd/mm/yyyy)
- bodies: comma-separated list of bodies (more about how the body filter works below)
- debug: enable debug logging

To run the scraper, use the following command:

```bash
python -m src.main --q "search query" --from_date "dd/mm/yyyy" --to_date "dd/mm/yyyy" --bodies "body1,body2,body3" --debug
```

### Body Filter
The body values are 4 in this website:

- Employment Appeals Tribunal
- Equality Tribunal
- Labour Court
- Workplace Relations Commission


For each body filter specified, the scraper will run a separate spider for it in parallel.

If a document has 2 body filters only one record will be created but it will have both body filters in the body_filters field.

### Saving Records
After the search query is done the spider will find the items and extract all the data required from each item into the following record format:

- url: the url of the item
- ref_number: the reference number of the item
- published_date: timestamp of when the item was published
- description: the description of the item
- partition_date: the partition date
- scraped_at: timestamp of when the item was scraped
- body_filters: the body filters the item appeared in
- additional_files: the additional files of the item (in case there are nested links in the page)

The record is then saved in mongodb and the file is saved to minio (similar to s3).

No record is saved twice, if the record already exists it will not be saved again. (based on ref_number or url)

The file is saved into the following path: files/partition_date/published_date/ref_number/

The reason the file is saved in a directory of ref_number is that we might have multiple files inside it related to that main file in case its an html file (for example attachments, nested links etc...).

## Transformer
The transformer is a separate python script that takes the data from mongodb checks the files in minio, processes them and then saves them to another bucket in minio and another collection in mongodb.

It takes the following arguments:
- start_date: start date (dd/mm/yyyy)
- end_date: end date (dd/mm/yyyy)

To run the transformer, use the following command:

```bash
python -m src.main --start_date "dd/mm/yyyy" --end_date "dd/mm/yyyy"
```

The transformer will fetch all records from the `wrc_decisions` collection that fall within the specified date range. For each record, it will:
1.  Check if the file exists in the `wrc-decisions` bucket.
2.  If the file is an HTML file, it will clean it (remove navs, footers, etc.).
3.  Calculate the hash of the main file.
4.  Save the processed file(s) to the `wrc-processed` bucket under the same folder structure.
5.  Upsert the record into the `wrc_decisions_processed` collection, adding the new `file_hash` and `processed_at` timestamp.

## Airflow
The orchestration is handled by Airflow 3.1.4. The pipeline is defined in `dags/wrc_pipeline.py`.

### Configuration
- DAG: `wrc_pipeline`
- Schedule: None (Manual Trigger)
- Parameters:
    - start_date: Date to start scraping/processing (DD/MM/YYYY).
    - end_date: Date to end (DD/MM/YYYY).
    - query: Text to search for on the WRC site.

### Design Decisions
We utilize the `BashOperator` to execute the python modules directly.
In a production environment, it is better to isolate these tasks using `KubernetesPodOperator`, `DockerOperator`, or external Cloud Functions (`PythonOperator` with virtualenv is also an option).
However, for this local task, `BashOperator` provides the simplest integration with the mounted source code and shared environment, effectively running:

1.  Scraper Task: `python -m src.main ...` (in `scarper/` directory)
2.  Transformer Task: `python -m src.main ...` (in `transformer/` directory)

The transformer task depends on the scraper task standard downstream relationship (`>>`).

## Docker Compose
The project runs entirely on docker. The `docker-compose.yml` file spins up the following services:

- airflow-scheduler: schedules and runs the tasks (uses LocalExecutor).
- airflow-apiserver: handles API requests for Airflow 3.
- airflow-dag-processor: parses the DAG files.
- airflow-postgres: metadata database for airflow.
- mongodb: database for storing scraper/transformer records.
- minio: object storage for files (bucket `wrc-decisions` and `wrc-processed`).

Configuration (secrets, passwords) is handled via the `.env` file which is injected into the containers.

## How to Run

### Prerequisites
- Docker & Docker Compose installed.

### Steps
1.  Clone the repository.
2.  Copy the example.env file to .env, no need to change any values.
3.  Start Services:
    ```bash
    docker-compose up -d
    ```
    Wait for a minute for Airflow and other services to initialize.
4.  Access Airflow:
    Go to `http://localhost:8080`.
    User: `airflow`
    Password: `airflow`
5.  Trigger Pipeline:
    Unpause the `wrc_pipeline` DAG and trigger it with your desired parameters (Query, Start Date, End Date).

## Fast Run (run_pipeline.sh)
For quick local testing without interacting with the Airflow UI, a helper script `run_pipeline.sh` is provided. (Requires Python to be installed)

This script:
1.  Ensures docker containers are up.
2.  Creates/Activates a python virtual environment for the scraper.
3.  Installs requirements.
4.  Runs the scraper with default hardcoded dates/query (editable in the script).
5.  Creates/Activates a virtual environment for the transformer.
6.  Runs the transformer.

To use it:
```bash
source ./run_pipeline.sh
```
