"""Dash frontend for the Job Market application."""

import requests

from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from dash import Dash, Input, Output, State, ctx, dcc, html

from src.config.settings import DASH_DEBUG, FASTAPI_URL, FRONTEND_PORT, JOBS_PAGE_SIZE

ASSETS_DIRECTORY = Path(__file__).parent / "assets"

app = Dash(
    __name__,
    assets_folder=str(ASSETS_DIRECTORY),
    title="Job Market",
)


def _format_salary(job: dict) -> str | None:
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


def _create_job_card(job: dict) -> html.Article:
    """Create a card for one job-search result."""

    metadata = []

    if job.get("city"):
        metadata.append(html.Span(f"⌖ {job['city']}"))

    salary = _format_salary(job)

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


def _create_map(jobs: list[dict]) -> Figure:
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
        zoom=4,
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
        dcc.Store(
            id="current-page",
            data=1,
        ),
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
                                        html.Div(
                                            [
                                                html.Button(
                                                    "‹",
                                                    id="previous-page-button",
                                                    disabled=True,
                                                ),
                                                html.Span(
                                                    "Page 1",
                                                    id="page-number",
                                                ),
                                                html.Button(
                                                    "›",
                                                    id="next-page-button",
                                                ),
                                            ],
                                            className="pagination",
                                        ),
                                    ],
                                    className="results-column",
                                ),
                                html.Div(
                                    dcc.Graph(
                                        id="job-map",
                                        figure=_create_map([]),
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
    Output("current-page", "data"),
    Output("page-number", "children"),
    Output("previous-page-button", "disabled"),
    Output("next-page-button", "disabled"),
    Input("search-button", "n_clicks"),
    Input("previous-page-button", "n_clicks"),
    Input("next-page-button", "n_clicks"),
    State("current-page", "data"),
    State("keyword-input", "value"),
    State("location-input", "value"),
    State("company-input", "value"),
)
def search_jobs(
    search_clicks: int | None,
    previous_clicks: int | None,
    next_clicks: int | None,
    current_page: int,
    keyword: str | None,
    city: str | None,
    company: str | None,
):
    """Retrieve jobs from FastAPI and update the results."""

    if ctx.triggered_id == "search-button":
        current_page = 1
    elif ctx.triggered_id == "previous-page-button":
        current_page = max(1, current_page - 1)
    elif ctx.triggered_id == "next-page-button":
        current_page += 1

    offset = (current_page - 1) * JOBS_PAGE_SIZE

    parameters: dict[str, str | int] = {
        "limit": JOBS_PAGE_SIZE + 1,
        "offset": offset,
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
        return [message], _create_map([])

    jobs = response.json()

    has_next_page = len(jobs) > JOBS_PAGE_SIZE
    jobs = jobs[:JOBS_PAGE_SIZE]

    previous_disabled = current_page == 1
    next_disabled = not has_next_page

    if not jobs:
        message = html.P(
            "No matching jobs were found.",
            className="empty-message",
        )
        return [message], _create_map([])

    cards = [_create_job_card(job) for job in jobs]

    return (
        cards,
        _create_map(jobs),
        current_page,
        f"Page {current_page}",
        previous_disabled,
        next_disabled,
    )


if __name__ == "__main__":
    # 0.0.0.0 tells Uvicorn to listen on all network interfaces.
    # Without this, it would listen only on 127.0.0.1 inside the container,
    # and Docker could not forward requests from the browser.
    app.run(
        host="0.0.0.0",
        port=FRONTEND_PORT,
        debug=DASH_DEBUG,
    )
