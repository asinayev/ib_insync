from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='limit buy stocks at listed limit prices on open and then sell at market close')

parser.add_argument('--exceptions', type=str, required=True)
parser.add_argument('--ordertype', type=str, required=True, choices=['MOC','MKT']) 
parser.add_argument('--timeinforce', type=str, required=True, choices=['OPG','DAY','close']) 
parser.add_argument('--real', dest='real', action = 'store_true') 
#File needs columns:
# symbol

args = parser.parse_args()

ib = initiate.initiate_ib(args, 133) 

stockdict = csv.DictReader(open(args.exceptions, "r"))
exception_tickers = [row['symbol'] for row in stockdict]

openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}

for sym in position_tickers:
    if sym not in exception_tickers:
        position = openPositions[position_tickers[sym]]
        contr = Stock(sym, exchange='SMART', currency='USD')
        ib.qualifyContracts(contr)
        if position.position>0:
            order =Order(action = 'SELL', orderType = args.ordertype, totalQuantity = position.position, tif = args.timeinforce  )
        elif position.position<0:
            order =Order(action = 'BUY', orderType = args.ordertype, totalQuantity = -(position.position) , tif = args.timeinforce )
        ib.placeOrder(contr, order)
        print("ordering close for "+sym)

ib.disconnect()
