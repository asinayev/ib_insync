from ib_insync import *
from connection import initiate

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Cancel all open orders')

parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 13)

x = ib.reqAllOpenOrders()
print(len(x))
for OtC in x: 
    ib.cancelOrder(OtC)
ib.disconnect()


