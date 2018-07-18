from poker_bot import PokerBot

from pokereval.hand_evaluator import HandEvaluator
from pokereval.card import Card

import random

class PotOddsPokerBot(PokerBot):

    def __init__(self, preflop_tight_loose_threshold,aggresive_passive_threshold,bet_tolerance):
        self.preflop_tight_loose_threshold = preflop_tight_loose_threshold
        self.aggresive_passive_threshold=aggresive_passive_threshold
        self.bet_tolerance=bet_tolerance
    def game_over(self, isWin,winChips,data):
        print "Game Over"

    def declareAction(self, state, minBet, seat_num):
        hole = state.player_state[seat_num].cards
        board = state.table_state.board
        chips = state.player_state[seat_num].chips
        round = state.table_state.round
        # Aggresive -tight
        self.number_players = len([player for player in state.player_state if player.isSurvive])

        my_Raise_Bet = (chips * self.bet_tolerance) / (1 - self.bet_tolerance)
        my_Call_Bet = minBet
        Table_Bet = state.table_state.total_bet
        total_bet = state.player_state[seat_num].roundBet  # how many chips you bet in this round

        print "Round:{}".format(round)
        score = HandEvaluator.evaluate_hand(hole, board)
        print "score:{}".format(score)
        # score = math.pow(score, self.number_players)
        print "score:{}".format(score)

        if round == 'Deal':
            if score >= self.preflop_tight_loose_threshold:
                action = 'call'
                amount = my_Call_Bet
            else:
                action = 'fold'
                amount = 0
        else:
            if score >= self.aggresive_passive_threshold:
                TableOdds = (my_Raise_Bet + total_bet) / (my_Raise_Bet + Table_Bet)
                if score >= TableOdds:
                    action = 'raise'
                    amount = my_Raise_Bet
                else:
                    TableOdds = (my_Call_Bet + total_bet) / (my_Call_Bet + Table_Bet)
                    if score >= TableOdds:
                        action = 'call'
                        amount = my_Call_Bet
                    else:
                        action = 'fold'
                        amount = 0
            else:
                TableOdds = (my_Call_Bet + total_bet) / (my_Call_Bet + Table_Bet)
                if score >= TableOdds:
                    action = 'call'
                    amount = my_Call_Bet
                else:
                    action = 'fold'
                    amount = 0
        # if (action=='call' or action=='raise') and len(board)>=4:
        # simulation_number=1000
        # win_rate=self.get_win_prob(hole, board, simulation_number,number_players)
        # if win_rate<0.4:
        # action = 'fold'
        # amount = 0
        # print 'change'
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
