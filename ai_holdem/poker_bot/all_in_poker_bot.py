from poker_bot import PokerBot

class AllInPokerBot(PokerBot):

    def game_over(self, isWin, winChips, data):
        pass

    def declareAction(self, state, minBet, seat_num):
        action = 'allin'
        amount = 0
        return action, amount