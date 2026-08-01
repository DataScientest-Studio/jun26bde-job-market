from urllib.parse import quote

from dash import Dash, Input, Output, State, dcc, html
from src.config.settings import FASTAPI_URL, FRONTEND_PORT

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Job Market"),
        dcc.Input(
            id="search-input",
            type="text",
            placeholder="Search job text, company, or occupation...",
        ),
        html.Button("Search", id="search-button"),
        html.Iframe(
            id="job-map",
            src=f"{FASTAPI_URL}/map",
            style={
                "width": "100%",
                "height": "700px",
                "border": "none",
            },
        ),
    ]
)


@app.callback(
    Output("job-map", "src"),
    Input("search-button", "n_clicks"),
    State("search-input", "value"),
    prevent_initial_call=True,
)
def update_map(_n_clicks: int, search: str | None) -> str:
    if not search or not search.strip():
        return f"{FASTAPI_URL}/map"

    return f"{FASTAPI_URL}/map?search={quote(search.strip())}"


if __name__ == "__main__":
    app.run(debug=True, port=FRONTEND_PORT)
