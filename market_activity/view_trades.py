from ib_insync import IB, Trade
from connection import initiate
from datetime import date
from pandas import read_csv
from typing import List, Dict, Tuple

import transaction_logging
import argparse

def get_trade_info(trade: Trade) -> List[str]:
    today = date.today().strftime("%m/%d/%Y")
    local_symbol = trade.contract.localSymbol
    action = trade.order.action
    price = str(trade.fills[0].execution.price)
    shares = str(sum([fill.execution.shares for fill in trade.fills]))
    status = str(trade.orderStatus.status)
    num_fills = str(len(trade.fills))
    time = str(trade.fills[0].execution.time)
    return [today, local_symbol, action, price, '', shares, status, num_fills, time]

def log_json(ib: IB, args):
    for t in ib.trades():
        transaction_logging.log_trade(t,'',args.out_file)

def get_opens_and_closes(ib: IB, args) -> Tuple[List[List[str]], Dict[str, List[str]]]:
    opens = []
    closes = {}
    for t in ib.trades():
        if len(t.fills) > 0 and all([f.commissionReport.realizedPNL == 0 for f in t.fills]):
            opens.append(get_trade_info(t))
        if len(t.fills) > 0 and any([f.commissionReport.realizedPNL != 0 for f in t.fills]):
            trade_info = get_trade_info(t)
            closes[t.contract.localSymbol] = trade_info
    return opens, closes

def pop_off_trade(order_stocks, trade):
    for order_type, stocks in order_stocks.items():
        if trade[1] in stocks:
            order_stocks[order_type] = [s for s in stocks if s != trade[1]]
            return order_type
    return ''

def get_formatted_trade(t, closes, order_stocks):
    close_price = closes.get(t[1], ['','','',''])[3]
    t[2], t[3] = (str(t[3]), str(close_price)) if t[2] == 'BUY' else (str(close_price), str(t[3]))
    t[4] = pop_off_trade(order_stocks, t)
    t.append('more closed than opened' if t[1] in closes and t[5] < closes[t[1]][5] else '')
    return ','.join(t)


def print_trades(opens, closes, order_stocks, out_file=False):
    if out_file:
        out_file=open(out_file, 'w')
    for t in opens:
        print(get_formatted_trade(t, closes, order_stocks), file=out_file)

    print("#############################", file=out_file)
    for sym in closes:
        print(sym, ',', closes[sym], ', CLOSE TRADE', file=out_file)
    if out_file:
        out_file.close()

# Instantiate the parser
parser = argparse.ArgumentParser(description='Print trades in a very specific comma-separated format')


parser.add_argument('--real', dest='real', action = 'store_true', help='Use real account instead of paper trading') 
parser.add_argument('-c','--certain', action='append', help='Trades in order of certaintiy of execution executed', required=False)
parser.add_argument('--out_file', type=str, required=False) 
parser.add_argument('--file_type', type=str, required=False) 
parser.set_defaults(feature=False)
args = parser.parse_args()

ib = initiate.initiate_ib(args, 14)
if args.file_type=='json':
    log_json(ib,args)
    ib.disconnect()
else:
    opens, closes = get_opens_and_closes(ib,args)
    order_csvs = {o:read_csv('/tmp/stonksanalysis/'+o+'.csv') for o in args.certain}
    order_stocks = {order:csv.symbol.tolist() for order,csv in order_csvs.items()}
    print_trades(opens, closes, order_stocks, args.out_file)
    ib.disconnect()


