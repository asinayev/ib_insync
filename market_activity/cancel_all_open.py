from ib_async import *
from connection import initiate

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Cancel all open orders')

parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--justprint', dest='justprint', action='store_true')
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 14)
ib.client.reqAllOpenOrders()
dummy = ib.reqOpenOrders()

if args.justprint:
    x=ib.openTrades()
    for OtC in x: 
        print(OtC.order.action, OtC.order.totalQuantity, OtC.contract.symbol, OtC.order.orderType, OtC.order.lmtPrice, OtC.order.tif, "################################")
else:
    x = ib.openOrders()
    print(len(x), "################################")
    for OtC in x: 
        ib.cancelOrder(OtC)
    print('canceled')
ib.disconnect()


