from ib_async import *
from connection import initiate
import argparse
import csv

def check_asset_file(args):
    ib = initiate.initiate_ib(args, cid=133)
    asset_dict = csv.DictReader(open(args.file, "r"))
    close_types, liquidities = extract_close_types_and_liquidities(asset_dict)
    open_positions = ib.positions()
    position_tickers = {p.contract.symbol: p.position for p in open_positions}
    current_status_list = list(csv.DictReader(open(args.current_status_file, "r")))
    print_correct_asset_file(close_types, position_tickers, liquidities, current_status_list, args.out_file)
    ib.disconnect()

def extract_close_types_and_liquidities(asset_dict):
    close_types = {}
    liquidities = {}
    for row in asset_dict:
        symbol = row['symbol']
        close_types[symbol] = row['close_type']
        liquidities[symbol] = row['liquid']
    return close_types, liquidities

def print_correct_asset_file(close_types, position_tickers, liquidities, current_status_list, out_file):
    # starts as the intersection of stocks in assets file and existing positions
    correct_asset_file = {sym: close_types[sym] for sym in close_types if sym in position_tickers}
    for ticker in position_tickers:
        if ticker not in close_types:
            # when a position is not an asset, we add it with the appropriate close strategy and get the liquidity
            correct_asset_file[ticker] = 'last_high_eod' if position_tickers[ticker] > 0 else 'low_close_moo'
            liquidities[ticker] = find_liquidity(ticker, current_status_list)
            if liquidities[ticker]=='UNKNOWN' and out_file:
                liquidities[ticker]='0'
    mtm_positions = {t:mtm_position(t,current_status_list,position_tickers[t]) for t in correct_asset_file}
    # Now we have liquidities for all the tickers in the existing files and the missing ones
    if out_file:
        out_file=open(out_file, 'w')
        print('symbol,close_type,liquid,position,mtm_dollars\n', file=out_file)
    print(*[f"{t},{correct_asset_file[t]},{liquidities[t]},{position_tickers[t]},{mtm_positions[t]}" for t in correct_asset_file], sep="\n", file=out_file)
    if out_file:
        out_file.close()

def find_liquidity(ticker, current_status_list):
    for row in current_status_list:
        if row['symbol'] == ticker and int(row['volume']) > 150000:
            return '1'
    return 'UNKNOWN'

def mtm_position(ticker, current_status_list, position):
    for row in current_status_list:
        if row['symbol'] == ticker and 'AdjClose' in row:
            return round(position*float(row['AdjClose']))
    return 'UNKNOWN'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check for issues with asset file')
    parser.add_argument('--file', type=str, required=True, help='Path to asset file')
    parser.add_argument('--real', dest='real', action='store_true', help='Use real account')
    parser.add_argument('--current_status_file', type=str, required=True, help='Path to current status file')
    parser.add_argument('--out_file', type=str, required=False) 

    args = parser.parse_args()
    check_asset_file(args)
