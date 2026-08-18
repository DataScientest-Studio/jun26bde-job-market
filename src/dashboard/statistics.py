""" """

import requests

import pandas as pd
import plotly.express as px
from dash import dcc, html

from src.config.settings import FASTAPI_URL

# region Private helper functions


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


# endregion


def create_statistics_content() -> tuple[html.Div, list[dcc.Graph]]:
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

    return overview_cards, [
        dcc.Graph(figure=companies_figure),
        dcc.Graph(figure=locations_figure),
        dcc.Graph(figure=home_office_figure),
    ]
