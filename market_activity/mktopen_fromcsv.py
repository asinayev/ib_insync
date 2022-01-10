from ib_insync import *
from connection import initiate

import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='market buy (or sell) listed quantities of stocks at open and then close the position at market close')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--cash', type=float, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.add_argument('--autoclose', dest='autoclose', action = 'store_true') 
parser.add_argument('--openaction', type=str, required=True, choices=['BUY','SELL']) 
parser.set_defaults(short=False)
args = parser.parse_args()

closeaction = {'BUY':'SELL','SELL':'BUY'}[args.openaction]

ib = initiate.initiate_ib(args, 15)

stockdict = csv.DictReader(open(args.file, "r"))

for row in stockdict:
    row['contract']=Stock(row['symbol'], exchange='SMART', currency='USD')
    row['quantity']=round(args.cash/float(row['price']))
    ib.qualifyContracts(row['contract'])
    if 'slow' in row and int(row['slow'])>0:
        open_order=Order(action = 'BUY', orderType = 'MKT', totalQuantity = row['quantity'] , tif = 'DAY', algoStrategy='Adaptive', algoParams = [TagValue('adaptivePriority', 'Normal')])
    else:
        open_order=Order(action = args.openaction, orderType = 'MKT', totalQuantity = row['quantity'] , tif = 'OPG' )
    open_trade = ib.placeOrder(row['contract'], open_order)
    if args.autoclose:
        close_order=Order(action = closeaction, orderType = 'MOC', totalQuantity = row['quantity'] )
        close_trade = ib.placeOrder(row['contract'], close_order)

ib.disconnect()

