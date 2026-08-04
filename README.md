# Project 'Job-Market'

## Architecture

### Project Folder Structure

#### Code

```text
src
|
+---api
|   |   main.py
|   |       FastAPI entry point
|   |
|   +---routes
|       |   health.py
|       |       health-check endpoint to verify that the API is running
|       |
|       |   jobs.py
|       |       endpoints for searching jobs and retrieving individual job details
|       |
|       |   statistics.py
|       |       statistical endpoints for jobs, companies, locations, and home-office availability
|
+---config
|   |   settings.py
|   |       shared configuration such as paths, ports, and API URLs
|
+---dashboard
|   |   app.py
|   |       Dash frontend entry point
|   |
|   +---assets
|       |   styles.css
|       |       visual styling and layout of the Dash frontend
|
+---data
|   |   arbeitsagentur_client.py
|   |       retrieves jobs from the Arbeitsagentur API
|   |
|   |   job_location_geocoder.py
|   |       adds latitude and longitude coordinates to job locations
|   |
|   |   make_dataset.py
|   |       runs the complete data pipeline: downloading, cleaning, geocoding, and saving jobs
|   |
|   |   sqlite_database.py
|   |       helper for database access
|   |
|   |   sqlite_loader.py
|   |       inserts or updates cleaned jobs in the SQLite database
|
+---tests
|   |   test_smoke.py
|   |       ensures that the GitHub Actions test workflow does not fail
```

#### Generated Data

```text
data
|
+---processed
|   |   job_market.sqlite3
|   |       processed SQLite database used by the API and dashboard
|
\---raw
    \---arbeitsagentur
        \---<timestamp>
            |   clean-jobs.json
            |       cleaned and normalized job data
            |
            |   job-details.json
            |       raw job details retrieved from the API
            |
            |   job-detail-failures.json
            |       failed job-detail requests
            |
            \---search-results
                +---<keyword>
                |       page-001.json
                |       raw search results for one keyword
                |
                \---...
```

### Project Overview

![Project Overview](docs/images/project-overview.png)

### Docker Deployment

![Docker Deployment](docs/images/docker-deployment.png)

## Usage

> **Note:** Every command in this section is assumed to be run from the project root directory.

### Without Docker

#### Setup Python

```sh
py -m venv .venv
source .venv\bin\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Create or update SQLite database with recent jobs

```sh
python -m src.data.make_dataset
```

#### Start the backend API

```sh
python -m uvicorn src.api.main:api --reload
```

#### Start the Dash frontend:

```sh
python -m src.dashboard.app
```


### With Docker

Start the application:

```sh
./docker_start.sh
```

If you see an error that the SQLite database does not exist, run:
```sh
./docker_build_db.sh
```

Then start the application again:

```sh
./docker_start.sh
```

### Open in your browser

**Swagger (Backend):** http://127.0.0.1:8000/docs

**Dash (Frontend):** http://127.0.0.1:8050

##

> Project is based on the [Cookiecutter Data Science project template](https://drivendata.github.io/cookiecutter-data-science/). #cookiecutterdatascience