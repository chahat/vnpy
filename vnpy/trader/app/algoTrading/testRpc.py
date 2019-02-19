# encoding: UTF-8

from __future__ import print_function
from time import sleep

from six.moves import input
from vnpy.rpc import RpcClient
from vnpy.trader.vtConstant import OFFSET_OPEN, DIRECTION_LONG


########################################################################
class TestClient(RpcClient):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, reqAddress, subAddress):
        """Constructor"""
        super(TestClient, self).__init__(reqAddress, subAddress)

    #----------------------------------------------------------------------
    def callback(self, topic, data):
        """回调函数实现"""
        print(('client received topic:', topic, ', data:', data))


if __name__ == '__main__':
    reqAddress = 'tcp://localhost:8899'
    subAddress = 'tcp://localhost:9988'

    tc = TestClient(reqAddress, subAddress)
    tc.subscribeTopic('')
    tc.start()

    setting = {
        'templateName': 'BestLimit',
        'vtSymbol': 'XBTUSD',
        'volume': 1,
        'direction': DIRECTION_LONG,
        'offset': OFFSET_OPEN
    }
    algoName = tc.addAlgo(setting)
    print(u'StartAlgorithmInstanceName', algoName)
    
    sleep(5)
    tc.stopAlgo(algoName)
    print(u'StopAlgorithm')
    
    input()
