class PokerBot(object):

    def declareAction(self, state, minBet, seat_num):
        err_msg = self.__build_err_msg("declare_action")
        raise NotImplementedError(err_msg)

    def game_over(self,isWin,winChips, data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)

    def set_data(self, data, pre_player_action):
        err_msg = self.__build_err_msg("set_data")
        raise NotImplementedError(err_msg)