from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='cancel orders for unopened positions and order closes for opened positions')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--limitclose', dest='limitclose', action = 'store_true') 
parser.add_argument('--ordertype', type=str, required=True, choices=['LOC','MOC','LMT','MKT']) 
parser.add_argument('--timeinforce', type=str, required=True, choices=['OPG','DAY','none']) 
parser.set_defaults(feature=False)
args = parser.parse_args()

stocks = csv.DictReader(open(args.file, "r"))
stock_tickers = [row['symbol'] for row in stocks]

ib = initiate.initiate_ib(args, 14)
# Cancel orders that did not execute intended for opening
openOrders = ib.openOrders()
for OtC in openOrders:
    if OtC.tif=='OPG':
        ib.cancelOrder(OtC)

# Order positions from this strategy to be closed 
openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}

for sym in stock_tickers:
    if sym in position_tickers:
        position = openPositions[position_tickers[sym]]
        contr = Stock(sym, exchange='SMART', currency='USD')
        ib.qualifyContracts(contr)
        if position.position>0 and args.limitclose:
            print("Closing stock "+sym+" at .98 limit")
            order =Order(action = 'SELL', orderType = 'LOC', totalQuantity = position.position, lmtPrice = round(position.avgCost*0.98,2) )
        elif position.position>0 and not args.limitclose:
            order =Order(action = 'SELL', orderType = args.ordertype, totalQuantity = position.position, tif = args.timeinforce  )
        elif position.position<0:
            order =Order(action = 'BUY', orderType = args.ordertype, totalQuantity = -(position.position) , tif = args.timeinforce )
        ib.placeOrder(contr, order)
        print("ordering close for "+sym)

ib.disconnect()

