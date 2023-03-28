from ib_insync import *
from connection import initiate
import argparse
import csv

def check_asset_file(args):
    ib = initiate.initiate_ib(args, client_id=133)

    stock_dict = csv.DictReader(open(args.file, "r"))
    close_types, liquidities, repeating_symbol_issues = extract_close_types_and_liquidities(stock_dict)
    open_positions = ib.positions()
    position_tickers = {p.contract.symbol: p.position for p in open_positions}
    issues = find_issues(close_types, position_tickers)
    issues+=repeating_symbol_issues
    if issues:
        print(*issues, sep="\n")
        print_correct_asset_file(close_types, position_tickers, args)
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

def print_correct_asset_file(close_types, position_tickers, args):
    print("Correct asset file:\n")
    correct_asset_file = {sym: close_types[sym] for sym in close_types if sym in position_tickers}
    liquidities = {}
    for ticker in position_tickers:
        if ticker not in close_types:
            liquidities[ticker] = find_liquidity(ticker, args)
            correct_asset_file[ticker] = 'last_high_eod' if position_tickers[ticker] > 0 else 'low_close_moo'
    print(*[f"{t},{correct_asset_file[t]},{liquidities[t]}" for t in correct_asset_file], sep="\n")

def find_liquidity(ticker, args):
    current_status = csv.DictReader(open(args.current_status_file, "r"))
    for row in current_status:
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
