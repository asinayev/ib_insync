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

opens = [[date.today().strftime("%m/%d/%Y"), 
        t.contract.localSymbol, 
        t.order.action,
        str(t.fills[0].execution.price),
        '',
        str(sum([f.execution.shares for f in t.fills])),
        str(t.orderStatus.status), 
        str(len(t.fills)), 
        str(t.fills[0].execution.time)] for t in ib.trades() 
        if len(t.fills)>0 and all([f.commissionReport.realizedPNL==0 for f in t.fills])] 
closes = {t.contract.localSymbol:t.fills[0].execution.price for t in ib.trades()if (len(t.fills)>0 and any([f.commissionReport.realizedPNL!=0 for f in t.fills]))}

for t in opens:
    if t[1] in closes:
        close_price = str(closes[t[1]])
    else:
        close_price = ""
    if t[2]=='BUY':
        t[2]=str(t[3])
        t[3]=str(close_price)
    else:
        t[2]=close_price

    for order,stocks in order_stocks.items():
        if any(stocks==t[1]):
            t[4]=order
            order_stocks[order]=order_stocks[order][stocks!=t[1]]
            break
    print(','.join(t))

print("#############################")
for sym in closes:
    if sym not in (o[1] for o in opens):
        print(sym,',',closes[sym])
ib.disconnect()


