import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import requests
import pandas as pd
import constants

# Function to fetch data from API
def fetch_data(player_id):
    api_url = f"https://aoe4world.com/api/v0/players/{player_id}/games?limit=1"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()  # Parse and return the JSON response

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Function to extract the last match information
def get_last_match_data(player_id):
    data = fetch_data(player_id)
    if "error" in data:
        return data["error"]

    if not data or "games" not in data:
        return "No games found"

    games = data["games"]
    if not games:
        return "No games found"

    # Find the match with the biggest timestamp
    last_match = max(games, key=lambda x: x['started_at'])
    return last_match

def get_player_info_from_last_match(last_match):
    teams = last_match["teams"]
    player_info = []

    for team in teams:
        for player_data in team:
            player = player_data['player']
            player_info.append({
                'profile_id': player['profile_id'],
                'name': player['name'],
                'civilization': player['civilization'],
                'result': player['result']
            })

    return player_info

def sec_to_min(sec):
    minutes = sec // 60
    remaining_seconds = sec % 60
    return f"{minutes:02}:{remaining_seconds:02}"

def get_game_info_from_match(last_match):
    game_id = last_match["game_id"]
    duration = sec_to_min(last_match["duration"])
    map =  last_match["map"]
    kind = last_match["kind"]
    avg_mmr = last_match["average_mmr"]


    game_card = dbc.Card(
        dbc.CardBody(
            [
                html.H4(f"Game ID: {game_id} | Duration: {duration} | Map: {map} | Kind: {kind} | MMR: {avg_mmr}",
                        className="text-center"
                        ),
            ]
        ),
        className="mb-3",
    )
    return game_card


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("AOE4 Player Last Match Info", className="text-center my-4")
            )
        ),
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
                        "Fetch Last Match Info",
                        id="fetch-button",
                        color="primary",
                        className="mb-3"
                    )
                ]
            )
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
        )
    ],
    fluid=True
)

@app.callback(
    [Output("my-team-info", "children"),
     Output("opponent-team-info", "children"),
     Output("game-info", "children")],
    [Input("fetch-button", "n_clicks")],
    [Input("player-id-input", "value")]
)
def update_match_info(n_clicks, my_profile_id):
    if not n_clicks:
        return "", "", ""

    match = get_last_match_data(my_profile_id)
    if isinstance(match, str):
        return html.Div(match), html.Div(match), html.Div(match)

    # Determine teams
    player_info_list = get_player_info_from_last_match(match)
    game_info = get_game_info_from_match(match)
    my_team_cards = []
    opponent_team_cards = []


    # Identify your team and opponent team
    for player_info in player_info_list:
        player_card = generate_player_card(player_info)
        if str(player_info['profile_id']) == my_profile_id:
            my_team_index = player_info_list.index(player_info) // 2  # Assuming 2 teams, index // 2 gives the team number
            break

    for index, player_info in enumerate(player_info_list):
        player_card = generate_player_card(player_info)
        if index // 2 == my_team_index:
            my_team_cards.append(player_card)
        else:
            opponent_team_cards.append(player_card)

    return html.Div(my_team_cards), html.Div(opponent_team_cards), html.Div(game_info)


def generate_player_card(player_info):
    player_card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(player_info['name'], className="card-title"),
                html.Li(f"Profile ID: {player_info['profile_id']}", className="card-text"),
                html.Li(f"Civilization: {player_info['civilization']}", className="card-text"),
                dbc.Row(
                    [
                        dbc.Col(html.Label("Feudal", className="mr-2"), width="auto", align="center"),
                        dbc.Col(dbc.Input(type="time", id="feudal-time", className="mr-2")),
                        dbc.Col(
                            dcc.Dropdown(
                                id="feudal-dropdown",
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['feudal'],
                                value=player_info['civilization'],
                                className="mr-2"
                            ),
                        ),
                    ],
                    style={"margin-bottom": "5px"},
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(html.Label("Castle", className="mr-2"), width="auto", align="center"),
                        dbc.Col(dbc.Input(type="time", id="castle-time", className="mr-2")),
                        dbc.Col(
                            dcc.Dropdown(
                                id="castle-dropdown",
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['castle'],
                                value=player_info['civilization'],
                                className="mr-2"
                            ),
                        ),
                    ],
                    style={"margin-bottom": "5px"},
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(html.Label("Empire", className="mr-2"), width="auto", align="center"),
                        dbc.Col(dbc.Input(type="time", id="empire-time", className="mr-2")),
                        dbc.Col(
                            dcc.Dropdown(
                                id="empire-dropdown",
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['empire'],
                                value=player_info['civilization'],
                                className="mr-2"
                            ),
                        ),
                    ],
                    style={"margin-bottom": "10px"},
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Textarea(
                                size="sm",
                                className="mb-3",
                                placeholder="How the play want to play? Is it successful or not?",
                            ),
                        ),     
                    ],
                    style={"margin-bottom": "5px"},
                    align="center",
                ),
            ]
        ),
        className="mb-3",
    )

    return player_card


if __name__ == "__main__":
    app.run_server(debug=True)
