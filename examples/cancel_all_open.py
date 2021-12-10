from ib_insync import *

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Cancel all open orders')

parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

ib=IB()
if args.real: 
    port=4001
else:
    port=4002
ib.connect('127.0.0.1', port, clientId=122)
x = ib.reqAllOpenOrders()
print(len(x))
for OtC in x: 
    ib.cancelOrder(OtC)
ib.disconnect()


