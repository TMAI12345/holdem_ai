import json
from websocket import create_connection

class PokerSocket(object):

    # def __init__(self,playerName,connect_url, pokerbot):
    #     self.pokerbot=pokerbot
    #     self.playerName=playerName
    #     self.connect_url=connect_url

    def getAction(self,data):
        err_msg = self.__build_err_msg("get_action")
        raise NotImplementedError(err_msg)

    def takeAction(self,action, data):
        err_msg = self.__build_err_msg("take_action")
        raise NotImplementedError(err_msg)
    def doListen(self):
        err_msg = self.__build_err_msg("do_listen")
        raise NotImplementedError(err_msg)