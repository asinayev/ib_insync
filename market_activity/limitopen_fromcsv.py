from ib_insync import *
from connection import initiate
from datetime import datetime, timedelta

import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='limit buy stocks at listed limit prices on open and then sell at market close')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--cash', type=int, required=True)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 133)

stockdict = csv.DictReader(open(args.file, "r"))
for row in stockdict:
    row['contract']=Stock(row['symbol'], exchange='ISLAND', currency='USD')
    ib.qualifyContracts(row['contract'])
    quantity = max(1, int(args.cash/float(row['close'])))
    if float(row['buy'])>0:
        buy_order =Order(action = 'BUY',  orderType = 'LMT', totalQuantity = quantity, tif = 'OPG', lmtPrice=row['buy'])
        buy_trade = ib.placeOrder(row['contract'], buy_order)
    if float(row['sell'])>0:
        sell_order=Order(action = 'SELL', orderType = 'LMT', totalQuantity = quantity, tif = 'OPG', lmtPrice=row['sell'] )
        sell_trade = ib.placeOrder(row['contract'], sell_order)

ib.disconnect()

