from .pot_odds_poker_bot import PotOddsPokerBot

from pokereval.hand_evaluator import HandEvaluator
from pokereval.card import Card

import random


class CustomPokerBot(PotOddsPokerBot):
    data = ""
    pre_player_action = ""


    # def set_data(self, data, pre_player_action):
    #     self.data = data
    #     self.pre_player_action = pre_player_action

    def game_over(self, isWin,winChips,data):
        print "Game Over"

    def declareAction(self, state, minBet, seat_num):
        holes = state.player_state[seat_num].cards
        boards = state.table_state.board
        my_chips = state.player_state[seat_num].chips
        this_round = state.table_state.round
        # Aggresive -tight
        number_players = len([player for player in state.player_state if player.isSurvive])

        my_raise_bet = (my_chips * self.bet_tolerance) / (1 - self.bet_tolerance)
        my_call_bet = minBet
        table_bet = state.table_state.total_bet
        total_bet = state.player_state[seat_num].roundBet  # how many chips you bet in this round

        action = 'fold'
        amount = 0
        my_rank = HandEvaluator.evaluate_hand(holes, boards)
        print "this_round:{}".format(this_round)
        print "evaluate_hand:{}".format(my_rank)
        print "pre_player_action:{}".format(state.table_state.last_action)

        # if this_round == 'preflop':
        if this_round == 'Deal':
            table_odds = (1.0 * my_call_bet + total_bet) / (my_call_bet + table_bet)
            print "call table_odds:{}".format(table_odds)
            if my_rank > table_odds:
                if my_rank > 0.5:
                    action = 'call'
                    amount = my_call_bet
                # elif my_rank > 0.5 and my_call_bet <= my_chips * 0.7:
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
            if win_rate > 0.9 or my_rank > 0.9:
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
        print("state.table_state.last_action: {}".format(state.table_state.last_action))
        if action == 'fold':
            if my_call_bet == 0:
                action = 'call'
                amount = my_call_bet
                print "call for bet 0"
            # elif self.pre_player_action == 'check' or self.pre_player_action == '':
            elif state.table_state.last_action == 'check' or state.table_state.last_action == '':
                action = 'check'
                amount = 0
                print "go check"
            # elif this_round == 'preflop' and self.data['game']['bigBlind']['playerName'] == self.data['self']['playerName']:
            #    action = 'check'
            #    amount = 0
            #    print "go check for preflop"

        return action, amount

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

    def _pick_unused_card(self, card_num, used_card):
        used = [self.getCardID(card) for card in used_card]
        unused = [card_id for card_id in range(1, 53) if card_id not in used]
        choiced = random.sample(unused, card_num)
        return [self.genCardFromId(card_id) for card_id in choiced]

    def get_win_prob(self, hand_cards, board_cards, simulation_number, num_players):
        """Calculate the win probability from your board cards and hand cards by using simple Monte Carlo method.
        Args:
            board_cards: The board card list.
            hand_cards: The hand card list
        Examples:
#            >>> get_win_prob(["8H", "TS", "6C"], ["7D", "JC"])
        """
        win = 0
        round = 0
        evaluator = HandEvaluator()
        for i in range(simulation_number):

            board_cards_to_draw = 5 - len(board_cards)  # 2
            board_sample = board_cards + self._pick_unused_card(board_cards_to_draw, board_cards + hand_cards)
            unused_cards = self._pick_unused_card((num_players - 1) * 2, hand_cards + board_sample)
            opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(num_players - 1)]

            try:
                opponents_score = [pow(evaluator.evaluate_hand(hole, board_sample), num_players) for hole in
                                   opponents_hole]
                # hand_sample = self._pick_unused_card(2, board_sample + hand_cards)
                my_rank = pow(evaluator.evaluate_hand(hand_cards, board_sample), num_players)
                if my_rank >= max(opponents_score):
                    win += 1
                # rival_rank = evaluator.evaluate_hand(hand_sample, board_sample)
                round += 1
            except Exception, e:
                print e.message
                continue
        # The large rank value means strong hand card
        print "Win:{}".format(win)
        win_prob = win / float(round)
        print "win_prob:{}".format(win_prob)
        return win_prob
