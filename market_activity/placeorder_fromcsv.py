from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import execution_flow
import functools 
import argparse
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

parser.add_argument('--real', dest='real', action = 'store_true') 
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

def place_order(row, ib):
    ibkr_ordertype = row['order_type']
    if row['time_in_force'] == 'close' and row['order_type'] in ['MKT', 'LMT']:
        ibkr_ordertype = {'MKT': 'MOC', 'LMT': 'LOC'}[row['order_type']]
    row['contract']=Stock(row['symbol'], exchange='SMART', currency='USD')
    if ('strike_price' not in row or row['strike_price']=='') and 'close' not in row:
        print("Stock has no strike price or close price. Skipping: "+row['symbol'])
        return
    if 'strike_price' not in row or row['strike_price']=='' :
        row['strike_price']=float(row['close'])
    else:
        row['strike_price']=float(row['strike_price'])
    row['quantity']=round(args.cash/row['strike_price'])
    ib.qualifyContracts(row['contract'])
    part_order = functools.partial(Order,
                        action = row['action'],
                        orderType = ibkr_ordertype, 
                        totalQuantity = row['quantity'], 
                        tif = row['time_in_force'], 
                        lmtPrice=round(float(row['strike_price']),2))
    #if not execution_flow.fee_too_high(order_preset=part_order, contract=row['contract'], 
    #        ib_conn=ib, fee_limit=max(2,args.cash/1000)):
    if row['strike_price']>args.minprice:
        print(f"Sending {ibkr_ordertype} order at {row['strike_price']}: {row['symbol']}")
        this_trade = ib.placeOrder(row['contract'], part_order())
    else:
        print(f"Skipping because price {row['strike_price']} is too low: {row['symbol']}")

order_if_needed(args)
