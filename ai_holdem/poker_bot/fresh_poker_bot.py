from poker_bot import PokerBot
from pokereval.hand_evaluator import HandEvaluator
class FreshPokerBot(PokerBot):

    def game_over(self, isWin, winChips, data):
        pass

    def declareAction(self, state, minBet, seat_num):
        hole = state.player_state[seat_num].cards
        board = state.table_state.board
        my_rank = HandEvaluator.evaluate_hand(hole, board)

        big_blind = state.table_state.big_blind_amount
        chips = state.player_state[seat_num].chips
        my_Raise_Bet = min(big_blind, int(chips / 4))

        if my_rank > 0.85:
            action = 'raise'
            amount = my_Raise_Bet
        elif my_rank > 0.6:
            action = 'call'
            amount = minBet
        else:
            action = 'fold'
            amount = 0
        return action, amount
