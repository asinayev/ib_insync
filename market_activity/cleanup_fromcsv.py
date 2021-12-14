from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import argparse
import csv
import pandas as pd

# Instantiate the parser
parser = argparse.ArgumentParser(description='cancel sell orders for unopened positions')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 13)
openTrades = ib.reqOpenTrades()
openPositions = ib.positions()
position_ticker = [p.contract for p in openPositions]

for stockname in stockdict.symbol:
    if stockname == 
for ord in openOrders: 

    ib.cancelOrder(OtC)
for row in stockdict:
    assert(row['date']==(datetime.today()-timedelta(days=1)).strftime('%Y-%m-%d'))
    row['contract']=Stock(row['symbol'], exchange='SMART', currency='USD')
    ib.qualifyContracts(row['contract'])
    quantity = int(cash_per_stock/float(row['purchase']))
    buy_order=Order(action = 'BUY', orderType = 'LMT', totalQuantity = quantity , tif = 'OPG', lmtPrice=row['purchase'])
    buy_trade = ib.placeOrder(row['contract'], buy_order)
    #sell_order=Order(action = 'SELL', orderType = 'MOC', totalQuantity = quantity )
    #sell_trade = ib.placeOrder(row['contract'], sell_order)

ib.disconnect()

