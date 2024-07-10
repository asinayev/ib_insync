from ib_async import *

def initiate_ib(args, cid):
    ib=IB()
    if args.real: 
        port=4001
    else:
        port=4002
    ib.connect('127.0.0.1', port, clientId=cid, timeout=15)
    return ib
