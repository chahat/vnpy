# WebTrader Instructions for use

**Development author：cccbbbaaab**

## Steps for usage

1. Modify the account and server address in CTP_connect.json
2. Modify the web login username and password in WEB_setting.json
3. Open cmd and run python run.py
4. The browser will open automatically and visit http://127.0.0.1:5000/
5. After entering the username and password in 2, click on “Connect CTP” in the lower left corner.
6. The front end of the web page is basically the same as the regular version of VnTrader.
7. To run the CTA policy, modify the configuration in CTA_setting.json

## file function

* tradingServer.py: A transaction server based on the vnpy.rpc module, including CTP interface and CTA policy module
* webServer.py: a web server based on Flask, which internally accesses the transaction server via the vnpy.rpc client
* run.py: unattended service

## Architecture Design

* Active function call function based on Flask-Restful implementation, data flow:
1. The user clicks on a button in the browser to initiate a Restful function call.
2. The web server receives the Restful request and converts it into an RPC function call and sends it to the transaction server.
3. The transaction server receives the RPC request, executes the specific function logic, and returns the result.
4. The web server returns the result of the Restful request to the browser.

* Passive data push function based on Flask-Socketio, data flow:
1. The event engine of the transaction server forwards an event push and pushes it to the RPC client (web server)
2. After receiving the event push, the web server converts it into json format and sends it through Websocket.
3. The browser receives the pushed data through the Websocket and renders it on the web front end interface.

* The main reasons for dividing the program into two processes include:
1. The calculation of policy operation and data calculation in the transaction server is relatively stressful, and it is necessary to ensure low latency efficiency as much as possible.
2. Web server needs to face Internet access, and the transaction-related logic stripping can better ensure security.