from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta
import functools
import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='cancel orders for unopened positions and order closes for opened positions')

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

for sym in stock_tickers:
    if sym in position_tickers and not sym in open_tickers:
        position = openPositions[position_tickers[sym]]
        contr = Stock(sym, exchange='SMART', currency='USD')
        ib.qualifyContracts(contr)
        if args.illiquid or args.closetype=='last_high_eod':
            actual_order_type='MIDPRICE'
            tif='DAY'
        else:
            actual_order_type='MOC'
            tif=None
        if position.position>0:
            ord_action="SELL"
            if args.closetype=='last_high_eod' and not args.illiquid:
                actual_order_type='LOC'
                tif=None
        else:
            ord_action="BUY"
        part_order = functools.partial(Order,
                        action=ord_action,
                        orderType=actual_order_type,
                        totalQuantity = abs(position.position), 
                        tif = tif,
                        conditions = [])
        if actual_order_type=='MIDPRICE':
            if ord_action=="BUY":
                lmt_price=round(float(position.avgCost*3),2)
            else:
                lmt_price=round(float(position.avgCost/3),2)
            part_order=functools.partial(part_order, lmtPrice=lmt_price, conditions=[TimeCondition(isMore=True, time=datetime.today().strftime('%Y%m%d')+' 15:50:00 EST', conjunction='a')])
        if args.closetype=='last_high_eod':
            if sym not in current_moves:
                print("Stock "+sym+" does not have current data. CLOSE MANUALLY")
                continue 
            print("Closing stock "+sym+" at previous high")
            if ord_action=='SELL':
                order =part_order(lmtPrice = round(float(current_moves[sym]["high"]),2) )
            else:
                order.conditions.append(
                    PriceCondition(1,conjunction='a', isMore=True,
                        price=round(float(current_moves[sym]["high"]),2), 
                        exch='SMART', conId=contr.conId))
        else:
            order = part_order() 
        ib.placeOrder(contr, order)
        print("ordering close for "+sym)

ib.disconnect()

