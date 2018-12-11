# encoding: UTF-8

from __future__ import print_function
import sys
try:
    reload(sys)  # Python 2
    sys.setdefaultencoding('utf8')
except NameError:
    pass         # Python 3

import multiprocessing
from time import sleep
from datetime import datetime, time

from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_ERROR
from vnpy.trader.vtEngine import MainEngine, LogEngine
from vnpy.trader.gateway import ctpGateway
from vnpy.trader.app import ctaStrategy
from vnpy.trader.app.ctaStrategy.ctaBase import EVENT_CTA_LOG



#----------------------------------------------------------------------
def processErrorEvent(event):
    """
    Handling error events
    After each login, the error message will be pushed all the time that has been generated on the current day, so it is not suitable for writing logs.
    """
    error = event.dict_['data']
    print(u'ErrorCode：%s，ErrorMessage：%s' %(error.errorID, error.errorMsg))
    
#----------------------------------------------------------------------
def runChildProcess():
    """ChildProcessRunFunction"""
    print('-'*20)
    
    # CreateALogEngine
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()
    le.addFileHandler()
    
    le.info(u'StartTheCTAPolicyToRunTheChildProcess')
    
    ee = EventEngine2()
    le.info(u'EventEngineCreatedSuccessfully')
    
    me = MainEngine(ee)
    me.addGateway(ctpGateway)
    me.addApp(ctaStrategy)
    le.info(u'TheMainEngineWasCreatedSuccessfully')
    
    ee.register(EVENT_LOG, le.processLogEvent)
    ee.register(EVENT_CTA_LOG, le.processLogEvent)
    ee.register(EVENT_ERROR, processErrorEvent)
    le.info(u'RegistrationLogEventListener')
    
    me.connect('CTP')
    le.info(u'ConnectToTheCTPInterface')
    
    sleep(10)                       # WaitingForCTPInterfaceInitialization
    me.dataEngine.saveContracts()   # SaveContractInformationToFile
    
    cta = me.getApp(ctaStrategy.appName)
    
    cta.loadSetting()
    le.info(u'CTAStrategyLoadedSuccessfully')
    
    cta.initAll()
    le.info(u'CTAPolicyInitializationSucceeded')
    
    cta.startAll()
    le.info(u'CTAPolicyStartedSuccessfully')
    
    while True:
        sleep(1)

#----------------------------------------------------------------------
def runParentProcess():
    """ParentProcessRunFunction"""
    # CreateALogEngine
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()
    
    le.info(u'StartTheCTAPolicyDaemonParentProcess')
    
    DAY_START = time(8, 45)         # DateStartAndStopTime
    DAY_END = time(15, 30)
    
    NIGHT_START = time(20, 45)      # NightDiskStartAndStopTime
    NIGHT_END = time(2, 45)
    
    p = None        # ChildProcessHandle
    
    while True:
        currentTime = datetime.now().time()
        recording = False
        
        # DetermineTheCurrentTimePeriod
        if ((currentTime >= DAY_START and currentTime <= DAY_END) or
            (currentTime >= NIGHT_START) or
            (currentTime <= NIGHT_END)):
            recording = True
        
        # RecordingTimeRequiresStartingTheChildProcess
        if recording and p is None:
            le.info(u'PromoterProcess')
            p = multiprocessing.Process(target=runChildProcess)
            p.start()
            le.info(u'TheChildProcessStartedSuccessfully')
            
        # ExitTheChildProcessAtNonRecordingTime
        if not recording and p is not None:
            le.info(u'CloseChildProcess')
            p.terminate()
            p.join()
            p = None
            le.info(u'ChildProcessClosedSuccessfully')
            
        sleep(5)


if __name__ == '__main__':
    runChildProcess()
    
    # Although it is also unattended, it is strongly recommended to manually check it at startup every day, responsible for your own PNL.
    #runParentProcess()
