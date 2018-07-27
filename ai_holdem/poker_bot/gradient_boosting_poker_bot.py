from poker_bot import PokerBot
from sklearn.externals import joblib
from utils.utils import get_log_data, ROUND_NAME_TO_NUM
import pandas as pd
from pokereval.hand_evaluator import HandEvaluator

class GradientBoostingPokerBot(PokerBot):

    def __init__(self):
        self.model = []
        for i in range(4):
            self.model.append(joblib.load("poker_bot_model/GB/GB_model_{}.dat".format(i)))

    def game_over(self, isWin, winChips, data):
        pass

    def declareAction(self, state, minBet, seat_num):
        # X_feature = ["round", "number_players", "total_pot", "chips", "rank", "big_blind",
        #              "round_bet", "phase_bet", "isSB", "isBB"]
        # d = get_log_data(state, seat_num)
        phase = ROUND_NAME_TO_NUM[state.table_state.round]
        number_players = state.table_state.number_players
        big_blind = state.table_state.big_blind_amount
        total_pot = state.table_state.total_pot / big_blind
        chips = state.player_state[seat_num].chips / big_blind
        evaluator = HandEvaluator()
        rank = evaluator.evaluate_hand(state.player_state[seat_num].hand, state.table_state.board)
        round_bet = state.player_state[seat_num].round_bet / big_blind
        phase_bet = state.player_state[seat_num].bet / big_blind
        isSB = 1 if state.player_state[seat_num].player_name == state.table_state.small_blind else 0
        isBB = 1 if state.player_state[seat_num].player_name == state.table_state.big_blind else 0
        features = [phase, number_players, total_pot, chips, rank,
                    big_blind, round_bet, phase_bet, isSB, isBB]
        action = self.model[phase].predict([features])
        if action == 1:
            action = 'call'
        else:
            action = 'fold'
        print action
        amount = 0
        return action, amount


def fit_ml(algo, X_train, y_train, X_test, cv):
        model = algo.fit(X_train, y_train)
        test_pred = model.predict(X_test)
        if (isinstance(algo, (
                GradientBoostingClassifier))):
            probs = model.predict_proba(X_test)[:, 1]
        else:
            probs = "Not Available"
        acc = round(model.score(X_test, y_train) * 100, 2)
        # cross validation
        train_pred = model_selection.cross_val_predict(algo,
                                                       X_train,
                                                       y_train,
                                                       cv=cv,
                                                       n_jobs=-1)
        acc_cv = round(metrics.accuracy_score(y_train, train_pred) * 100, 2)

        # save model to file
        # joblib.dump(model, "GB_model.dat")

        return model, train_pred, test_pred, acc, acc_cv, probs

if __name__ == '__main__':
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn import datasets, model_selection, metrics
    from sklearn.externals import joblib
    import pandas as pd
    import numpy as np
    import time, datetime

    feature_columns = ["phase", "number_players", "board", "total_pot", "action", "amount", "chips", "hand", "rank",
                       "big_blind", "round_bet", "phase_bet", "win_money", "isSB", "isBB"]
    data = pd.read_csv("../log/no fold/log.csv")
    data = data[feature_columns]
    data['play'] = np.where(data['win_money'] > 0, 1, 0)

    X_feature = ["phase", "number_players", "total_pot", "chips", "rank", "big_blind",
                 "round_bet", "phase_bet", "isSB", "isBB"]
    data_list = []
    for i in range(4):
        data_round = data[data['phase'] == i]
        X_train = data_round[X_feature]
        y_train = data_round['play']

        # Gradient Boosting Trees
        start_time = time.time()
        model, train_pred_gbt, test_pred_gbt, acc_gbt, acc_cv_gbt, probs_gbt = fit_ml(GradientBoostingClassifier(),
                                                                                           X_train,
                                                                                           y_train,
                                                                                           X_train,
                                                                                           10)
        print "Round_{} acc: {}".format(i, acc_gbt)
        joblib.dump(model, "../poker_bot_model/GB/GB_model_{}.dat".format(i))

