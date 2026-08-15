"""Dash frontend for the Job Market application."""

import requests

from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

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
        custom_data=[
            "reference_number",
            "company",
            "city",
        ],
        zoom=4,
        center={"lat": 51.1, "lon": 10.4},
        map_style="open-street-map",
    )

    figure.update_traces(
        marker={
            "size": 18,
            "color": "#ff385c",
        },
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Company: %{customdata[1]}<br>"
            "City: %{customdata[2]}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )

    return figure


def _format_location(location: dict) -> str:
    parts = [
        location.get("postal_code"),
        location.get("city"),
        location.get("region"),
        location.get("country"),
    ]

    return ", ".join(str(part) for part in parts if part)


def _create_job_modal_content(job: dict) -> list:
    salary = _format_salary(job)

    locations = [
        html.Li(_format_location(location)) for location in job.get("locations", [])
    ]

    content = [
        html.H2(job["title"]),
        html.P(
            job.get("company") or "Company not specified",
            className="job-company",
        ),
    ]

    if salary:
        content.append(html.P(salary))

    if locations:
        content.extend(
            [
                html.H3("Locations"),
                html.Ul(locations),
            ]
        )

    if job.get("description"):
        content.append(
            html.Div(
                [
                    html.H3("Description"),
                    html.P(job["description"]),
                ],
                className="job-description",
            )
        )

    if job.get("external_url"):
        content.append(
            html.A(
                "Open job advertisement",
                href=job["external_url"],
                target="_blank",
                rel="noopener noreferrer",
                className="details-button",
            )
        )

    return content


def _get_statistics() -> tuple[dict, list, list, dict]:
    overview = requests.get(
        f"{FASTAPI_URL}/statistics/overview",
        timeout=10,
    )
    overview.raise_for_status()

    companies = requests.get(
        f"{FASTAPI_URL}/statistics/companies",
        params={"limit": 10},
        timeout=10,
    )
    companies.raise_for_status()

    locations = requests.get(
        f"{FASTAPI_URL}/statistics/locations",
        params={"limit": 10},
        timeout=10,
    )
    locations.raise_for_status()

    home_office = requests.get(
        f"{FASTAPI_URL}/statistics/home-office",
        timeout=10,
    )
    home_office.raise_for_status()

    return (
        overview.json(),
        companies.json(),
        locations.json(),
        home_office.json(),
    )


def _create_statistics_content() -> list:
    overview, companies, locations, home_office = _get_statistics()

    overview_cards = html.Div(
        [
            html.Div(
                [
                    html.H3("Jobs"),
                    html.P(overview["total_jobs"]),
                ],
                className="statistics-card",
            ),
            html.Div(
                [
                    html.H3("Companies"),
                    html.P(overview["total_companies"]),
                ],
                className="statistics-card",
            ),
            html.Div(
                [
                    html.H3("Locations"),
                    html.P(overview["total_locations"]),
                ],
                className="statistics-card",
            ),
            html.Div(
                [
                    html.H3("Period"),
                    html.P(
                        f"{overview['earliest_publication_date']} – "
                        f"{overview['latest_publication_date']}"
                    ),
                ],
                className="statistics-card",
            ),
        ],
        className="statistics-overview",
    )

    companies_frame = pd.DataFrame(companies)

    companies_figure = px.bar(
        companies_frame,
        x="job_count",
        y="company",
        orientation="h",
        title="Top companies",
    )

    locations_frame = pd.DataFrame(locations)

    locations_figure = px.bar(
        locations_frame,
        x="job_count",
        y="city",
        orientation="h",
        title="Top locations",
    )

    home_office_frame = pd.DataFrame(
        {
            "status": ["Possible", "Not possible", "Unknown"],
            "count": [
                home_office["possible"],
                home_office["not_possible"],
                home_office["unknown"],
            ],
        }
    )

    home_office_figure = px.pie(
        home_office_frame,
        names="status",
        values="count",
        hole=0.5,
        title="Home office",
    )

    return [
        overview_cards,
        dcc.Graph(figure=companies_figure),
        dcc.Graph(figure=locations_figure),
        dcc.Graph(figure=home_office_figure),
    ]


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
                        html.Button(
                            "Find jobs",
                            id="find-jobs-tab",
                            className="navigation-tab active",
                        ),
                        html.Button(
                            "Statistics",
                            id="statistics-tab",
                            className="navigation-tab",
                        ),
                        html.Button(
                            "About",
                            id="about-tab",
                            className="navigation-tab",
                        ),
                    ],
                    className="navigation",
                ),
            ],
            className="page-header",
        ),
        html.Main(
            [
                html.Div(
                    id="find-jobs-page",
                    children=[
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
                    ],
                ),
                html.Div(
                    id="statistics-page",
                    children=[
                        html.Div(id="statistics-content"),
                    ],
                    className="statistics-page",
                    style={"display": "none"},
                ),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            "×",
                            id="close-job-modal",
                            className="modal-close-button",
                        ),
                        html.Div(id="job-modal-content"),
                    ],
                    className="job-modal",
                ),
            ],
            id="job-modal-overlay",
            className="modal-overlay",
        ),
    ],
    className="page",
)


@app.callback(
    Output("find-jobs-page", "style"),
    Output("statistics-page", "style"),
    Output("find-jobs-tab", "className"),
    Output("statistics-tab", "className"),
    Output("statistics-content", "children"),
    Input("find-jobs-tab", "n_clicks"),
    Input("statistics-tab", "n_clicks"),
)
def switch_tab(find_jobs_clicks, statistics_clicks):
    if ctx.triggered_id == "statistics-tab":
        return (
            {"display": "none"},
            {"display": "block"},
            "navigation-tab",
            "navigation-tab active",
            _create_statistics_content(),
        )

    return (
        {"display": "block"},
        {"display": "none"},
        "navigation-tab active",
        "navigation-tab",
        no_update,
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


@app.callback(
    Output("job-modal-overlay", "className"),
    Output("job-modal-content", "children"),
    Input(
        {
            "type": "job-card-button",
            "index": ALL,
        },
        "n_clicks",
    ),
    Input("job-map", "clickData"),
    Input("close-job-modal", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_job_modal(
    job_clicks,
    map_click,
    close_clicks,
):
    triggered_id = ctx.triggered_id

    if triggered_id == "close-job-modal":
        return "modal-overlay", []

    if triggered_id == "job-map":
        reference_number = map_click["points"][0]["customdata"][0]

    elif isinstance(triggered_id, dict):
        if not any(job_clicks):
            return no_update, no_update

        reference_number = triggered_id["index"]

    else:
        return no_update, no_update

    try:
        response = requests.get(
            f"{FASTAPI_URL}/jobs/{reference_number}",
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return (
            "modal-overlay open",
            html.P("The job details could not be loaded."),
        )

    job = response.json()

    return (
        "modal-overlay open",
        _create_job_modal_content(job),
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
