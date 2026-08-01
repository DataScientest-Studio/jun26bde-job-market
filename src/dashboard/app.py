"""Dash frontend for the Job Market application."""

import requests

from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from dash import Dash, Input, Output, State, dcc, html

from src.config.settings import FASTAPI_URL, FRONTEND_PORT

ASSETS_DIRECTORY = Path(__file__).parent / "assets"

app = Dash(
    __name__,
    assets_folder=str(ASSETS_DIRECTORY),
    title="Job Market",
)

DUMMY_JOBS = [
    {
        "reference_number": "JOB-001",
        "title": "Senior Data Engineer",
        "company": "FERCHAU GmbH",
        "city": "Berlin",
        "work_model": "Remote",
        "salary": "€70,000–€85,000",
        "latitude": 52.5200,
        "longitude": 13.4050,
    },
    {
        "reference_number": "JOB-002",
        "title": "Python Backend Developer",
        "company": "TechWorks AG",
        "city": "Hamburg",
        "work_model": "Hybrid",
        "salary": "€65,000–€78,000",
        "latitude": 53.5511,
        "longitude": 9.9937,
    },
    {
        "reference_number": "JOB-003",
        "title": "AI Software Engineer",
        "company": "Intelligence Labs",
        "city": "Munich",
        "work_model": "Remote",
        "salary": "€80,000–€95,000",
        "latitude": 48.1351,
        "longitude": 11.5820,
    },
    {
        "reference_number": "JOB-004",
        "title": "Data Analyst",
        "company": "Analytics Solutions",
        "city": "Cologne",
        "work_model": "On-site",
        "salary": "€55,000–€68,000",
        "latitude": 50.9375,
        "longitude": 6.9603,
    },
]


def format_salary(job: dict) -> str | None:
    """Format the available salary information."""

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")

    if salary_min is None and salary_max is None:
        return None

    if salary_min is not None and salary_max is not None:
        salary = f"€{salary_min:,.0f}–€{salary_max:,.0f}"
    elif salary_min is not None:
        salary = f"From €{salary_min:,.0f}"
    else:
        salary = f"Up to €{salary_max:,.0f}"

    if job.get("salary_period"):
        salary += f" / {job['salary_period']}"

    return salary


def create_job_card(job: dict) -> html.Article:
    """Create a card for one job-search result."""

    metadata = []

    if job.get("city"):
        metadata.append(html.Span(f"⌖ {job['city']}"))

    salary = format_salary(job)

    if salary:
        metadata.append(html.Span(salary))

    return html.Article(
        [
            html.H2(job["title"], className="job-title"),
            html.P(
                job.get("company") or "Company not specified", className="job-company"
            ),
            html.Div(metadata, className="job-metadata"),
            html.Button(
                "View details",
                id={
                    "type": "job-card-button",
                    "index": job["reference_number"],
                },
                className="details-button",
            ),
        ],
        className="job-card",
    )


def create_map(jobs: list[dict]) -> Figure:
    """Create a map containing the available job locations."""

    jobs_with_coordinates = [
        job
        for job in jobs
        if job.get("latitude") is not None and job.get("longitude") is not None
    ]

    if not jobs_with_coordinates:
        figure = Figure()
        figure.update_layout(
            map={
                "style": "open-street-map",
                "zoom": 4.5,
                "center": {"lat": 51.1, "lon": 10.4},
            },
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            annotations=[
                {
                    "text": "No job locations available",
                    "showarrow": False,
                }
            ],
        )
        return figure

    jobs_frame = pd.DataFrame(jobs_with_coordinates)

    figure = px.scatter_map(
        jobs_frame,
        lat="latitude",
        lon="longitude",
        hover_name="title",
        hover_data={
            "company": True,
            "city": True,
            "latitude": False,
            "longitude": False,
        },
        custom_data=["reference_number"],
        zoom=4.5,
        center={"lat": 51.1, "lon": 10.4},
        map_style="open-street-map",
    )

    figure.update_traces(
        marker={
            "size": 18,
            "color": "#ff385c",
        }
    )

    figure.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )

    return figure


app.layout = html.Div(
    [
        html.Header(
            [
                html.A(
                    [
                        html.Div("J", className="brand-icon"),
                        html.Span("jobmarket"),
                    ],
                    href="/",
                    className="brand",
                ),
                html.Nav(
                    [
                        html.A("Find jobs", href="#", className="active"),
                        html.A("Statistics", href="#"),
                        html.A("About", href="#"),
                    ],
                    className="navigation",
                ),
            ],
            className="page-header",
        ),
        html.Main(
            [
                html.Section(
                    [
                        html.P(
                            "Explore jobs from companies across Germany.",
                            className="hero-subtitle",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("What"),
                                        dcc.Input(
                                            id="keyword-input",
                                            type="text",
                                            placeholder="Job title or keyword",
                                        ),
                                    ],
                                    className="search-field",
                                ),
                                html.Div(
                                    [
                                        html.Label("Where"),
                                        dcc.Input(
                                            id="location-input",
                                            type="text",
                                            placeholder="City or remote",
                                        ),
                                    ],
                                    className="search-field",
                                ),
                                html.Div(
                                    [
                                        html.Label("Company"),
                                        dcc.Input(
                                            id="company-input",
                                            type="text",
                                            placeholder="Any company",
                                        ),
                                    ],
                                    className="search-field",
                                ),
                                html.Button(
                                    "Search",
                                    id="search-button",
                                    className="search-button",
                                ),
                            ],
                            className="search-panel",
                        ),
                    ],
                    className="hero",
                ),
                html.Section(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            id="job-list",
                                            className="job-list",
                                        ),
                                    ],
                                    className="results-column",
                                ),
                                html.Div(
                                    dcc.Graph(
                                        id="job-map",
                                        figure=create_map([]),
                                        config={
                                            "displayModeBar": False,
                                            "scrollZoom": True,
                                        },
                                        className="job-map",
                                    ),
                                    className="map-column",
                                ),
                            ],
                            className="content-grid",
                        ),
                    ],
                    className="results-section",
                ),
            ]
        ),
    ],
    className="page",
)


@app.callback(
    Output("job-list", "children"),
    Output("job-map", "figure"),
    Input("search-button", "n_clicks"),
    State("keyword-input", "value"),
    State("location-input", "value"),
    State("company-input", "value"),
)
def search_jobs(
    n_clicks: int | None,
    keyword: str | None,
    city: str | None,
    company: str | None,
) -> tuple[list, Figure]:
    """Retrieve jobs from FastAPI and update the results."""

    parameters = {
        "limit": 100,
    }

    if keyword:
        parameters["keyword"] = keyword.strip()

    if city:
        parameters["city"] = city.strip()

    if company:
        parameters["company"] = company.strip()

    try:
        response = requests.get(
            f"{FASTAPI_URL}/jobs",
            params=parameters,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        message = html.P(
            "The job API is currently unavailable.",
            className="error-message",
        )
        return [message], create_map([])

    jobs = response.json()

    if not jobs:
        message = html.P(
            "No matching jobs were found.",
            className="empty-message",
        )
        return [message], create_map([])

    cards = [create_job_card(job) for job in jobs]

    return cards, create_map(jobs)


if __name__ == "__main__":
    app.run(debug=True, port=FRONTEND_PORT)
