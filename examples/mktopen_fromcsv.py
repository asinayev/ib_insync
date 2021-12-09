from ib_insync import *

import argparse
import csv

# Instantiate the parser
parser = argparse.ArgumentParser(description='Buy at open and sell at close')

parser.add_argument('--file', type=str, required=True)
args = parser.parse_args()

stockdict = csv.DictReader(open(args.file, "r"), fieldnames = ['ticker','price'])

ib=IB()
if args.real: 
    port=4002
else:
    port=4001
ib.connect('127.0.0.1', port, clientId=13)

contracts = {Stock(row.ticker, exchange='SMART', currency='USD')}
ib.qualifyContracts(contract)

buy_order=Order(action = 'BUY', orderType = 'MKT', totalQuantity = args.amount, tif = 'OPG')
buy_trade = ib.placeOrder(contract, buy_order)

sell_order=Order(action = 'SELL', orderType = 'MOC', totalQuantity = args.amount )
sell_trade = ib.placeOrder(contract, sell_order)

ib.sleep(1)
print(buy_trade.log)
print(sell_trade.log)
ib.disconnect()

