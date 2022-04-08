from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import argparse
import functools
import csv
import execution_flow

# Instantiate the parser
parser = argparse.ArgumentParser(description='limit buy stocks at listed limit prices on open and then sell at market close')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--cash', type=int, required=True)
parser.add_argument('--minprice', type=float, required=True)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 133)

stockdict = csv.DictReader(open(args.file, "r"))

for row in stockdict:
    row['contract']=Stock(row['symbol'], exchange='SMART', currency='USD')
    ib.qualifyContracts(row['contract'])
    quantity = max(1, int(args.cash/float(row['close'])))
    limit_order = functools.partial(Order, orderType = 'LMT', totalQuantity = quantity, tif = 'OPG')
    if float(row['buy'])>args.minprice:
        part_order = functools.partial(limit_order, action = 'BUY',  lmtPrice=row['buy'])
        #if not execution_flow.fee_too_high(
        #        order_preset=part_order, contract=row['contract'], 
        #        ib_conn=ib, fee_limit=max(2,args.cash/300)):
        buy_trade = ib.placeOrder(row['contract'], part_order())
    if float(row['sell'])>args.minprice:
        part_order = functools.partial(limit_order, action = 'SELL',  lmtPrice=row['sell'])
        #if not execution_flow.fee_too_high(
        #        order_preset=part_order, contract=row['contract'], 
        #        ib_conn=ib, fee_limit=max(2,args.cash/300)):
        sell_trade = ib.placeOrder(row['contract'], part_order())

ib.disconnect()

