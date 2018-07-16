# import poker_bot
import poker_socket
import threading
from poker_bot.custom_poker_bot import CustomPokerBot

def play(socket_list):
    for s in socket_list:
        bot_do_action = lambda: s.doListen()
        thread = threading.Thread(target=bot_do_action)
        thread.start()


if __name__ == '__main__':
    playerName = ["5f4387a3b13e40419c696980d1c75147"]
    # connect_url = "ws://poker-dev.wrs.club:3001/"
    # connect_url = "ws://poker-training.vtr.trendnet.org:3001/"
    connect_url = "ws://poker-battle.vtr.trendnet.org:3001"

    aggresive_threshold = 0.5
    passive_threshold = 0.7
    preflop_threshold_Loose = 0.3
    preflop_threshold_Tight = 0.5
    #
    # simulation_number = 100
    bet_tolerance = 0.1

    # Aggresive -loose
    # myPokerBot = poker_bot.PotOddsPokerBot(preflop_threshold_Loose, aggresive_threshold, bet_tolerance)
    # myPokerBot = poker_bot.PotOddsPokerBot(preflop_threshold_Tight, aggresive_threshold, bet_tolerance)
    # myPokerBot = poker_bot.PotOddsPokerBot(preflop_threshold_Loose, passive_threshold, bet_tolerance)
    # myPokerBot = poker_bot.PotOddsPokerBot(preflop_threshold_Tight, passive_threshold, bet_tolerance)

    # myPokerBot = poker_bot.FreshPokerBot()
    # myPokerBot = poker_bot.MontecarloPokerBot(simulation_number)

    myPokerBot = CustomPokerBot(preflop_threshold_Tight, aggresive_threshold, bet_tolerance)
    socket_list = []
    for i in range(len(playerName)):
        # socket = poker_socket.TMSocket(playerName[i], connect_url, myPokerBot)
        socket = poker_socket.PredictRankSocket(playerName[i], connect_url, myPokerBot)
        socket_list.append(socket)
    play(socket_list)
