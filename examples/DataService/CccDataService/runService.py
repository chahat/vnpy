# encoding: UTF-8

"""
Timed service, which can be run unattended, and automatically downloads updated historical market data to the database every day.
"""
from __future__ import print_function

from dataService import *


if __name__ == '__main__':
    taskCompletedDate = None
    
    taskTime = datetime.time(hour=22, minute=0)
    
    # EnterTheMainLoop
    while True:
        t = datetime.datetime.now()
        
        # Perform data download operation after reaching the task download time every day
        if t.time() > taskTime and (taskCompletedDate is None or t.date() != taskCompletedDate):
            end = t.strftime('%Y%m%d')
            start = (t - datetime.timedelta(1)).strftime('%Y%m%d')
            
            # DownloadKLineDataForThePast24Hours
            downloadAllMinuteBar(start, end)
            
            # UpdateTheDateTheTaskWasCompleted
            taskCompletedDate = t.date()
        else:
            print(u'CurrentTime %s，TaskTiming %s' %(t, taskTime))
    
        time.sleep(60)