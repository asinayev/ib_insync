from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import transaction_logging
import functools 
import argparse
import math
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='limit buy stocks at listed limit prices on open and then sell at market close')

parser.add_argument('--file', type=str, required=True)
#File needs columns:
# symbol
# action
# ttrike_price
# order_type
# time_in_force

parser.add_argument('--real', dest='real', action='store_true') 
parser.add_argument('--cash', type=int, required=True)
parser.add_argument('--minprice', type=float, required=True)
parser.add_argument('--minspymove', type=float, required=False)
parser.add_argument('--maxspymove', type=float, required=False)
parser.add_argument('--spyfile', type=str, required=False)
#File needs columns:
# symbol

args = parser.parse_args()

def order_if_needed(args):
    SPY_issue = check_spy(args)
    if SPY_issue:
        print(SPY_issue)
    else:
        print(f"Executing {args.file}")
        ib = initiate.initiate_ib(args, 14)
        stockdict = csv.DictReader(open(args.file, "r"))
        for row in stockdict:
            place_order(row, ib)
        while ib.isConnected():
            ib.disconnect()
            ib.waitOnUpdate(timeout=.3)

def check_spy(args):
    SPY_issue=None
    if args.minspymove or args.maxspymove:
        spy = next(csv.DictReader(open(args.spyfile, "r")))
        todays_change_perc = float(spy['todaysChangePerc'])
        if args.minspymove and todays_change_perc < float(args.minspymove):
            SPY_issue = 'SPY moved too low for \n'+args.file
        if args.maxspymove and todays_change_perc > float(args.maxspymove):
            SPY_issue = 'SPY moved too high for \n'+args.file
    return SPY_issue

def get_ibkr_order_type(row):
    if row['time_in_force'] == 'close' and row['order_type'] in ['MKT', 'LMT']:
        return {'MKT': 'MOC', 'LMT': 'LOC'}[row['order_type']]
    else:
        return row['order_type']

def get_quantity(row,existing_position, to_spend, price):
    if row['action']=='BUY' and existing_position>0: 
        return round(to_spend/price), {}
    elif row['action']=='SELL' and existing_position<0: 
        return round(to_spend/price), {}
    elif round(existing_position)==0:
        return round(to_spend/price), {}
    else:
        return abs(existing_position), {'close':1}

def get_price(ib,contract,is_limit,strike_price,action):
    last_live=ib.reqMktData(contract, genericTickList='', snapshot=True, regulatorySnapshot=False,mktDataOptions=None)
    while math.isnan(last_live.last):
        ib.sleep(.1)
    mkt_price=last_live.last
    if is_limit:
        return mkt_price, float(strike_price)
    elif action=='BUY':
        return mkt_price, mkt_price*1.1
    elif action=='SELL':
        return mkt_price, mkt_price*.9

def get_position(ib,sym):
    openPositions = ib.positions()
    position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}
    ib.client.reqAllOpenOrders()
    _ = ib.reqOpenOrders()
    openTrades = ib.openTrades()
    if sym in position_tickers:
        final_position=openPositions[position_tickers[sym]].position
        for t in openTrades:
            if sym==t.contract.symbol:
                if t.order.action=='BUY':
                    final_position+=t.order.totalQuantity
                elif t.order.action=='SELL':
                    final_position-=t.order.totalQuantity
        return final_position
    else: return 0

def place_order(row, ib):
    ibkr_ordertype = get_ibkr_order_type(row)
    qualifieds=ib.qualifyContracts(Stock(row['symbol'], exchange='SMART', currency='USD'))
    if len(qualifieds)==0:
        print("Symbol not found. Skipping: "+row['symbol'])
        return
    if len(qualifieds)>1:
        print("More than one contract for symbol found. Skipping: "+row['symbol'])
        return
    if row['order_type']=='LMT':
        if 'strike_price' not in row or row['strike_price']=='':
            print("Stock has no strike price or close price. Skipping: "+row['symbol'])
            return
    row['contract']=qualifieds[0]
    row['strike_price'], lmt_price = get_price(ib,row['contract'],row['order_type']=='LMT',row['strike_price'],row['action'])
    current_position=get_position(ib,row['symbol'])
    row['quantity'], notes=get_quantity(row,current_position,args.cash,row['strike_price'])
    part_order = functools.partial(Order,
                        action = row['action'],
                        orderType = ibkr_ordertype, 
                        totalQuantity = row['quantity'], 
                        tif = row['time_in_force'], 
                        lmtPrice=round(lmt_price,2))
    if row['strike_price']>args.minprice and row['strike_price']*row['quantity']<args.cash*1.5:
        print(f"Sending {ibkr_ordertype} order at {row['strike_price']}: {row['symbol']}")
        this_trade = ib.placeOrder(row['contract'], part_order())
        transaction_logging.log_trade(this_trade,args.file,'/tmp/stonksanalysis/order_logs.json',notes)
    else:
        print(f"Skipping because price {row['strike_price']} is too low or trying to order too much: {row['symbol']}")

order_if_needed(args)
