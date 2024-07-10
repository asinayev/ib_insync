from ib_async import IB, Trade
from connection import initiate
from datetime import date
from typing import List, Dict, Tuple

import argparse
import ast
import pandas as pd
import transaction_logging

def get_trade_info(trade: Trade) -> List[str]:
    today = date.today().strftime("%m/%d/%Y")
    local_symbol = trade.contract.localSymbol
    action = trade.order.action
    price = str(sum([f.execution.price * f.execution.shares for f in trade.fills])/sum([fill.execution.shares for fill in trade.fills]))
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
    matched = order_stocks[(order_stocks.symbol==trade[1]) & ( abs(order_stocks.quantity-float(trade[5]) )<1 ) ]
    if not matched.empty:
        first_matched = matched.index[0]
        matched_strat = order_stocks.loc[first_matched,'trade_reason']
        matched_strat = matched_strat.split('/')[-1].split('.')[-2]
        order_stocks.drop(first_matched, inplace=True)
        return matched_strat
    else:
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
    with open('/tmp/stonksanalysis/order_logs.json', 'r') as f:
        order_stocks = pd.DataFrame([ast.literal_eval(line) for line in f])
    print_trades(opens, closes, order_stocks, args.out_file)
    ib.disconnect()


