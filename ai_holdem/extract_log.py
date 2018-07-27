# import pandas as pd
import os
import re
import json
from holdem import Table, Player
from pokereval.hand_evaluator import HandEvaluator
from utils.utils import getCard, get_index_from_player_list, get_current_state, get_log_data, state_to_csv, LOG_DATA

EVENT_LIST = ["SHOW_ACTION", "ROUND_END", "GAME_OVER"]


def extract_log(location, log_path):
    file_list = []
    msg_list = []
    log_list = []
    for filename in os.listdir(location):
        file_list.append(filename)
    for filename in reversed(file_list):
        print filename
        f = open(os.path.join(location, filename), "r")
        for line in f:
            if any(event in line for event in EVENT_LIST):
                s = re.search(r'({.*})', line).group(1)
                msg = json.loads(s)
                msg_list.append(msg)
    table_dict = get_table_dict(msg_list)
    for table_number in table_dict.keys():
        table_data = table_dict[table_number]
        table_obj = None
        players = []
        log = []
        for msg in table_data:
            event_name = msg["eventName"]
            data = msg["data"]
            if table_obj is None:
                table_obj = Table(table_number)
            if len(players) == 0:
                for i, p in enumerate(data["players"]):
                    players.append(Player(p['playerName'], 3000))

            if event_name == "__show_action":
                player_index = get_index_from_player_list(data['action']['playerName'], players)
                players[player_index].update_action(data['action'], data["table"]["roundName"])
                #  update table and player
                table_obj.update_table_status(data)
                for i, p in enumerate(players):
                    p.update_by_state(data['players'][i])

                #  get predict rank data
                state = get_current_state(table_obj, players)
                log_info = get_log_data(state, player_index)
                log.append(log_info)
            elif event_name == "__round_end":
                if table_obj is not None:
                    for player in data['players']:
                        for i, log_data in enumerate(log):
                            if log_data.player_name == player['playerName']:
                                if player['isOnline'] and not player['folded'] and not player['isHuman']:  # if player is not online, delete the record
                                # if player['isOnline'] and not player['isHuman']:  # if player is not online and not human, delete the record
                                    log_list.append(log_data._replace(win_money=player['winMoney'] / (1.0 * log[i].big_blind)))
                    # state_to_csv(LOG_DATA, "log/no fold/", log)
                    log = []
                # table_obj.update_table_status(data)
                # for i, p in enumerate(players):
                #     p.update_by_state(data['players'][i])
                for p in players:
                    p.new_round()
            elif event_name == "__game_over":
                players = []
                table_obj = None
                log = []
    # state_to_csv(LOG_DATA, "log/{}/".format(log_path), log_list)
    state_to_csv(LOG_DATA, "log/no fold/", log_list)


def get_table_dict(data):
    table_dict = {}
    for d in data:
        table_number = d["data"]["table"]["tableNumber"]
        if table_dict.has_key(table_number):
            table_dict[table_number].append(d)
        else:
            table_dict[table_number] = [d]
    return table_dict

if __name__ == '__main__':
    # file_list = ["0717", "0718", "0719", "0720", "0723", "0724", "0725", "0726"]
    file_list = ["0726"]
    for file in file_list:
        file_path = "C:\Users\jeremy_pan\Desktop\log\\{}\common_log\\".format(file)
        extract_log(file_path, file)
