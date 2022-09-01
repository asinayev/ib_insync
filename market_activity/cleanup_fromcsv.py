from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta
import functools
import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='order closes for opened positions')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--closetype', type=str, required=True, choices=['last_high_eod','mkt_eod']) 
parser.add_argument('--illiquid', dest='illiquid', action='store_true') 
parser.add_argument('--currentstatusfile', type=str, required=False) 
parser.add_argument('--assettype', type=str, required=False) 
parser.set_defaults(feature=False)
args = parser.parse_args()

# Import data
stocks = csv.DictReader(open(args.file, "r"))
stock_tickers = [row['symbol'] for row in stocks if 'asset_type' not in row or row['asset_type']==args.assettype]

current_moves = csv.DictReader(open(args.currentstatusfile, "r"))
current_moves = {row['symbol']:row for row in current_moves}

# Open connection
ib = initiate.initiate_ib(args, 14)
openTrades = ib.openTrades()

# Order positions from this strategy to be closed 
openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}
open_tickers = [t.contract.symbol for t in ib.openTrades()]

def order_conditions(args, position, lmt_price=None, contr):
    time_condition = TimeCondition(isMore=True, time=datetime.today().strftime('%Y%m%d')+' 15:50:00 EST', conjunction='a')
    price_condition = PriceCondition(1,conjunction='a', isMore=True,
                        price=lmt_price, 
                        exch='SMART', conId=contr.conId)
    if args.illiquid and args.closetype=='last_high_eod' and position>0:
        return Order(action="SELL",
                     orderType="LMT",
                     algoStrategy='Adaptive', 
                     algoParams = [TagValue('adaptivePriority', 'Patient')],
                     totalQuantity = abs(position), 
                     tif = "DAY",
                     conditions = [time_condition],
                     lmtPrice=lmt_price)
    elif args.closetype=='last_high_eod' and position<0:
        return Order(action="BUY",
                     orderType="MKT",
                     algoStrategy='Adaptive', 
                     algoParams = [TagValue('adaptivePriority', 'Patient')],
                     totalQuantity = abs(position), 
                     tif = "DAY",
                     conditions = [time_condition,price_condition] )
    elif args.illiquid and args.closetype=='mkt_eod' and position<0:
        return Order(action="BUY",
                     orderType="MKT",
                     algoStrategy='Adaptive', 
                     algoParams = [TagValue('adaptivePriority', 'Patient')],
                     totalQuantity = abs(position), 
                     tif = "DAY",
                     conditions = [time_condition] )
    elif args.illiquid and args.closetype=='mkt_eod' and position>0:
        return Order(action="SELL",
                     orderType="MKT",
                     algoStrategy='Adaptive', 
                     algoParams = [TagValue('adaptivePriority', 'Patient')],
                     totalQuantity = abs(position), 
                     tif = "DAY",
                     conditions = [time_condition] )
    elif not args.illiquid and args.closetype=='last_high_eod' and position>0:
        return Order(action="SELL",
                     orderType="LOC",
                     totalQuantity = abs(position), 
                     tif = None,
                     lmtPrice=lmt_price)
    elif not args.illiquid and args.closetype=='mkt_eod' and position<0:
        return Order(action="BUY",
                     orderType="MOC",
                     totalQuantity = abs(position), 
                     tif = None)
    elif not args.illiquid and args.closetype=='mkt_eod' and position>0:
        return Order(action="SELL",
                     orderType="MOC",
                     totalQuantity = abs(position), 
                     tif = None)
     
for sym in stock_tickers:
    if sym in position_tickers and not sym in open_tickers:
        position = openPositions[position_tickers[sym]]
        contr = Stock(sym, exchange='SMART', currency='USD')
        ib.qualifyContracts(contr)
        if args.closetype=='last_high_eod':
            if sym not in current_moves:
                print("Stock "+sym+" does not have current data. CLOSE MANUALLY")
                continue 
            print("Closing stock "+sym+" at previous high")
            order=order_conditions(args, position=position.position, lmtPrice = round(float(current_moves[sym]["high"]),2), contr=contr)
        else:
            order=order_conditions(args, position=position.position, contr=contr)
        ib.placeOrder(contr, order)
        print("ordering close for "+sym)

ib.disconnect()

