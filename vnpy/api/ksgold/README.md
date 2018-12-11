# vn.ksgold

### Introduction
The Python package of Kingstar Gold T+D interface (SPD) needs to copy the SLEdll folder to the folder where python.exe is located.

### Description
This interface looks very simple like CTP, but there are quite a lot of pits:
1. Flow control with up to 5 operations per second (authors seem to trigger flow control with 3 strokes), and it seems that the underlying mode is synchronous, meaning that if the user invokes the delegate function to encounter flow control restrictions, then the delegate waits The current thread will block during the process, causing the program to be stuck in the interface (because the main thread is stuck)

2. OnRtnOrder returns very few data fields, including only the commission number and the current state, and will only be pushed when the commission is released and the delegate is revoked. The commission is not pushed when the transaction is completed. The user needs to combine the data of OnRtnTrade to restore the latest status of the current commission.

3. After login, the historical transaction and the delegate's active push will not be provided. Users need to query it themselves, and the query also has flow control (1 second/time).

If you plan to develop your own recommendations to refer to ksgoldGateway in vn.trader, you can step on the pit.

### API version

Date: 2014-07-21

Name: api release _20140721 (golden trader application interface)

Source: Provided by Shanghai Pudong Development Bank Technology Department