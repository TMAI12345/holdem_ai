from collections import namedtuple
from pokereval.card import Card
from pokereval.hand_evaluator import HandEvaluator
from operator import attrgetter
import csv

TABLE_STATE = namedtuple(
    'table_state', ['table_number', 'round', 'number_players', 'board', 'round_count',
                    'raise_count', 'bet_count', 'total_pot', 'small_blind',
                    'big_blind', 'small_blind_amount', 'big_blind_amount',
                    'last_player', 'last_action', 'last_amount'])

PLAYER_STATE = namedtuple(
    'player_state', ['player_name', 'chips', 'folded', 'allIn', 'isSurvive',
                     'hand', 'reload_count', 'round_bet', 'bet', 'action',
                     'amount', 'phase_raise', 'last_action', 'last_amount'])

STATE = namedtuple('state', ['table_state', 'player_state'])

PREDICT_RANK_DATA = namedtuple(
    'rank_data', ['player_name', 'round', 'number_players', 'board', 'total_pot', 'action',
                  'amount', 'chips', 'hand', 'rank'])

LOG_DATA = namedtuple(
    'log_data', ['player_name', 'table_number', 'round_count', 'phase', 'number_players', 'board', 'total_pot', 'action',
                 'amount', 'chips', 'hand', 'rank', 'big_blind', 'round_bet', 'phase_bet', 'phase_raise', 'last_phase_raise',
                 'last_action', 'last_amount', 'win_money', 'isSB', 'isBB'])


CHAR_SUIT_TO_INT = {
    's': 0,  # spades
    'h': 13,  # hearts
    'd': 26,  # diamonds
    'c': 39,  # clubs
}
# " {'23456789TJQKA'} + {'shdc''} (note: lower case) "
CHAR_RANK_TO_INT = {
    '2': 1,
    '3': 2,
    '4': 3,
    '5': 4,
    '6': 5,
    '7': 6,
    '8': 7,
    '9': 8,
    'T': 9,
    'J': 10,
    'Q': 11,
    'K': 12,
    'A': 0,
}

ACTION_TO_NUM = {
    'check': 0,
    'call': 1,
    'raise': 2,
    'fold': 3,
    'bet': 4,
    'allin': 5
}

NUM_TO_ACTION = {
    0: 'check',
    1: 'call',
    2: 'raise',
    3: 'fold'
}

ROUND_NAME_TO_NUM = {
    "Deal": 0,
    "Flop": 1,
    "Turn": 2,
    "River": 3
}


def getCard(card):
    card_type = card[1]
    cardnume_code = card[0]
    card_num = 0
    card_num_type = 0
    if card_type == 'H':
        card_num_type = 2
    elif card_type == 'S':
        card_num_type = 1
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


def cards_to_index52(cards, card_hot=[0]*52):
    for card in cards:
        suit = Card.SUIT_TO_STRING[card.suit]
        rank = Card.RANK_TO_STRING[card.rank]
        index = CHAR_SUIT_TO_INT[suit] + CHAR_RANK_TO_INT[rank]
        card_hot[index] = 1
    return card_hot


def get_a3c_input(hand, board, round_name, total_pot, my_stack, big_blind, my_cycle_bet):
    cards_index = cards_to_index52(hand)
    cards_index = cards_to_index52(board,cards_index)

    #  covert total_pot and my_stack to big_blind
    total_pot_bb = total_pot / big_blind
    my_stack_bb = my_stack / big_blind

    percentage = HandEvaluator.evaluate_hand(hand, board)


    # E = (state.community_state.totalpot + 2 * state.community_state.to_call)
    #  * percentage # calculate EV
    E = percentage * (total_pot - my_cycle_bet) + \
        (1 - percentage) * -1 * (my_cycle_bet)
    ev = 0
    if E > 0:
        ev = 1

    #  convert round_name to num
    if round_name not in ['Deal','Flop','Turn','River']:
        raise Exception("Error: round_name is not correct")
    if round_name == 'Deal':
        round = 0
    elif round_name == 'Flop':
        round = 1
    elif round_name == 'Turn':
        round = 2
    else:
        round = 3
    round = round / 3  #  normalization

    # return cards_index + [my_rank, round, total_pot_bb, my_stack_bb]
    return cards_index + [round + ev]


def get_rank_data(state, player_index):
    predict_rank_data = PREDICT_RANK_DATA(
        state.player_state[player_index].player_name,
        int(ROUND_NAME_TO_NUM[state.table_state.round]),
        int(state.table_state.number_players),
        state.table_state.board,
        float(state.table_state.total_pot / state.table_state.big_blind_amount),
        int(state.player_state[player_index].action),
        float(state.player_state[player_index].amount / state.table_state.big_blind_amount),
        float(state.player_state[player_index].chips / state.table_state.big_blind_amount),
        state.player_state[player_index].hand,
        0.0  # rank
    )
    return predict_rank_data


def get_current_state(table, players):
    table_state = table.get_table_state()
    player_states = []
    for player in players:
        player_states.append(player.get_player_states())
    state = STATE(table_state, tuple(player_states))
    return state


def get_index_from_player_list(md5_name, players):
    for i, player in enumerate(players):
        if player._player_name == md5_name:
            return i


def state_to_csv(data_type, log_path, data_list):
    # predict_rank_data_list = sorted(predict_rank_data_list, key=attrgetter('player_name')) # base on player_name
    data_dict = player_name_dict(data_list)  # namedtuple to dictionary
    for key, value in data_dict.iteritems():
        # with open(log_path + "{}.csv".format(key), 'a+b') as csvfile:
        with open(log_path + "log.csv", 'a+b') as csvfile:
            writer = csv.writer(csvfile)
            #  create header
            csv_dict = [row for row in csv.DictReader(csvfile)]
            if len(csv_dict) == 0:
                writer.writerow(data_type._fields)

            # writer.writerows(data for data in predict_rank_data_list)
            for row in value:
                data = []
                for name in data_type._fields:
                    #  change the format of cards and board
                    if name == "hand" or name == "board":
                        str = []
                        cards = getattr(row, name)
                        for card in cards:
                            str.append(card_to_str(card))
                        data.append(str)
                    else:
                        data.append(getattr(row, name))
                # print(data)
                writer.writerow(data)
    print("Record log successfully.")


def card_to_str(card):
    return Card.RANK_TO_STRING[card.rank] + Card.SUIT_TO_STRING[card.suit]


def player_name_dict(predict_rank_data_list):  # {player_name: state}
    rank_dict = {}
    for rank_data in predict_rank_data_list:
        player_name = rank_data.player_name
        if rank_dict.has_key(player_name):
            rank_dict[player_name].append(rank_data)
        else:
            rank_dict[player_name] = [rank_data]
    # print rank_dict
    return rank_dict

def str_list_to_card(cards, board):
    hands = []
    boards = []
    for card in cards:
        hands.append(getCard(card))
    for card in board:
        boards.append(getCard(card))
    return hands, boards


def get_log_data(state, player_index):
    # 'log_data', ['player_name', 'round', 'number_players', 'round_count', 'board', 'total_pot', 'action',
    #              'amount', 'chips', 'hand', 'rank', 'big_blind', 'round_bet', 'phase_bet', 'win_money',
    #              'isSB', 'isBB']
    evaluator = HandEvaluator()
    rank = evaluator.evaluate_hand(state.player_state[player_index].hand, state.table_state.board)
    alive_players = [player for player in state.player_state if player.isSurvive]

    phase = ROUND_NAME_TO_NUM[state.table_state.round]
    phase_raise = state.player_state[player_index].phase_raise[phase]
    phase_raise = phase_raise - 1 if state.player_state[player_index].action == 2 else phase_raise
    last_phase_raise = -1 if phase == 0 else state.player_state[player_index].phase_raise[phase - 1]
    # isBTN
    isSB = 1 if state.player_state[player_index].player_name == state.table_state.small_blind else 0
    isBB = 1 if state.player_state[player_index].player_name == state.table_state.big_blind else 0
    log_data = LOG_DATA(
        state.player_state[player_index].player_name,
        int(state.table_state.table_number),
        int(state.table_state.round_count),
        int(ROUND_NAME_TO_NUM[state.table_state.round]),
        int(state.table_state.number_players),
        state.table_state.board,
        float((state.table_state.total_pot - state.player_state[player_index].amount)
              / state.table_state.big_blind_amount),
        int(state.player_state[player_index].action),
        float(state.player_state[player_index].amount / state.table_state.big_blind_amount),
        float((state.player_state[player_index].chips + state.player_state[player_index].amount)
              / state.table_state.big_blind_amount),
        state.player_state[player_index].hand,
        float(rank),
        int(state.table_state.big_blind_amount),
        float((state.player_state[player_index].round_bet - state.player_state[player_index].amount)
              / state.table_state.big_blind_amount),
        float((state.player_state[player_index].bet - state.player_state[player_index].amount)
              / state.table_state.big_blind_amount),
        int(phase_raise),
        int(last_phase_raise),
        int(state.player_state[player_index].last_action),
        float(state.player_state[player_index].last_amount / state.table_state.big_blind_amount),
        0.0,  # win_money
        # isBTN,
        int(isSB),
        int(isBB)
    )
    return log_data
