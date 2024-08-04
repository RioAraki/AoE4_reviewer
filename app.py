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
                html.H1("帝国时代4 录像回放 比赛记录", className="text-center my-4")
            )
        ),
        html.I(className="bi bi-book floating-icon", style={"font-size": "2rem", "position": "fixed", "top": "1%", "left": "15px", "z-index": -999}, id="menu-toggle"),
        dbc.Row(
            dbc.Col(
                [
                    dcc.Input(
                        id="player-id-input",
                        type="text",
                        placeholder="Enter Player ID",
                        value="684292",
                        className="form-control mb-3"
                    ),
                    dbc.Button(
                        "Find Last Match Info",
                        id="fetch-button",
                        color="primary",
                        className="mb-3",
                        style={"margin-right": "20px"},
                    ),
                    dbc.Button(
                        "Find Recent Matches",
                        id="recent-match-button",
                        color="primary",
                        className="mb-3"
                    )
                ]
            )
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
                    dbc.Button(
                        "Save",
                        id="save-button",
                        color="primary",
                        className="mb-3",
                        style={"display": "none"}
                    )
                ]
            )
        ),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("Saved Matches"),
                        html.Div(deserialize_historical_match(), id="saved-matches")
                    ]
                )
            ),
            id="sidebar",
            is_open=False,
            style={
                "height": "100%",
                "width": "50%",
                "position": "fixed",
                "top": "80px",
                "left": "15px",
            }
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Save Successful")),
                dbc.ModalBody(id="save-modal-body"),
            ],
            id="save-modal",
            is_open=False,
        ),
    ],
    fluid=True
)

# Register callbacks
register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
