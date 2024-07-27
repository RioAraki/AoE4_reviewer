import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State, ALL
import requests
import pandas as pd
import constants
from datetime import datetime
import json

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

def convert_time_string(time_str, for_persist=False):
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    if for_persist:
        return dt.strftime("%Y-%m-%d_%H_%M_%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sec_to_min(sec):
    minutes = sec // 60
    remaining_seconds = sec % 60
    return f"{minutes:02}:{remaining_seconds:02}"

def get_game_info_from_match(last_match, for_persist=False):
    game_id = last_match["game_id"]
    start_time = convert_time_string(last_match["started_at"], for_persist)
    duration = sec_to_min(last_match["duration"])
    map =  last_match["map"]
    kind = last_match["kind"]
    avg_mmr = last_match["average_mmr"]
    if for_persist:
        return f"{start_time},{map},{kind}"

    return f"Game ID: {game_id} | Time: {start_time} | Duration: {duration} | Map: {map} | Kind: {kind} | MMR: {avg_mmr}"

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dcc.Store(id='match-store'),
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
    ],
    fluid=True
)

@app.callback(
    [
     State({"type": "feudal-time", "player_id": ALL}, "id"),
     State({"type": "feudal-time", "player_id": ALL}, "value"),
     State({"type": "feudal-dropdown", "player_id": ALL}, "value"),
     State({"type": "castle-time", "player_id": ALL}, "value"),
     State({"type": "castle-dropdown", "player_id": ALL}, "value"),
     State({"type": "empire-time", "player_id": ALL}, "value"),
     State({"type": "empire-dropdown", "player_id": ALL}, "value"),
     State({"type": "strategy-input", "player_id": ALL}, "value"),
     State({"type": "improve-input", "player_id": ALL}, "value"),
     State("match-store", "data")],

    [Input("save-button", "n_clicks")]
)
def persist_game(ids, feudal_times, feudal_dropdowns, castle_times, castle_dropdowns, empire_times,  empire_dropdowns, strategies, improvements, match_data, n_clicks):
    if n_clicks is None:
        return
    print(ids)
    print(feudal_times)
    print(castle_times)
    print(empire_times)
    print(strategies)
    print(improvements)
    print(match_data)

    match_name = get_game_info_from_match(match_data, True)
    ids = [entry['player_id'] for entry in ids]
    player_input = {}

    for idx, id in enumerate(ids):
        cur_input = {
            "feudal-time": feudal_times[idx],
            "feudal-dropdown": feudal_dropdowns[idx],
            "castle-time": castle_times[idx],
            "castle-dropdown": castle_dropdowns[idx],
            "empire-time": empire_times[idx],
            "empire-dropdown": empire_dropdowns[idx],
            "strategy-input": strategies[idx],
            "improve-input": improvements[idx],
        }
        player_input[id] = cur_input
    
    match_data["player-input"] = player_input

    with open(f"./data/{match_name}", 'w') as json_file:
        json.dump(match_data, json_file, indent=4)


@app.callback(
    [Output("my-team-info", "children"),
     Output("opponent-team-info", "children"),
     Output("game-info", "children"),
     Output("save-button", "style"),
     Output("match-store", "data")],
    [Input("fetch-button", "n_clicks")],
    [State("player-id-input", "value")]
)
def update_match_info(n_clicks, my_profile_id):
    if not n_clicks:
        return "", "", "", {"display": "none"}, None

    match = get_last_match_data(my_profile_id)

    if isinstance(match, str):
        return html.Div(match), html.Div(match), html.Div(match), {"display": "none"}, None

    # Determine teams
    player_info_list = get_player_info_from_last_match(match)
    game_info = dbc.Card(
        dbc.CardBody(
            [
                html.H4(get_game_info_from_match(match),
                    className="text-center"
                ),
            ]
        ),
        className="mb-3",
    )
    my_team_cards = []
    opponent_team_cards = []

    # Identify your team and opponent team
    my_team_index = -1
    for player_info in player_info_list:
        if str(player_info['profile_id']) == my_profile_id:
            my_team_index = player_info_list.index(player_info) // 2  # Assuming 2 teams, index // 2 gives the team number
            break

    for index, player_info in enumerate(player_info_list):
        player_card = generate_player_card(player_info)
        if index // 2 == my_team_index:
            my_team_cards.append(player_card)
        else:
            opponent_team_cards.append(player_card)

    return html.Div(my_team_cards), html.Div(opponent_team_cards), html.Div(game_info), {"display": "inline-block"}, match


def generate_player_card(player_info):
    player_id = player_info['profile_id']
    player_card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(player_info['name'], className="card-title"),
                html.Li(f"Profile ID: {player_id}", className="card-text"),
                html.Li(f"Civilization: {player_info['civilization']}", className="card-text"),
                dbc.Row(
                    [
                        dbc.Col(html.Label("Feudal", className="mr-2"), width="auto", align="center"),
                        dbc.Col(dbc.Input(type="time", id={"type": "feudal-time", "player_id": player_id}, className="mr-2", value=None)),
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "feudal-dropdown", "player_id": player_id},
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['feudal'],
                                value=None,
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
                        dbc.Col(dbc.Input(type="time", id={"type": "castle-time", "player_id": player_id}, className="mr-2", value=None)),
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "castle-dropdown", "player_id": player_id},
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['castle'],
                                value=None,
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
                        dbc.Col(dbc.Input(type="time", id={"type": "empire-time", "player_id": player_id}, className="mr-2", value=None)),
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "empire-dropdown", "player_id": player_id},
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['empire'],
                                value=None,
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
                                id={"type": "strategy-input", "player_id": player_id},
                                size="sm",
                                className="mb-3",
                                placeholder="What is the game plan? Is it successful or not?",
                            ),
                        ),     
                    ],
                    style={"margin-bottom": "5px"},
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Textarea(
                                id={"type": "improve-input", "player_id": player_id},
                                size="sm",
                                className="mb-3",
                                placeholder="What are some areas to improve?",
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
