# callbacks.py
import dash
from dash.dependencies import Input, Output, State, ALL
import json
import os
from util import fetch_recent_matches, get_game_info_from_match, save_match_data, deserialize_historical_match, display_recent_matches, get_last_match_data, match_info_to_display

def register_callbacks(app):

    @app.callback(
        [Output("recent-match-info", "children"),
         Output("recent-match-store", "data")],
        [Input("recent-match-button", "n_clicks")],
        [State("player-id-input", "value")],
    )
    def update_recent_matches(n_clicks, my_profile_id):
        if not n_clicks:
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
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if not ctx.triggered:
            return "", "", "", {"display": "none"}, None

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
    def serialize_game(ids, feudal_times, feudal_dropdowns, castle_times, castle_dropdowns, empire_times, empire_dropdowns, strategies, improvements, match_data, n_clicks):
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
        filepath = save_match_data(match_data, match_name)
        return True, f"File saved successfully at {filepath}"

