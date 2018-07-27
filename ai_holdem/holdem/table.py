from utils.utils import TABLE_STATE, getCard


class Table():
    def __init__(self, table_number):
        self._table_number = table_number
        self._round = ""  # Deal, Flop, Turn, River.
        self._number_players = 0
        self._board = []
        self._round_count = 0
        self._raise_count = 0
        self._bet_count = 0
        self._total_bet = 0
        self._small_blind = ""
        self._big_blind = ""
        self._small_blind_amount = 0
        self._big_blind_amount = 0
        self.last_player = ""
        self.last_action = ""
        self.last_amount = 0

    # def init(self):
    #     self._table_number = ""
    #     self._round = ""  # Deal, Flop, Turn, River.
    #     self._board = []
    #     self._round_count = 0
    #     self._raise_count = 0
    #     self._bet_count = 0
    #     self._total_bet = 0
    #     # self._small_blind_name = ""
    #     # self._big_blind_name = ""
    #     # self._small_blind = 0
    #     # self._big_blind = 0
    #     self.players = []
    #
    # def reset_table(self):
    #     self.init()

    def update_table_status(self, data):  # community cards are dealt
        table_data = data['table']
        player_data = data['players']
        if self._table_number != table_data['tableNumber']:
            raise Exception("Error: Table number is not syncing.")
        if 'action' in data:
            self.last_player = data['action']['playerName']
            self.last_action = data['action']['action']
            if 'amount' in data['action']:
                self.last_amount = data['action']['amount']
            else:  # fold
                self.last_amount = 0
        else:
            self.last_player = ""
            self.last_action = ""
            self.last_amount = 0
        self._round = table_data['roundName']
        self._number_players = len([player for player in player_data if player['isSurvive']])
        board = []
        for card in table_data['board']:
            board.append(getCard(card))
        self._board = board
        self._round_count = table_data['roundCount']
        self._raise_count = table_data['raiseCount']
        self._bet_count = table_data['betCount']
        if 'totalBet' in table_data:
            self._total_bet = table_data['totalBet']
        self._small_blind = table_data['smallBlind']['playerName']
        self._big_blind = table_data['bigBlind']['playerName']
        self._small_blind_amount = 1.0 * table_data['smallBlind']['amount']
        self._big_blind_amount = 1.0 * table_data['bigBlind']['amount']

    def get_table_state(self):
        table_state = TABLE_STATE(
            int(self._table_number),
            str(self._round),
            int(self._number_players),
            self._board,
            int(self._round_count),
            int(self._raise_count),
            int(self._bet_count),
            int(self._total_bet),
            str(self._small_blind),
            str(self._big_blind),
            float(self._small_blind_amount),
            float(self._big_blind_amount),
            str(self.last_player),
            str(self.last_action),
            int(self.last_amount)
        )
        return table_state
