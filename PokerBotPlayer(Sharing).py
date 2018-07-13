#coding=UTF-8
from pokereval.card import Card
#from deuces import Card, Evaluator
from pokereval.hand_evaluator import HandEvaluator
from websocket import create_connection
import math
import random
import json
import numpy as np

def getCard(card):
    card_type = card[1]
    cardnume_code = card[0]
    card_num = 0
    card_num_type = 0
    if card_type == 'H':
        card_num_type = 1
    elif card_type == 'S':
        card_num_type = 2
    elif card_type == 'D':
        card_num_type = 3
    else:
        card_num_type = 4

    if cardnume_code == 'T':
        card_num = 10
    elif cardnume_code == 'J':
        card_num = 11
    elif cardnume_code == 'Q':
        card_num = 12
    elif cardnume_code == 'K':
        card_num = 13
    elif cardnume_code == 'A':
        card_num = 14
    else:
        card_num = int(cardnume_code)

    return Card(card_num,card_num_type)


class PokerBot(object):
    def declareAction(self,hole, board, round, my_Raise_Bet, my_Call_Bet,Table_Bet,number_players,raise_count,bet_count,my_Chips,total_bet):
        err_msg = self.__build_err_msg("declare_action")
        raise NotImplementedError(err_msg)
    def game_over(self,isWin,winChips,data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)
    def set_data(self, data, pre_player_action):
        err_msg = self.__build_err_msg("set_data")
        raise NotImplementedError(err_msg)


class PokerSocket(object):
    ws = ""
    board = []
    hole = []
    my_Raise_Bet = 0
    my_Call_Bet = 0
    number_players = 0
    my_Chips=0
    Table_Bet=0
    playerGameName=None
    raise_count=0
    bet_count=0
    total_bet=0
    pre_player_action = ""

    def __init__(self,playerName,connect_url, pokerbot):
        self.pokerbot=pokerbot
        self.playerName=playerName
        self.connect_url=connect_url

    def getAction(self,data):
        round = data['game']['roundName']
        # time.sleep(2)
        players = data['game']['players']
        chips = data['self']['chips']
        hands = data['self']['cards']
        big_blind = 2 * data['game']['bigBlind']['amount']

        self.raise_count = data['game']['raiseCount']
        self.bet_count = data['game']['betCount']
        self.my_Chips=chips
        self.playerGameName=data['self']['playerName']

        self.number_players = len(players)
        self.my_Call_Bet = data['self']['minBet']
        self.my_Raise_Bet = min(big_blind, int(chips / 4))
        self.hole = []
        for card in (hands):
            self.hole.append(getCard(card))

        print 'my_Call_Bet:{}'.format(self.my_Call_Bet)
        print 'my_Raise_Bet:{}'.format(self.my_Raise_Bet)
        print 'board:{}'.format(self.board)
        print 'table_bet:{}'.format(self.Table_Bet)
        print 'total_bet:{}'.format(self.total_bet)
        print 'hands:{}'.format(self.hole)

        if self.board == []:
            round = 'preflop'

        print "round:{}".format(round)

        self.pokerbot.set_data(data, self.pre_player_action)
        # aggresive_Tight = PokerBotPlayer(preflop_threshold_Tight, aggresive_threshold)
        # tightAction, tightAmount = aggresive_Tight.declareAction(hole, board, round, my_Raise_Bet, my_Call_Bet,Table_Bet,number_players)
        action, amount= self.pokerbot.declareAction(self.hole, self.board, round, self.my_Raise_Bet,self.my_Call_Bet, self.Table_Bet, self.number_players,self.raise_count,self.bet_count,self.my_Chips,self.total_bet)
        self.total_bet += amount
        return action, amount

    def takeAction(self,action, data):
        # Get number of players and table info
        if action == "__deal":
            self.pre_player_action = ""
        if action == "__show_action":
            self.pre_player_action = data['action']['action']

        if action == "__show_action" or action == "__deal":
            table = data['table']
            players = data['players']
            boards = table['board']
            self.number_players = len(players)
            self.Table_Bet = table['totalBet']
            self.board = []
            for card in (boards):
                self.board.append(getCard(card))
            print 'number_players:{}'.format(self.number_players)
            print 'board:{}'.format(self.board)
            print 'total_bet:{}'.format(self.Table_Bet)
        elif action == "__bet":
            action,amount=self.getAction(data)
            print "action: {}".format(action)
            print "action amount: {}".format(amount)
            self.ws.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.playerName,
                    "amount": amount
                }}))
        elif action == "__action":
            action,amount=self.getAction(data)
            print "action: {}".format(action)
            print "action amount: {}".format(amount)

            self.ws.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.playerName,
                    "amount": amount
                }}))
        elif action == "__round_end":
            print "Game Over"
            self.total_bet=0
            players=data['players']
            isWin=False
            winChips=0
            for player in players:
                winMoney=player['winMoney']
                playerid=player['playerName']
                if (self.playerGameName == playerid):
                    if (winMoney==0):
                        isWin = False
                    else:
                        isWin = True
                    winChips=winMoney
            print "winPlayer:{}".format(isWin)
            print "winChips:{}".format(winChips)
            self.pokerbot.game_over(isWin,winChips,data)
        elif action == "__new_round":
            self.board = []

    def doListen(self):
        try:
            self.ws = create_connection(self.connect_url)
            self.ws.send(json.dumps({
                "eventName": "__join",
                "data": {
                    "playerName": self.playerName
                }
            }))
            while 1:
                result = self.ws.recv()
                msg = json.loads(result)
                event_name = msg["eventName"]
                data = msg["data"]
                print event_name
                print data
                self.takeAction(event_name, data)
        except Exception, e:
            print e.message
            self.doListen()

class PotOddsPokerBot(PokerBot):

    def __init__(self, preflop_tight_loose_threshold,aggresive_passive_threshold,bet_tolerance):
        self.preflop_tight_loose_threshold = preflop_tight_loose_threshold
        self.aggresive_passive_threshold=aggresive_passive_threshold
        self.bet_tolerance=bet_tolerance
    def game_over(self, isWin,winChips,data):
        print "Game Over"

    def getCardID(self, card):
        rank = card.rank
        suit = card.suit
        suit = suit - 1
        id = (suit * 13) + rank
        return id

    def genCardFromId(self, cardID):
        if int(cardID) > 13:
            rank = int(cardID) % 13
            if rank == 0:
                suit = int((int(cardID) - rank) / 13)
            else:
                suit = int((int(cardID) - rank) / 13) + 1

            if (rank == 1):
                rank = 14
                suit -= 1
            elif (rank == 0):
                rank = 13
            return Card(rank, suit)
        else:
            suit = 1
            rank = int(cardID)
            if (rank == 1):
                rank = 14
            return Card(rank, suit)

    def _pick_unused_card(self,card_num, used_card):
        used = [self.getCardID(card) for card in used_card]
        unused = [card_id for card_id in range(1, 53) if card_id not in used]
        choiced = random.sample(unused, card_num)
        return [self.genCardFromId(card_id) for card_id in choiced]

    def get_win_prob(self,hand_cards, board_cards,simulation_number,num_players):
        """Calculate the win probability from your board cards and hand cards by using simple Monte Carlo method.

        Args:
            board_cards: The board card list.
            hand_cards: The hand card list

        Examples:
#            >>> get_win_prob(["8H", "TS", "6C"], ["7D", "JC"])
        """
        win = 0
        round=0
        evaluator = HandEvaluator()
        for i in range(simulation_number):

            board_cards_to_draw = 5 - len(board_cards)  # 2
            board_sample = board_cards + self._pick_unused_card(board_cards_to_draw, board_cards + hand_cards)
            unused_cards = self._pick_unused_card((num_players - 1)*2, hand_cards + board_sample)
            opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(num_players - 1)]

            try:
                opponents_score = [pow(evaluator.evaluate_hand(hole, board_sample), num_players) for hole in opponents_hole]
                # hand_sample = self._pick_unused_card(2, board_sample + hand_cards)
                my_rank = pow(evaluator.evaluate_hand(hand_cards, board_sample),num_players)
                if my_rank >= max(opponents_score):
                    win += 1
                #rival_rank = evaluator.evaluate_hand(hand_sample, board_sample)
                round+=1
            except Exception, e:
                print e.message
                continue
        # The large rank value means strong hand card
        print "Win:{}".format(win)
        win_prob = win / float(round)
        print "win_prob:{}".format(win_prob)
        return win_prob

    def declareAction(self,hole, board, round, my_Raise_Bet, my_Call_Bet,Table_Bet,number_players,raise_count,bet_count,my_Chips,total_bet):
        # Aggresive -tight
        self.number_players=number_players

        my_Raise_Bet=(my_Chips*self.bet_tolerance)/(1-self.bet_tolerance)
        print "Round:{}".format(round)
        score = HandEvaluator.evaluate_hand(hole, board)
        print "score:{}".format(score)
        #score = math.pow(score, self.number_players)
        print "score:{}".format(score)

        if round == 'preflop':
            if score >= self.preflop_tight_loose_threshold:
                action = 'call'
                amount = my_Call_Bet
            else:
                action = 'fold'
                amount = 0
        else:
            if score >= self.aggresive_passive_threshold:
                TableOdds = (my_Raise_Bet+total_bet) / (my_Raise_Bet + Table_Bet)
                if score >= TableOdds:
                    action = 'raise'
                    amount = my_Raise_Bet
                else:
                    TableOdds = (my_Call_Bet+total_bet) / (my_Call_Bet + Table_Bet)
                    if score >= TableOdds:
                        action = 'call'
                        amount = my_Call_Bet
                    else:
                        action = 'fold'
                        amount = 0
            else:
                TableOdds = (my_Call_Bet+total_bet) / (my_Call_Bet + Table_Bet)
                if score >= TableOdds:
                    action = 'call'
                    amount = my_Call_Bet
                else:
                    action = 'fold'
                    amount = 0
        #if (action=='call' or action=='raise') and len(board)>=4:
            #simulation_number=1000
            #win_rate=self.get_win_prob(hole, board, simulation_number,number_players)
            #if win_rate<0.4:
                #action = 'fold'
                #amount = 0
                #print 'change'
        return action, amount

class MontecarloPokerBot(PokerBot):

    def __init__(self, simulation_number):
       self.simulation_number=simulation_number

    def game_over(self, isWin,winChips,data):
        pass

    def declareAction(self,hole, board, round, my_Raise_Bet, my_Call_Bet,Table_Bet,number_players,raise_count,bet_count,my_Chips,total_bet):
        win_rate =self.get_win_prob(hole,board,number_players)
        print "win Rate:{}".format(win_rate)
        if win_rate > 0.5:
            if win_rate > 0.85:
                # If it is extremely likely to win, then raise as much as possible
                action = 'raise'
                amount = my_Raise_Bet
            elif win_rate > 0.75:
                # If it is likely to win, then raise by the minimum amount possible
                action = 'raise'
                amount = my_Raise_Bet
            else:
                # If there is a chance to win, then call
                action = 'call'
                amount=my_Call_Bet
        else:
            action = 'fold'
            amount=0
        return action,amount

    def getCardID(self, card):
        rank = card.rank
        suit = card.suit
        suit = suit - 1
        id = (suit * 13) + rank
        return id

    def genCardFromId(self, cardID):
        if int(cardID) > 13:
            rank = int(cardID) % 13
            if rank == 0:
                suit = int((int(cardID) - rank) / 13)
            else:
                suit = int((int(cardID) - rank) / 13) + 1

            if (rank == 1):
                rank = 14
                suit -= 1
            elif (rank == 0):
                rank = 13
            return Card(rank, suit)
        else:
            suit = 1
            rank = int(cardID)
            if (rank == 1):
                rank = 14
            return Card(rank, suit)

    def _pick_unused_card(self,card_num, used_card):

        used = [self.getCardID(card) for card in used_card]
        unused = [card_id for card_id in range(1, 53) if card_id not in used]
        choiced = random.sample(unused, card_num)
        return [self.genCardFromId(card_id) for card_id in choiced]

    def get_win_prob(self,hand_cards, board_cards,num_players):
        """Calculate the win probability from your board cards and hand cards by using simple Monte Carlo method.

        Args:
            board_cards: The board card list.
            hand_cards: The hand card list

        Examples:
#            >>> get_win_prob(["8H", "TS", "6C"], ["7D", "JC"])
        """
        win = 0
        round=0
        evaluator = HandEvaluator()

        for i in range(self.simulation_number):

            board_cards_to_draw = 5 - len(board_cards)  # 2
            board_sample = board_cards + self._pick_unused_card(board_cards_to_draw, board_cards + hand_cards)

            unused_cards = self._pick_unused_card((num_players - 1) * 2, hand_cards + board_sample)
            opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(num_players - 1)]
            #hand_sample = self._pick_unused_card(2, board_sample + hand_cards)

            try:
                opponents_score = [evaluator.evaluate_hand(hole, board_sample) for hole in opponents_hole]
                my_rank = evaluator.evaluate_hand(hand_cards, board_sample)
                if my_rank >= max(opponents_score):
                    win += 1
                #rival_rank = evaluator.evaluate_hand(hand_sample, board_sample)
                round+=1
            except Exception, e:
                #print e.message
                continue
        print "Win:{}".format(win)
        win_prob = win / float(round)
        return win_prob

class FreshPokerBot(PokerBot):

    def game_over(self, isWin,winChips,data):
        pass

    def declareAction(self,holes, boards, round, my_Raise_Bet, my_Call_Bet,Table_Bet,number_players,raise_count,bet_count,my_Chips,total_bet):
        my_rank = HandEvaluator.evaluate_hand(holes, boards)
        if my_rank>0.85:
            action = 'raise'
            amount = my_Raise_Bet
        elif  my_rank>0.6:
            action = 'call'
            amount = my_Call_Bet
        else:
            action = 'fold'
            amount = 0
        return action,amount


class CustomPokerBot(PotOddsPokerBot):
    data = ""
    pre_player_action = ""

    def set_data(self, data, pre_player_action):
        self.data = data
        self.pre_player_action = pre_player_action

    def game_over(self, is_win, win_chips, data):
        pass

    def declareAction(self, holes, boards, this_round, my_raise_bet, my_call_bet, table_bet, number_players,
                      raise_count, bet_count, my_chips, total_bet):
        action = 'fold'
        amount = 0
        my_rank = HandEvaluator.evaluate_hand(holes, boards)
        print "this_round:{}".format(this_round)
        print "evaluate_hand:{}".format(my_rank)
        print "pre_player_action:{}".format(self.pre_player_action)

        if this_round == 'preflop':
            table_odds = (1.0 * my_call_bet + total_bet) / (my_call_bet + table_bet)
            print "call table_odds:{}".format(table_odds)
            if my_rank > table_odds:
                if my_rank > 0.5:
                    action = 'call'
                    amount = my_call_bet
                #elif my_rank > 0.5 and my_call_bet <= my_chips * 0.7:
                #    action = 'call'
                #   amount = my_call_bet
                #    print "prevent allin"
                elif my_rank > 0.3 and my_call_bet <= my_chips / 50.0:
                    action = 'call'
                    amount = my_call_bet
                    print "aggressive call"
            else:
                action = 'fold'
                amount = 0
        elif this_round == 'River':
            win_rate = self.get_win_prob(holes, boards, 80, number_players)
            print "win_rate:{}".format(win_rate)
            if my_rank > 0.95:
                action = "allin"
            elif win_rate > 0.9:
                action = 'raise'
                amount = my_raise_bet
            elif win_rate > 0.5 or my_rank > 0.75:
                action = 'call'
                amount = my_call_bet
            elif my_rank > 0.6:
                table_odds = (1.0 * my_call_bet + total_bet) / (my_call_bet + table_bet)
                print "call table_odds:{}".format(table_odds)
                if my_rank > table_odds:
                    action = 'call'
                    amount = my_call_bet
                else:
                    action = 'fold'
                    amount = 0
            else:
                action = 'fold'
                amount = 0
        else:
            if my_rank > 0.55:
                print "total_bet:{}".format(total_bet)
                print "table_bet:{}".format(table_bet)
                table_odds = (1.0 * my_raise_bet + total_bet) / (my_raise_bet + table_bet)
                print "raise table_odds:{}".format(table_odds)
                if my_rank > 0.85 and my_rank > table_odds:
                    action = 'raise'
                    amount = my_raise_bet
                else:
                    table_odds = (1.0 * my_call_bet + total_bet) / (my_call_bet + table_bet)
                    print "call table_odds:{}".format(table_odds)
                    if my_rank > table_odds:
                        action = 'call'
                        amount = my_call_bet
                    else:
                        action = 'fold'
                        amount = 0
            else:
                action = 'fold'
                amount = 0

        # handle check
        if action == 'fold':
            if my_call_bet == 0:
                action = 'call'
                amount = my_call_bet
                print "call for bet 0"
            elif self.pre_player_action == 'check' or self.pre_player_action == '':
                action = 'check'
                amount = 0
                print "go check"
            #elif this_round == 'preflop' and self.data['game']['bigBlind']['playerName'] == self.data['self']['playerName']:
            #    action = 'check'
            #    amount = 0
            #    print "go check for preflop"

        return action, amount


if __name__ == '__main__':
        aggresive_threshold = 0.5
        passive_threshold = 0.7
        preflop_threshold_Loose = 0.3
        preflop_threshold_Tight = 0.5

        # Aggresive -loose
        #myPokerBot=PotOddsPokerBot(preflop_threshold_Loose,aggresive_threshold,bet_tolerance)
        #myPokerBot=PotOddsPokerBot(preflop_threshold_Tight,aggresive_threshold,bet_tolerance)
        #myPokerBot=PotOddsPokerBot(preflop_threshold_Loose,passive_threshold,bet_tolerance)
        #myPokerBot=PotOddsPokerBot(preflop_threshold_Tight,passive_threshold,bet_tolerance)

        playerName = "Sheryl_1112"
        connect_url = "ws://poker-dev.wrs.club:3001/"
        #connect_url = "ws://poker-training.vtr.trendnet.org:3001/"
        simulation_number = 100
        bet_tolerance = 0.1
        #myPokerBot=FreshPokerBot()
        #myPokerBot=MontecarloPokerBot(simulation_number)
        #myPokerBot=PotOddsPokerBot(preflop_threshold_Tight,aggresive_threshold,bet_tolerance)
        myPokerBot = CustomPokerBot(preflop_threshold_Tight, aggresive_threshold, bet_tolerance)
        myPokerSocket = PokerSocket(playerName,connect_url,myPokerBot)
        myPokerSocket.doListen()
