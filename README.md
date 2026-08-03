# Project 'Job-Market'

## Project Organization

```text
├── LICENSE
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── logs               <- Logs from training and predicting
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── src                <- Source code for use in this project.
│   ├── __init__.py    <- Makes src a Python module
│   │
│   ├── data           <- Scripts to download or generate data
│   │   └── make_dataset.py
│   │
│   ├── features       <- Scripts to turn raw data into features for modeling
│   │   └── build_features.py
│   │
│   ├── models         <- Scripts to train models and then use trained models to make
│   │   │                 predictions
│   │   ├── predict_model.py
│   │   └── train_model.py
│   │
│   ├── visualization  <- Scripts to create exploratory and results oriented visualizations
│   │   └── visualize.py
│   └── config         <- Describe the parameters used in train_model.py and predict_model.py
```

Project is based on the [Cookiecutter Data Science project template](https://drivendata.github.io/cookiecutter-data-science/).
#cookiecutterdatascience

## Architecture

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
