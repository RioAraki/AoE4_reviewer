import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State, ALL
import requests
import pandas as pd
import constants
from datetime import datetime
import json
import os


def fetch_recent_matches(player_id):
    api_url = f"https://aoe4world.com/api/v0/players/{player_id}/games?limit=10"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()  # Parse and return the JSON response

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def fetch_data(player_id):
    api_url = f"https://aoe4world.com/api/v0/players/{player_id}/games?limit=1"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()  # Parse and return the JSON response

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def display_recent_matches(data):

    return [
        dbc.ListGroupItem(
            dbc.Button(get_game_info_from_match(game), id={'type': 'game-link', 'index': i}, color="link", className="list-group-item")
        ) 
        for i, game in enumerate(data["games"])
    ]

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

    for idx, team in enumerate(teams):
        for player_data in team:
            player = player_data['player']
            player_info.append({
                'profile_id': player['profile_id'],
                'name': player['name'],
                'civilization': player['civilization'],
                'result': player['result'],
                'team': idx
            })

    return player_info

def convert_time_string(time_str, for_persist=False):
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    if for_persist:
        return dt.strftime("%Y-%m-%d_%H_%M_%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sec_to_min(sec):
    if sec is None:
        return "N/A"
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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

app.layout = dbc.Container(
    [
        
        dcc.Store(id='match-store'),
        dcc.Store(id='recent-match-store'),
        dbc.Row(
            dbc.Col(
                html.H1("帝国时代4 录像回放 比赛记录", className="text-center my-4")
            )
        ),
        html.I(className="bi bi-book floating-icon", style={"font-size": "2rem", "position": "fixed", "top": "1%", "left": "15px", "z-index": 1}, id="menu-toggle"),
        
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
                        "Find recent matches",
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
                        html.Div(id="nav-links")
                    ]
                )
            ),
            id="sidebar",
            is_open=False,
            style={
                "height": "100%",
                "width": "50%",
                "position": "fixed",
                # "z-index": 1,
                "top": "80px",
                "left": "15px",
                "transition": "0.5s",
            }
        ),
        dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Save Successful")),
            dbc.ModalBody(id="save-modal-body"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-save-modal", className="ml-auto")
            ),
        ],
        id="save-modal",
        is_open=False,
    ),
    ],
    fluid=True
)

@app.callback(
    Output("sidebar", "is_open"),
    [Input("menu-toggle", "n_clicks")],
    [State("sidebar", "is_open")]
)
def toggle_sidebar(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    [
        Output("save-modal", "is_open"),
        Output("save-modal-body", "children")
    ],
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
def serialize_game(ids, feudal_times, feudal_dropdowns, castle_times, castle_dropdowns, empire_times,  empire_dropdowns, strategies, improvements, match_data, n_clicks):
    if n_clicks is None:
        return False, ""

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
    directory = "./data"
    if not os.path.exists(directory):
        os.makedirs(directory)

    filepath = os.path.join(directory, f"{match_name}.json")

    with open(filepath, 'w', encoding='utf-8') as json_file:
        json.dump(match_data, json_file, ensure_ascii=False, indent=4)

    return True, f"File saved successfully at {filepath}"


def match_info_to_display(match, my_profile_id):

    user_input = match.get("player-input", None)
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
            my_team_index = player_info['team']
            break

    for player_info in player_info_list:
        cur_input = None
        if user_input:
            cur_input = user_input[str(player_info["profile_id"])]
        
        player_card = generate_player_card(player_info, cur_input)
        
        if player_info['team'] == my_team_index:
            if str(player_info['profile_id']) == my_profile_id:
                my_team_cards = [player_card] + my_team_cards
            else:
                my_team_cards.append(player_card)
        else:
            opponent_team_cards.append(player_card)

    return html.Div(my_team_cards), html.Div(opponent_team_cards), html.Div(game_info), {"display": "inline-block"}, match


@app.callback(
    [Output("recent-match-info", "children"),
     Output("recent-match-store", "data")],
    [Input("recent-match-button", "n_clicks")],
    [State("player-id-input", "value")],

)
def update_recent_matches(n_clicks, my_profile_id):
    ctx = dash.callback_context

    if not ctx.triggered:
        return [""], None
    
    recent_matches = fetch_recent_matches(my_profile_id)
    game_list = []
    for match in recent_matches["games"]:
        game_list.append(match)

    return display_recent_matches(recent_matches), game_list

@app.callback(
    [Output("my-team-info", "children"),
     Output("opponent-team-info", "children"),
     Output("game-info", "children"),
     Output("save-button", "style"),
     Output("match-store", "data")],
    [Input("fetch-button", "n_clicks"),
     Input({'type': 'file-link', 'index': ALL}, 'n_clicks'),
     Input({'type': 'game-link', 'index': ALL}, 'n_clicks')],
    [State("player-id-input", "value"),
     State("recent-match-store", "data")],
)
def update_match_info(n_clicks, file_link_clicks, game_link_clicks, my_profile_id, recent_matches):
    
    ctx = dash.callback_context

    if not ctx.triggered:
        return "", "", "", {"display": "none"}, None

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if 'fetch-button' in trigger_id:
        if n_clicks:
            match = get_last_match_data(my_profile_id)
            return match_info_to_display(match, my_profile_id)

    elif any(element is not None for element in file_link_clicks):
        if file_link_clicks != [None, None]:
            index = eval(trigger_id)['index']
            files = os.listdir("./data")
            if index < len(files):
                file_path = f"./data/{files[index]}"
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        content_dict = json.loads(content)
                        return match_info_to_display(content_dict, my_profile_id)
                except Exception as e:
                    raise ValueError(e)
    elif any(element is not None for element in game_link_clicks):
        trigger_id_dict = json.loads(trigger_id)
        match = recent_matches[trigger_id_dict["index"]]
        return match_info_to_display(match, my_profile_id)

    else:
        return "", "", "", {"display": "none"}, None
    

@app.callback(
    Output("nav-links", "children"),
    [Input("menu-toggle", "n_clicks")]
)
def deserialize_historical_match(n_clicks):
    if n_clicks:
        try:
            files = os.listdir("./data")
            links = [
                dbc.ListGroupItem(
                    dbc.Button(file, id={'type': 'file-link', 'index': i}, color="link", className="list-group-item")
                ) 
                for i, file in enumerate(files)
            ]
            return links
        except FileNotFoundError:
            return [dbc.ListGroupItem("No saved matches found.", className="nav-text", action=True)]
    return []


def generate_player_card(player_info, cur_input = None):

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
                        dbc.Col(dbc.Input(type="time", id={"type": "feudal-time", "player_id": player_id}, className="mr-2", value=cur_input["feudal-time"] if cur_input else None)),
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "feudal-dropdown", "player_id": player_id},
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['feudal'],
                                value= cur_input["feudal-dropdown"] if cur_input else None,
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
                        dbc.Col(dbc.Input(type="time", id={"type": "castle-time", "player_id": player_id}, className="mr-2", value= cur_input["castle-dropdown"] if cur_input else None)),
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "castle-dropdown", "player_id": player_id},
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['castle'],
                                value=cur_input["castle-dropdown"] if cur_input else None,
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
                        dbc.Col(dbc.Input(type="time", id={"type": "empire-time", "player_id": player_id}, className="mr-2", value= cur_input["empire-dropdown"] if cur_input else None)),
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "empire-dropdown", "player_id": player_id},
                                options=constants.AOE4_LANDMARKS_BY_CIV[player_info['civilization']]['empire'],
                                value=cur_input["empire-dropdown"] if cur_input else None,
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
                                value=cur_input["strategy-input"] if cur_input else None,
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
                                value=cur_input["improve-input"] if cur_input else None,
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
