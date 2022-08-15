from ib_insync import *
from connection import initiate
from datetime import date
from glob import glob 
from pandas import read_csv

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Cancel all open orders')


parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('-c','--certain', action='append', help='Trades certainly executed', required=False)
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 14)
order_csvs = {o:read_csv('/tmp/stonksanalysis/'+o+'.csv') for o in args.certain}
order_stocks = {order:csv.symbol for order,csv in order_csvs.items()}

trade_info = [[date.today().strftime("%m/%d/%Y"), 
        t.contract.localSymbol, 
        t.order.action,
        str(t.fills[0].execution.price),
        '',
        str(sum([f.execution.shares for f in t.fills])),
        str(t.orderStatus.status), 
        str(len(t.fills)), 
        str(t.fills[0].execution.time)] for t in ib.trades() if len(t.fills)>0 ] 
for t in trade_info:
    if t[2]=='BUY':
        t[2]=t[3]
        t[3]=''
    else:
        t[2]=''

    for order,stocks in order_stocks.items():
        if any(stocks==t[1]):
            t[4]=order
            order_stocks[order]=order_stocks[order][stocks!=t[1]]
            break
    print(','.join(t))
ib.disconnect()


