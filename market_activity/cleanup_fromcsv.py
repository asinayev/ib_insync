from ib_async import *
from connection import initiate
from datetime import datetime, timedelta
import transaction_logging
import functools
import argparse
import csv
import time
import re

# Instantiate the parser
parser = argparse.ArgumentParser(description='order closes for opened positions')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--closetype', type=str, required=True, choices=['last_high_eod','mkt_eod','low_close_moo'])
parser.add_argument('--illiquid', dest='illiquid', action='store_true')
parser.add_argument('--currentstatusfile', type=str, required=False) 
parser.set_defaults(feature=False)
args = parser.parse_args()

# Import data
stocks = csv.DictReader(open(args.file, "r"))
stock_tickers = [row['symbol'] for row in stocks \
                     if 'close_type' not in row or \
                         (row['close_type']==args.closetype and bool(int(row['liquid'])) is not args.illiquid)]

current_moves = csv.DictReader(open(args.currentstatusfile, "r"))
current_moves = {row['symbol']:row for row in current_moves}
addtnl_moves = {}
for sym in current_moves:
    if not sym.isalnum():
        addtnl_moves[re.sub('[^0-9a-zA-Z]+', ' ', sym)]=current_moves[sym]
current_moves.update(addtnl_moves)

# Open connection
ib = initiate.initiate_ib(args, 14)
openTrades = ib.openTrades()

# Order positions from this strategy to be closed 
openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}
open_tickers = [t.contract.symbol for t in ib.openTrades()]

def order_conditions(args, position, lmt_price=None, contr=None):
    time_condition = TimeCondition(isMore=True, time=datetime.today().strftime('%Y%m%d')+' 15:50:00 US/Eastern', conjunction='a')
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
        price_condition = PriceCondition(1,conjunction='a', isMore=True,
                    price=lmt_price, 
                    exch='SMART', conId=contr.conId)
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
    elif not args.illiquid and args.closetype=='low_close_moo' and position<0:
        return Order(action="BUY",
                     orderType="MKT",
                     totalQuantity = abs(position), 
                     tif = "OPG")
    elif args.illiquid and args.closetype=='low_close_moo' and position<0:
        return Order(action="BUY",
                     orderType="MKT",
                     algoStrategy='Adaptive', 
                     algoParams = [TagValue('adaptivePriority', 'Patient')],
                     totalQuantity = abs(position), 
                     tif = "DAY", )
     
for sym in stock_tickers:
    print('starting close '+sym)
    if sym in position_tickers and not sym in open_tickers:
        position = openPositions[position_tickers[sym]]
        contr = Stock(sym, exchange='SMART', currency='USD')
        ib.qualifyContracts(contr)
        if args.closetype=='last_high_eod':
            if sym not in current_moves:
                print("Stock "+sym+" does not have current data. CLOSE MANUALLY")
                continue 
            print("Closing stock "+sym+" at previous high")
            order=order_conditions(args, position=position.position, lmt_price = round(float(current_moves[sym]["high"]),2), contr=contr)
        else:
            order=order_conditions(args, position=position.position, contr=contr)
        if args.closetype=='low_close_moo':
            if float(current_moves[sym]["close"])<float(current_moves[sym]["low"])+.2*(float(current_moves[sym]["high"])-float(current_moves[sym]["low"])):
              order=order_conditions(args, position=position.position, contr=contr)
            else:
              continue
        tr = ib.placeOrder(contr, order)
        transaction_logging.log_trade(tr,args.file,'/tmp/stonksanalysis/order_logs.json',{'close':1})
        print(tr)
        time.sleep(3)
        print("ordering close for "+sym)

while ib.isConnected():
    ib.disconnect()
    ib.waitOnUpdate(timeout=.3)

