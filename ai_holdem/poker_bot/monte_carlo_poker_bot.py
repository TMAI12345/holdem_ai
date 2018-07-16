from poker_bot import PokerBot
from utils import utils

from pokereval.hand_evaluator import HandEvaluator
from pokereval.card import Card

import random

class MontecarloPokerBot(PokerBot):

    def __init__(self, simulation_number):
        self.simulation_number = simulation_number

    def game_over(self, isWin,winChips,data):
        pass

    def declareAction(self, state, minBet, seat_num):
        hole = state.player_state[seat_num].cards
        board = state.table_state.board
        number_players = len([player for player in state.player_state if player.isSurvive])

        win_rate = self.get_win_prob(hole, board, number_players)
        print "win Rate:{}".format(win_rate)

        big_blind = state.table_state.big_blind_amount
        chips = state.player_state[seat_num].chips
        my_Raise_Bet = min(big_blind, int(chips / 4))

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
                amount = minBet
        else:
            action = 'fold'
            amount = 0
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
        unused = [card_id for card_id in range(2, 54) if card_id not in used]
        choiced = random.sample(unused, card_num)
        return [self.genCardFromId(card_id) for card_id in choiced]

    def get_win_prob(self, hand_cards, board_cards, num_players):
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

        for i in range(self.simulation_number):

            board_cards_to_draw = 5 - len(board_cards)  # 2
            board_sample = board_cards + self._pick_unused_card(board_cards_to_draw, board_cards + hand_cards)

            unused_cards = self._pick_unused_card((num_players - 1) * 2, hand_cards + board_sample)
            opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(num_players - 1)]
            # hand_sample = self._pick_unused_card(2, board_sample + hand_cards)

            try:
                opponents_score = [evaluator.evaluate_hand(hole, board_sample) for hole in opponents_hole]
                my_rank = evaluator.evaluate_hand(hand_cards, board_sample)
                if my_rank >= max(opponents_score):
                    win += 1
                # rival_rank = evaluator.evaluate_hand(hand_sample, board_sample)
                round += 1
            except Exception, e:
                # print e.message
                continue
        print "Win:{}".format(win)
        win_prob = win / float(round)
        return win_prob