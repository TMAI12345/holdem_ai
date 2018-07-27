import json

from websocket import create_connection
from pokereval.hand_evaluator import HandEvaluator
from pokereval.card import Card

import poker_bot
import hashlib

from holdem import Table
from holdem import Player
from poker_socket import PokerSocket
from utils import utils


class PredictRankSocket(PokerSocket):
    ws = ""
    predict_rank_data = []

    def __init__(self,playerName,connect_url, pokerbot):
        self.pokerbot = pokerbot
        self.playerName = playerName
        self.md5_name = hashlib.md5(self.playerName).hexdigest()
        self.connect_url = connect_url

        self.table = None
        self.players = []
        self.predict_rank_data = []

    def resetGame(self):
        return False

    def resetRound(self):
        return False

    def getAction(self, data):
        state = utils.get_current_state(self.table, self.players)
        minBet = data['self']['minBet']
        player_index = utils.get_index_from_player_list(data['self']['playerName'], self.players)
        #  Change hand and board to object Card
        # hand = []
        # board = []
        # print(state.player_state[seat_num].cards)
        # for card in state.player_state[seat_num].cards:
        #     hand.append(utils.getCard(card))
        # for card in state.table_state.board:
        #     board.append(utils.getCard(card))
        # state.player_state[seat_num] = state.player_state[seat_num]._replace(cards=hand)
        # state.table_state = state.table_state._replace(board=board)
        print("state: {}".format(state))
        action, amount = self.players[player_index].do_action(state, minBet, player_index)
        return action, amount

    def takeAction(self, action, data):
        # Get number of players and table info
        if action == "__game_start":
            # print("Game Start")
            table_number = data['tableNumber']
            self.table = Table(table_number)
            return False
        elif action == "__new_round":
            print("New Round")
            self.predict_rank_data = []
            table_data = data['table']
            players_data = data['players']
            if self.table is None:
                # raise ("Error: Table is None.")
                table_number = table_data['tableNumber']
                self.table = Table(table_number)
            self.table.update_table_status(data)

            if len(self.players) == 0:  # first time join the game
                for i, p in enumerate(players_data):
                    if p['playerName'] == self.md5_name:
                        self.players.append(Player(p['playerName'], p['chips'], self.pokerbot))
                    else:
                        self.players.append(Player(p['playerName'], p['chips']))
            for i, p in enumerate(self.players):
                p.update_by_state(players_data[i])
            return False
        elif action == "__show_action":
            player_index = utils.get_index_from_player_list(data['action']['playerName'], self.players)
            self.players[player_index].update_action(data['action'])
            #  get predict rank data
            state = utils.get_current_state(self.table, self.players)
            rank_info = utils.get_rank_data(state, player_index)
            self.predict_rank_data.append(rank_info)

            #  update table and player
            self.table.update_table_status(data)
            for i, p in enumerate(self.players):
                p.update_by_state(data['players'][i])
            #  record some states
            return False
        elif action == "__bet":
            print("Bet")
            action, amount = self.getAction(data)
            print "action: {}".format(action)
            print "action amount: {}".format(amount)
            self.ws.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.playerName,
                    "amount": amount
                }}))
            return False
        elif action == "__action":
            print("Action")
            action, amount = self.getAction(data)
            print "action: {}".format(action)
            print "action amount: {}".format(amount)
            self.ws.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.playerName,
                    "amount": amount
                }}))
            return False
        elif action == "__deal":
            print "Deal Cards"
            self.table.update_table_status(data)
            for i, p in enumerate(self.players):
                p.update_by_state(data['players'][i])
            return False
        elif action == "__start_reload":
            print "Reload"
            # self.ws.send(json.dumps({
            #     "eventName": "__reload",
            # }))
            # self.ws.send(json.dumps({
            #     "eventName": "__reload",
            # }))
            return False
        elif action == "__round_end":
            print "Round End"
            # update card and rank for each player
            evaluator = HandEvaluator()
            for player in data['players']:
                for i, rank_data in enumerate(self.predict_rank_data):
                    if rank_data.player_name == player['playerName']:
                        if not player['isOnline']:  # if player is not online, delete the record
                            self.predict_rank_data.remove(rank_data)
                        else:
                            hand = []
                            for card in player['cards']:
                                hand.append(utils.getCard(card))
                            board = self.predict_rank_data[i].board
                            self.predict_rank_data[i] = self.predict_rank_data[i]._replace(cards=hand)
                            # hand, board = utils.str_list_to_card(self.predict_rank_data[i].cards,
                            #                                      self.predict_rank_data[i].board)
                            rank = evaluator.evaluate_hand(hand, board)
                            # print("rank: {}".format(rank))
                            self.predict_rank_data[i] = self.predict_rank_data[i]._replace(rank=rank)
            utils.state_to_csv(utils.PREDICT_RANK_DATA, "log/", self.predict_rank_data)
            return False
        elif action == "__game_over":
            print "Game Over"
            self.table = None
            self.players = []
            self.ws.send(json.dumps({
                "eventName": "__join",
                "data": {
                    "playerName": self.playerName
                }
            }))
            return True

    def doListen(self):
        # self.ws = create_connection(self.connect_url)
        # self.ws.send(json.dumps({
        #     "eventName": "__join",
        #     "data": {
        #         "playerName": self.playerName
        #     }
        # }))
        while True:
            try:
                self.ws = create_connection(self.connect_url)
                self.ws.send(json.dumps({
                    "eventName": "__join",
                    "data": {
                        "playerName": self.playerName
                    }
                }))
                terminal = False
                while not terminal:
                    try:
                        result = self.ws.recv()
                        msg = json.loads(result)
                        event_name = msg["eventName"]
                        data = msg["data"]
                        print event_name
                        print data
                        terminal = self.takeAction(event_name, data)
                    # except WebSocketConnectionClosedException:
                    except Exception as e:
                        print e.message
                        # self.ws.close()
                        # self.ws = create_connection(self.connect_url)
                        self.ws.send(json.dumps({
                            "eventName": "__join",
                            "data": {
                                "playerName": self.playerName
                            }
                        }))
                self.ws.close()
            except Exception, e:
                print e.message
                self.doListen()

