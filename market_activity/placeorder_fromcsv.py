from ib_async import *
from connection import initiate
from datetime import datetime, timedelta

import transaction_logging
import functools 
import argparse
import random
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
parser.add_argument('--trixstatuslist', type=str, required=False)
#File needs columns:
# symbol

args = parser.parse_args()

def order_if_needed(args):
    SPY_issue = check_spy(args)
    allowlist_issue = check_status_list(args)
    if SPY_issue or allowlist_issue:
        print(SPY_issue + allowlist_issue)
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
    SPY_issue=''
    if args.minspymove or args.maxspymove:
        spy = next(csv.DictReader(open(args.spyfile, "r")))
        todays_change_perc = float(spy['todaysChangePerc'])
        if args.minspymove and todays_change_perc < float(args.minspymove):
            SPY_issue = 'SPY moved too low for \n'+args.file
        if args.maxspymove and todays_change_perc > float(args.maxspymove):
            SPY_issue = 'SPY moved too high for \n'+args.file
    return SPY_issue

def check_status_list(args):
    allowlist_issue=''
    if args.trixstatuslist:
        status_list = csv.DictReader(open(args.trixstatuslist, "r"))
        strat_name=args.file.split('/')[-1].split('.')[0]
        for row in status_list:
            if row['strategy']==strat_name:
                if not int(row['allow']):
                    allowlist_issue=strat_name + ' not allowed by status file'
    return allowlist_issue
        
def get_ibkr_order(row, lmt_price):
    if row['time_in_force'] == 'close' and row['order_type'] in ['MKT', 'LMT']:
        order_type_to_use = {'MKT': 'MOC', 'LMT': 'LOC'}[row['order_type']]
    else:
        order_type_to_use = row['order_type']
    if row['order_type'] == 'Adaptive':
        part_order = functools.partial(Order,
                            action = row['action'],
                            orderType = 'MKT',
                            algoStrategy='Adaptive', 
                            algoParams = [TagValue('adaptivePriority', 'Patient')],
                            totalQuantity = row['quantity'], 
                            tif = 'DAY', 
                            lmtPrice=round(lmt_price,2))
    else:
        part_order = functools.partial(Order,
                            action = row['action'],
                            orderType = order_type_to_use, 
                            totalQuantity = row['quantity'], 
                            tif = row['time_in_force'], 
                            lmtPrice=round(lmt_price,2))
    return part_order

def get_quantity(row,existing_position, to_spend, price):
    if row['action']=='BUY' and existing_position>0: 
        return round(to_spend/price), {}
    elif row['action']=='SELL' and existing_position<0: 
        return round(to_spend/price), {}
    elif round(existing_position)==0:
        return round(to_spend/price), {}
    else:
        return abs(existing_position), {'close':1}

def get_price(row, ib):
    if row['order_type']=='LMT':
        if 'strike_price' not in row or row['strike_price']=='':
            print("Limit order has no strike price or close price. Skipping: "+row['symbol'])
            return 0,0
    last_live=ib.reqMktData(row['contract'], genericTickList='', snapshot=True, regulatorySnapshot=False,mktDataOptions=None)
    i=0
    while math.isnan(last_live.last):
        ib.sleep(.1)
        i+=1
        if i>30:
            print("Market price not found. Using strike price for: "+row['contract'].symbol)
            mkt_price=float(row['strike_price'])
            break
    if i<=30:
        mkt_price=last_live.last
    if row['order_type']=='LMT':
        return mkt_price, float(row['strike_price'])
    elif row['action']=='BUY':
        return mkt_price, mkt_price*1.1
    elif row['action']=='SELL':
        return mkt_price, mkt_price*.9
    else:
        print("Did not match a known action.")
        return 0,0

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
        
def get_contract(row, ib):
    qualifieds=ib.qualifyContracts(Stock(row['symbol'], exchange='SMART', currency='USD'))
    if len(qualifieds)==0:
        print("Symbol not found. Skipping: "+row['symbol'])
        return
    elif len(qualifieds)>1:
        print("More than one contract for symbol found. Skipping: "+row['symbol'])
        return
    else:
        return qualifieds[0]

def place_order(row, ib):
    row['contract']=get_contract(row, ib)
    if not row['contract']: return
    row['strike_price'], lmt_price = get_price(row, ib)
    if not lmt_price: return
    current_position=get_position(ib,row['symbol'])
    row['quantity'], notes=get_quantity(row,current_position,args.cash,row['strike_price'])
    part_order = get_ibkr_order(row, lmt_price,)
    if row['strike_price']>args.minprice and row['strike_price']*row['quantity']<args.cash*1.5:
        print(f"Sending {row['order_type']} order at {row['strike_price']}: {row['symbol']}")
        this_trade = ib.placeOrder(row['contract'], part_order())
        if row['order_type']=='MKT': #log the initial trade as control and make an additional trade logged as experiment
            notes.update({'adapt_exp':0})
            transaction_logging.log_trade(this_trade,args.file,'/tmp/stonksanalysis/order_logs.json',notes)
            row['order_type']='Adaptive'
            row['time_in_force']='OPG'
            print(f"Sending {row['order_type']} order at {row['strike_price']}: {row['symbol']}")
            exp_trade = ib.placeOrder(row['contract'], part_order())
            notes.update({'adapt_exp':1})
            transaction_logging.log_trade(exp_trade,args.file,'/tmp/stonksanalysis/order_logs.json',notes)
        else: # just log the initial trade, not marking as control
            transaction_logging.log_trade(this_trade,args.file,'/tmp/stonksanalysis/order_logs.json',notes)
    else:
        print(f"Skipping because price {row['strike_price']} is too low or trying to order too much: {row['symbol']}")

order_if_needed(args)
