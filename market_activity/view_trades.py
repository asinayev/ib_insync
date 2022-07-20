from ib_insync import *
from connection import initiate
from datetime import date

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Cancel all open orders')

parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 14)

x = [[date.today().strftime("%m/%d/%Y"), t.contract.localSymbol, t.order.action,str(t.fills[0].execution.price),str(t.fills[0].execution.shares),str(t.orderStatus.status), str(len(t.fills))] for t in ib.trades() if len(t.fills)>0 ] 
for t in x:
    if t[2]=='BUY':
        t[2]=t[3]
        t[3]=''
    else:
        t[2]=''
    print(','.join(t))
ib.disconnect()


