# vn.rpc

###Introduction

Provides RPC modules for cross-process service calls, and supports active data push from the server to the client for implementing multi-process decoupling of modules under the vn.py framework.

### Description

1. Use zmq as the underlying communication library

2. Currently supports two data serialization schemes: msgpack (default) and json. Users can add other schemes themselves in RpcObject.

3. The client and server implement cross-process service calls through the REQ-REP mode.

4. Client and server implement active data push through SUB-PUB mode

5. RPCClient's send and RpcServer's publish function are not multi-thread safe. Users need to lock themselves when using in multi-threading, otherwise it may cause the bottom of zmq to crash.

6. Considering that the main application scenario of vn.rpc is native multi-process or distributed architecture in the LAN, the network reliability is high, so the heartbeat function is not provided in the module, and the user can add according to his own needs.
