from ib_insync import *

import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Buy at open and sell at close')

parser.add_argument('ticker', type=str,
                    help='stock to be traded')

parser.add_argument('amount', type=int,
                    help='shares to trade')
args = parser.parse_args()

ib=IB()
ib.connect('127.0.0.1', 4002, clientId=13)

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

