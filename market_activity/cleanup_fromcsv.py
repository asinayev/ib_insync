from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='cancel orders for unopened positions and order closes for opened positions')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

corr_stocks = csv.DictReader(open(args.file, "r"))
corr_stock_tickers = [row['symbol'] for row in corr_stocks]

ib = initiate.initiate_ib(args, 14)
# Cancel orders that did not execute intended for opening
openOrders = ib.openOrders()
for OtC in openOrders:
    if OtC.tif=='OPG':
        ib.cancelOrder(OtC)

# Order positions from this strategy to be closed at market close
openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}

for sym in corr_stock_tickers:
    if sym in position_tickers:
        position = openPositions[position_tickers[sym]]
        contr = Stock(sym, exchange='ISLAND', currency='USD')
        ib.qualifyContracts(contr)
        if position.position>0:
            order =Order(action = 'SELL', orderType = 'MOC', totalQuantity = position.position )
        elif position.position==0:
            print(sym+" already closed")
        else:
            order =Order(action = 'BUY', orderType = 'MOC', totalQuantity = -(position.position) )
        ib.placeOrder(contr, order)
        print("ordering close for "+sym)

ib.disconnect()

