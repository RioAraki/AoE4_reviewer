# utils.py
import os
import json
import requests
from datetime import datetime
import dash_bootstrap_components as dbc
from dash import html, dcc
import constants

def fetch_recent_matches(player_id, limit=10):
    api_url = f"https://aoe4world.com/api/v0/players/{player_id}/games?limit={limit}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def fetch_data(player_id):
    api_url = f"https://aoe4world.com/api/v0/players/{player_id}/games?limit=1"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

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

def get_game_info_from_match(match, for_persist=False):
    game_id = match["game_id"]
    start_time = convert_time_string(match["started_at"], for_persist)
    duration = sec_to_min(match["duration"])
    map_name = match["map"]
    kind = match["kind"]
    avg_mmr = match["average_mmr"]
    if for_persist:
        return f"{start_time},{map_name},{kind}"
    return f"Game ID: {game_id} | Time: {start_time} | Duration: {duration} | Map: {map_name} | Kind: {kind} | MMR: {avg_mmr}"

def save_match_data(match_data, match_name):
    directory = "./data"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, f"{match_name}.json")
    with open(filepath, 'w', encoding='utf-8') as json_file:
        json.dump(match_data, json_file, ensure_ascii=False, indent=4)
    return filepath

def deserialize_historical_match():
    try:
        files = os.listdir("./data")
        links = [
            dbc.ListGroupItem(
                html.A(file, id={'type': 'file-link', 'index': i}, className="list-group-item")
            ) 
            for i, file in enumerate(files)
        ]
        return links
    except FileNotFoundError:
        return [dbc.ListGroupItem("No saved matches found.", className="nav-text", action=True)]

def display_recent_matches(data):

    return [
        dbc.ListGroupItem(
            html.A(get_game_info_from_match(game), id={'type': 'game-link', 'index': i}, className="list-group-item")
        ) 
        for i, game in enumerate(data["games"])
    ]

def match_info_to_display(match, my_profile_id):
    user_input = match.get("player-input", None)
    player_info_list = get_player_info_from_last_match(match)

    my_team_index = -1
    my_name = ""
    for player_info in player_info_list:
        if str(player_info['profile_id']) == my_profile_id:
            my_team_index = player_info['team']
            my_name = player_info['name']
            break

    my_team_cards = []
    opponent_team_cards = []

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

    game_info = dbc.Card(
        dbc.CardBody(
            [
                html.A(children=html.H4(get_game_info_from_match(match), className="card-title"), href=f"https://aoe4world.com/players/{my_profile_id}-{my_name}/games/{match['game_id']}", className="text-center", target="_blank"),
            ]
        ),
        className="mb-3",
    )
    return html.Div(my_team_cards), html.Div(opponent_team_cards), html.Div(game_info), {"display": "inline-block"}, match

    
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

def generate_player_card(player_info, cur_input = None):
    player_id = player_info['profile_id']
    player_card = dbc.Card(
        dbc.CardBody(
            [
                html.A(children=html.H4(player_info['name'], className="card-title text-2xl font-bold hover:underline hover:text-blue-600 transition duration-300 ease-in-out"), href=f"https://aoe4world.com/players/{player_id}", target="_blank"),
                html.Li(f"Profile ID: {player_id}", className="card-text"),
                html.Li(f"Civilization: {player_info['civilization']}", className="card-text", style={"margin-bottom": "5px"}),
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
                        dbc.Col(dbc.Input(type="time", id={"type": "castle-time", "player_id": player_id}, className="mr-2", value= cur_input["castle-time"] if cur_input else None)),
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
                        dbc.Col(dbc.Input(type="time", id={"type": "empire-time", "player_id": player_id}, className="mr-2", value= cur_input["empire-time"] if cur_input else None)),
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
                                style={"height": "100px"}
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
                                style={"height": "100px"}
                            ),
                        ),     
                    ],
                    style={"margin-bottom": "5px"},
                    align="center",
                ),
            ]
        ),
        className="mb-3 hover:bg-gray-50 transition duration-300 hover:shadow-md ease-in-out",

    )

    return player_card

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
