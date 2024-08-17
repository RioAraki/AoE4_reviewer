# app.py
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from callback import register_callbacks
from util import deserialize_historical_match

# Initialize the Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        dbc.icons.BOOTSTRAP, 
        'https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css'
    ]
)

app.title = "Age of Empires 4 Match History"

app.layout = dbc.Container(
    [
        dcc.Store(id='match-store'),
        dcc.Store(id='recent-match-store'),
        dbc.Row(
            dbc.Col(
                html.H1("AOE4 Replay Reviewer", className="text-center my-4 text-4xl font-bold")
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Input(
                        id="player-id-input",
                        type="text",
                        placeholder="Enter Player ID, you can find player ID on aoe4world.com",
                        persistence=True,
                        className="form-control mb-3"
                    ),
                    width=12
                ),
                dbc.Col(
                    dbc.Button(
                        "Find Last Match Info",
                        id="fetch-button",
                        color="primary",
                        className="mb-3",
                        style={"margin-right": "20px"},
                    ),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Button(
                        "Find Recent Matches",
                        id="recent-match-button",
                        color="primary",
                        className="mb-3",
                        style={"margin-right": "20px"},
                    ),
                    width="auto"
                ),
                dbc.Col(
                    dcc.Upload(
                        id="upload-data",
                        children=dbc.Button(
                            "Load Saved Match",
                            color="primary",
                            className="mb-3"
                        ),
                        multiple=False
                    ),
                    width="auto"
                ),
            ],
            align="center",
            justify="start"
        ),
        dbc.Card(
            dbc.CardBody(
                html.Div(id="recent-match-info")
            ),
            id="recent-match-card",
            className="hover:bg-gray-200 transition duration-300 ease-in-out",
            style={"margin-bottom": "10px"},
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(id="game-info"), width=12),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(id="my-team-info"), width=6),
                dbc.Col(html.Div(id="opponent-team-info"), width=6)
            ]
        ),
        dbc.Row(
            dbc.Col(
                [
                    dcc.Download(id="download-json"),
                    dbc.Button(
                        "Download JSON",
                        id="download-button",
                        color="primary",
                        className="size-4",
                        style={"display": "none"}
                    )
                ]
            )
        ),
    ],
    fluid=False
)

# Register callbacks
register_callbacks(app)

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
