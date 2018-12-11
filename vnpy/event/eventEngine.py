# encoding: UTF-8

# systemModule
from __future__ import print_function
from queue import Queue, Empty
from threading import Thread
from time import sleep
from collections import defaultdict

# 第三方模块
from qtpy.QtCore import QTimer

# 自己开发的模块
from .eventType import *


########################################################################
class EventEngine(object):
    """
    eventDrivenEngine
    All variables in the event-driven engine are set to be private, this is to prevent carelessness
    The value or state of these variables has been modified externally, resulting in bug。
    
    variableDescription
    __queue：Private variable event queue
    __active：Private variable event engine switch
    __thread：Private variable event processing thread
    __timer：Private variable timer
    __handlers：Private variable event handler dictionary
    
    
    methodDescription
    __run: Private method, event processing thread running continuously
    __process: Private method, handling events, calling listener functions registered in the engine
    __onTimer：Private method, after the timer fixed event interval is triggered, the timer event is stored in the event queue.
    start: Public method start the engine
    stop：Public method stop the engine
    register：Public method, register the listener function in the engine
    unregister：Public method, logout listener function to the engine
    put：Public method to store new events into the event queue
    
    The event listener function must be defined as only one input parameter event Object ie：
    
    function
    def func(event)
        ...
    
    objectMethod
    def method(self, event)
        ...
        
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Initialize the event engine"""
        # EventQueue
        self.__queue = Queue()
        
        # EventEngineSwitch
        self.__active = False
        
        # EventProcessingThread
        self.__thread = Thread(target = self.__run)
        
        # TimerForTriggeringTimerEvents
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.__onTimer)
        
        # Here __handlers is a dictionary that holds the corresponding event call relationship.
        # The value corresponding to each key is a list, and the function function of monitoring the event is saved in the list.
        self.__handlers = defaultdict(list)
        
        # __generalHandlers Is a list to hold the generic callback function (all events are called)
        self.__generalHandlers = []
        
    #----------------------------------------------------------------------
    def __run(self):
        """EngineRunning"""
        while self.__active == True:
            try:
                event = self.__queue.get(block = True, timeout = 1)  # Get the blocking time of the event set to 1 second
                self.__process(event)
            except Empty:
                pass
            
    #----------------------------------------------------------------------
    def __process(self, event):
        """HandlingEvents"""
        # Check if there is a handler for listening to this event
        if event.type_ in self.__handlers:
            # If it exists, the event is passed to the handler in order.
            [handler(event) for handler in self.__handlers[event.type_]]
            
            # The above statement is a Python list parsing method, and the corresponding regular loop is:
            #for handler in self.__handlers[event.type_]:
                #handler(event) 
        
        # Call the generic handler for processing
        if self.__generalHandlers:
            [handler(event) for handler in self.__generalHandlers]
               
    #----------------------------------------------------------------------
    def __onTimer(self):
        """StoreTimerEventsIntoTheEventQueue"""
        # Create a timer event
        event = Event(type_=EVENT_TIMER)
        
        # Store timer events in the queue
        self.put(event)    

    #----------------------------------------------------------------------
    def start(self, timer=True):
        """
        EngineStart
        timer：Do you want to start the timer
        """
        # Set the engine to start
        self.__active = True
        
        # StartEventProcessingThread
        self.__thread.start()
        
        # Start timer, timer event interval is set to 1 second by default
        if timer:
            self.__timer.start(1000)
    
    #----------------------------------------------------------------------
    def stop(self):
        """StopTheEngine"""
        # SetTheEngineToStop
        self.__active = False
        
        # StopTimer
        self.__timer.stop()
        
        # Waiting for the event processing thread to exit
        self.__thread.join()
            
    #----------------------------------------------------------------------
    def register(self, type_, handler):
        """RegisterEventHandlerListener"""
        # Try to get a list of handlers for this event type, if none defaultDict Will automatically create a new one list
        handlerList = self.__handlers[type_]
        
        # Register the event if the processor to be registered is not in the processor list for this event
        if handler not in handlerList:
            handlerList.append(handler)
            
    #----------------------------------------------------------------------
    def unregister(self, type_, handler):
        """LogoutEventHandlerListener"""
        # Try to get the list of handlers corresponding to the event type. If not, ignore the logout request.
        handlerList = self.__handlers[type_]
            
        # RemoveIfTheFunctionExistsInTheList
        if handler in handlerList:
            handlerList.remove(handler)

        # If the function list is empty, remove the event type from the engine
        if not handlerList:
            del self.__handlers[type_]
            
    #----------------------------------------------------------------------
    def put(self, event):
        """DepositEventsIntoTheEventQueue"""
        self.__queue.put(event)
        
    #----------------------------------------------------------------------
    def registerGeneralHandler(self, handler):
        """RegisterAGenericEventHandlerListener"""
        if handler not in self.__generalHandlers:
            self.__generalHandlers.append(handler)
            
    #----------------------------------------------------------------------
    def unregisterGeneralHandler(self, handler):
        """LogoutGeneralEventHandlerListener"""
        if handler in self.__generalHandlers:
            self.__generalHandlers.remove(handler)
        


########################################################################
class EventEngine2(object):
    """
    Timer uses python threaded event driven engine
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """InitializeTheEventEngine"""
        # EventQueue
        self.__queue = Queue()
        
        # EventEngineSwitch
        self.__active = False
        
        # EventProcessingThread
        self.__thread = Thread(target = self.__run)
        
        # TimerForTriggeringTimerEvents
        self.__timer = Thread(target = self.__runTimer)
        self.__timerActive = False                      # Timer working status
        self.__timerSleep = 1                           # Timer trigger interval (default 1 second)
        
        # Here __handlers is a dictionary that holds the corresponding event call relationship.
        # The value corresponding to each key is a list, and the function function of monitoring the event is saved in the list.
        self.__handlers = defaultdict(list)
        
        # __generalHandlers Is a list to hold the generic callback function (all events are called)
        self.__generalHandlers = []        
        
    #----------------------------------------------------------------------
    def __run(self):
        """EngineRunning"""
        while self.__active == True:
            try:
                event = self.__queue.get(block = True, timeout = 1)  # Get the blocking time of the event set to 1 second
                self.__process(event)
            except Empty:
                pass
            
    #----------------------------------------------------------------------
    def __process(self, event):
        """HandlingEvents"""
        # Check if there is a handler for listening to this event
        if event.type_ in self.__handlers:
            # If it exists, the event is passed to the handler in order.
            [handler(event) for handler in self.__handlers[event.type_]]
            
            # The above statement is a Python list parsing method, and the corresponding regular loop is:
            #for handler in self.__handlers[event.type_]:
                #handler(event) 
                
        # Call the generic handler for processing
        if self.__generalHandlers:
            [handler(event) for handler in self.__generalHandlers]        
               
    #----------------------------------------------------------------------
    def __runTimer(self):
        """ALoopFunctionRunningInATimerThread"""
        while self.__timerActive:
            # CreateATimerEvent
            event = Event(type_=EVENT_TIMER)
        
            # StoreTimerEventsInTheQueue
            self.put(event)    
            
            # Wait
            sleep(self.__timerSleep)

    #----------------------------------------------------------------------
    def start(self, timer=True):
        """
        EngineStart
        timer：Do you want to start the timer?
        """
        # SetTheEngineToStart
        self.__active = True
        
        # StartEventProcessingThread
        self.__thread.start()
        
        # Start timer, timer event interval is set to 1 second by default
        if timer:
            self.__timerActive = True
            self.__timer.start()
    
    #----------------------------------------------------------------------
    def stop(self):
        """StopTheEngine"""
        # SetTheEngineToStop
        self.__active = False
        
        # StopTimer
        self.__timerActive = False
        self.__timer.join()
        
        # WaitingForTheEventProcessingThreadToExit
        self.__thread.join()
            
    #----------------------------------------------------------------------
    def register(self, type_, handler):
        """RegisterEventHandlerListener"""
        # Try to get the list of handlers corresponding to the event type. If no defaultDict is created, a new list will be created automatically.
        handlerList = self.__handlers[type_]
        
        # Register the event if the processor to be registered is not in the processor list for this event
        if handler not in handlerList:
            handlerList.append(handler)
            
    #----------------------------------------------------------------------
    def unregister(self, type_, handler):
        """LogoutEventHandlerListener"""
        # Try to get the list of handlers corresponding to the event type. If not, ignore the logout request.
        handlerList = self.__handlers[type_]
            
        # RemoveIfTheFunctionExistsInTheList
        if handler in handlerList:
            handlerList.remove(handler)

        # If the function list is empty, remove the event type from the engine
        if not handlerList:
            del self.__handlers[type_]  
        
    #----------------------------------------------------------------------
    def put(self, event):
        """DepositEventsIntoTheEventQueue"""
        self.__queue.put(event)

    #----------------------------------------------------------------------
    def registerGeneralHandler(self, handler):
        """RegisterAGenericEventHandlerListener"""
        if handler not in self.__generalHandlers:
            self.__generalHandlers.append(handler)
            
    #----------------------------------------------------------------------
    def unregisterGeneralHandler(self, handler):
        """LogoutGeneralEventHandlerListener"""
        if handler in self.__generalHandlers:
            self.__generalHandlers.remove(handler)


########################################################################
class Event:
    """EventObject"""

    #----------------------------------------------------------------------
    def __init__(self, type_=None):
        """Constructor"""
        self.type_ = type_      # EventType
        self.dict_ = {}         # DictionaryForSavingSpecificEventData


#----------------------------------------------------------------------
def test():
    """TestFunction"""
    import sys
    from datetime import datetime
    from qtpy.QtCore import QCoreApplication

    def simpletest(event):
        print(u'Handling timer events fired every second：{}'.format(str(datetime.now())))
    
    app = QCoreApplication(sys.argv)
    
    ee = EventEngine2()
    #ee.register(EVENT_TIMER, simpletest)
    ee.registerGeneralHandler(simpletest)
    ee.start()
    
    app.exec_()
    
    
# RunTheScriptDirectlyToTest
if __name__ == '__main__':
    test()
