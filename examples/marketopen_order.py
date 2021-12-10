from ib_insync import *

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Buy at open and sell at close')

parser.add_argument('--ticker', type=str, required=True,
                    help='stock to be traded')

parser.add_argument('--amount', type=int, required=True,
                    help='shares to trade')
parser.add_argument('--real', dest='real', action = 'store_true') 
parser.set_defaults(feature=False)
args = parser.parse_args()

args = parser.parse_args()

ib=IB()
if args.real: 
    port=4001
else:
    port=4002
ib.connect('127.0.0.1', port, clientId=13)

contract = Stock(args.ticker, exchange='SMART', currency='USD')
ib.qualifyContracts(contract)

buy_order=Order(action = 'BUY', orderType = 'MKT', totalQuantity = args.amount, tif = 'OPG')
buy_trade = ib.placeOrder(contract, buy_order)

sell_order=Order(action = 'SELL', orderType = 'MOC', totalQuantity = args.amount )
sell_trade = ib.placeOrder(contract, sell_order)

ib.sleep(1)
print(buy_trade.log)
print(sell_trade.log)
ib.disconnect()

