# callbacks.py
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import json
import os
from util import fetch_recent_matches, get_game_info_from_match, save_match_data, deserialize_historical_match, display_recent_matches, get_last_match_data, match_info_to_display
import base64
import io
def register_callbacks(app):

    @app.callback(
        [Output("recent-match-info", "children"),
         Output("recent-match-store", "data")],
        [Input("recent-match-button", "n_clicks")],
        [State("player-id-input", "value")],
    )
    def update_recent_matches(n_clicks, my_profile_id):
        if not n_clicks:
            raise PreventUpdate
        recent_matches = fetch_recent_matches(my_profile_id)
        game_list = []
        for match in recent_matches["games"]:
            game_list.append(match)
        return display_recent_matches(recent_matches), game_list


    @app.callback(
        [
            Output("my-team-info", "children"),
            Output("opponent-team-info", "children"),
            Output("game-info", "children"),
            Output("download-button", "style"),
            Output("match-store", "data")
        ],
        [
            Input("fetch-button", "n_clicks"),
            Input("upload-data", "contents"),
            Input({'type': 'file-link', 'index': ALL}, 'n_clicks'),
            Input({'type': 'game-link', 'index': ALL}, 'n_clicks')
        ],
        [
            State("player-id-input", "value"),
            State("upload-data", "filename"),
            State("recent-match-store", "data")
        ]
    )
    def update_match_info(n_clicks, contents, file_link_clicks, game_link_clicks, my_profile_id, filename, recent_matches):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Handle match fetching from the input button
        if 'fetch-button' in trigger_id:
            if n_clicks:
                match = get_last_match_data(my_profile_id)
                return match_info_to_display(match, my_profile_id)

        # Handle file uploads
        elif 'upload-data' in trigger_id and contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                match_data = json.load(io.StringIO(decoded.decode('utf-8')))
                return match_info_to_display(match_data, my_profile_id)
            except Exception as e:
                return html.Div(['There was an error processing this file.']), dash.no_update, dash.no_update, dash.no_update

        # Handle recent matches link clicks
        elif any(element is not None for element in game_link_clicks):
            trigger_id_dict = json.loads(trigger_id)
            match = recent_matches[trigger_id_dict["index"]]
            return match_info_to_display(match, my_profile_id)

        else:
            raise PreventUpdate

    @app.callback(
        Output("download-json", "data"),
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
            State("match-store", "data")
        ],
        [Input("download-button", "n_clicks")]
    )
    def download_game_data(ids, feudal_times, feudal_dropdowns, castle_times, castle_dropdowns, empire_times, empire_dropdowns, strategies, improvements, match_data, n_clicks):
        if n_clicks is None:
            raise PreventUpdate

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

        json_data = json.dumps(match_data, ensure_ascii=False, indent=4)

        # Return the data as a downloadable JSON file
        return dcc.send_string(json_data, filename=f"{match_name}.json")
    