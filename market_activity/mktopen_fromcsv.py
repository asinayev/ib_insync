from ib_insync import *
from connection import initiate

import argparse
import csv

cash_per_stock = 10000

# Instantiate the parser
parser = argparse.ArgumentParser(description='market buy listed quantities of stocks at open and then sell at market close')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 13)

stockdict = csv.DictReader(open(args.file, "r"))

for row in stockdict:
    row['contract']=Stock(row['ticker'], exchange='SMART', currency='USD')
    ib.qualifyContracts(row['contract'])
    buy_order=Order(action = 'BUY', orderType = 'MKT', totalQuantity = row['quantity'] , tif = 'OPG' )
    buy_trade = ib.placeOrder(row['contract'], buy_order)
    sell_order=Order(action = 'SELL', orderType = 'MOC', totalQuantity = row['quantity'] )
    sell_trade = ib.placeOrder(row['contract'], sell_order)

ib.disconnect()

