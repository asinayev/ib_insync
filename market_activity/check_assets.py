from ib_insync import *
from connection import initiate
import argparse
import csv

def check_asset_file(args):
    ib = initiate.initiate_ib(args, cid=133)

    stock_dict = csv.DictReader(open(args.file, "r"))
    close_types, liquidities, repeating_symbol_issues = extract_close_types_and_liquidities(stock_dict)
    open_positions = ib.positions()
    position_tickers = {p.contract.symbol: p.position for p in open_positions}
    issues = find_issues(close_types, position_tickers)
    issues+=repeating_symbol_issues
    if issues:
        print(*issues, sep="\n")
        current_status_list = list(csv.DictReader(open(args.current_status_file, "r")))
        print_correct_asset_file(close_types, position_tickers, liquidities, current_status_list)
    ib.disconnect()

def extract_close_types_and_liquidities(stock_dict):
    close_types = {}
    liquidities = {}
    repeating_symbol_issues=[]
    for row in stock_dict:
        symbol = row['symbol']
        if symbol in close_types:
            repeating_symbol_issues.append(f"Symbol {symbol} is repeated in the asset file")
        close_types[symbol] = row['close_type']
        liquidities[symbol] = row['liquid']
    return close_types, liquidities, repeating_symbol_issues

def find_issues(close_types, position_tickers):
    issues = []
    for ticker in close_types:
        if ticker not in position_tickers:
            issues.append(f"In asset file but not held: {ticker}")
    for ticker in position_tickers:
        if ticker not in close_types:
            issues.append(f"Held but absent from asset file: {ticker}")
    return issues

def print_correct_asset_file(close_types, position_tickers, liquidities, current_status_list):
    print("Correct asset file:\n")
    # starts as the intersection of stocks in current assets file and existing positions
    correct_asset_file = {sym: close_types[sym] for sym in close_types if sym in position_tickers}
    for ticker in position_tickers:
        if ticker not in close_types:
            # when current position is missing, we add it with the appropriate close strategy and get the liquidity
            correct_asset_file[ticker] = 'last_high_eod' if position_tickers[ticker] > 0 else 'low_close_moo'
            liquidities[ticker] = find_liquidity(ticker, current_status_list)
    # Now we have liquidities for all the tickers in the existing files and the missing ones
    print(*[f"{t},{correct_asset_file[t]},{liquidities[t]}" for t in correct_asset_file], sep="\n")

def find_liquidity(ticker, current_status_list):
    for row in current_status_list:
        if row['symbol'] == ticker and int(row['volume']) > 150000:
            return '1'
    return 'UNKNOWN'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check for issues with asset file')
    parser.add_argument('--file', type=str, required=True, help='Path to asset file')
    parser.add_argument('--real', dest='real', action='store_true', help='Use real account')
    parser.add_argument('--current_status_file', type=str, required=True, help='Path to current status file')

    args = parser.parse_args()
    check_asset_file(args)
