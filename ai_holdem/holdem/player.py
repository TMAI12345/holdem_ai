import poker_bot
from utils.utils import PLAYER_STATE, ACTION_TO_NUM, getCard


class Player(object):
    def __init__(self, player_name, chips, model=poker_bot.FreshPokerBot):
        self._player_name = player_name
        self._chips = chips
        self._begin_round_chips = chips
        self._folded = False
        self._allIn = False
        self._isSurvive = True
        self._reload_count = 0
        self._round_bet = 0
        self._bet = 0
        self._cards = []
        self._action = 0
        self._amount = 0
        self.model = model
        # self._rank = 0
        # self._winMoney = 0

    # def init(self):
    #     self._chips = 0

    # def reset_player(self):
    #     self._player_name = ""
    #     self._chips = 0
    #     self._folded = False
    #     self._allIn = False
    #     self._isSurvive = False
    #     self._reload_count = 2
    #     self._round_bet = 0
    #     self._bet = 0
    #     self._cards = []
    #     self.action = ""

    # def end_round(self, player_data):
    #     self._all_cards = player_data['hand']['cards']  # [self]
    #     self._rank = player_data['hand']['rank']
    #     self._message = player_data['hand']['message']
    #     self._winMoney = player_data['winMoney']
    #     self._isOnline = player_data['isOnline']


    def new_round(self, player_data):
        self.update_by_state(player_data)
        # self._begin_round_chips = self._chips
        return False

    def update_by_state(self, player):
        if self._player_name != player['playerName']:
            raise ("Error: player name is not sync")
        self._chips = player['chips']
        self._folded = player['folded']
        self._allIn = player['allIn']
        self._isSurvive = player['isSurvive']
        self._reload_count = player['reloadCount']
        self._round_bet = player['roundBet'] + player['bet']
        self._bet = player['bet']
        cards = []
        if 'cards' in player:
            for card in player['cards']:
                cards.append(getCard(card))
        self._cards = cards

    def do_action(self, state, minBet, seat_num):
        action, amount = self.model.declareAction(state, minBet, seat_num)
        return action, amount

    def update_action(self, actionData):
        self._action = ACTION_TO_NUM[actionData['action']]
        amount = 0
        if 'amount' in actionData:
            amount = actionData['amount']
        self._amount = amount
        self._round_bet += amount

    def get_player_states(self):
        player_features = PLAYER_STATE(
            self._player_name,
            int(self._chips),
            bool(self._folded),
            bool(self._allIn),
            bool(self._isSurvive),
            self._cards,
            int(self._reload_count),
            int(self._round_bet),
            int(self._bet),
            int(self._action),
            int(self._amount),
        )
        return player_features
