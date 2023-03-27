from ib_insync import *
from connection import initiate

import argparse
import csv
from collections import Counter

# Instantiate the parser
parser = argparse.ArgumentParser(description='check for issues with asset file')

parser.add_argument('--file', type=str, required=True)
parser.add_argument('--real', dest='real', action = 'store_true') 

args = parser.parse_args()

ib = initiate.initiate_ib(args, 133) 

stockdict = csv.DictReader(open(args.file, "r"))
close_types={}
liquidities={}
issues = []
for row in stockdict:
    if row['symbol'] in close_types:
        issues.append("Repeated in asset file: "+ row['symbol'])
    else:
        close_types[row['symbol']]=row['close_type']
        liquidities[row['symbol']]=row['liquid']

openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}

issues +=["In asset file but is not held: "+ticker for ticker in close_types if ticker not in position_tickers]
issues +=["Held but absent from asset file: "+ticker for ticker in position_tickers if ticker not in close_types]

if issues:
    print(*issues, sep = "\n")
    print("Correct asset file:\n")
    correct_asset_file={sym:close_types[sym] for sym in close_types if sym in position_tickers}
    for ticker in position_tickers: 
        if ticker not in close_types:
            if position_tickers[ticker]<0:
                correct_asset_file[ticker]='low_close_moo'
            else:
                correct_asset_file[ticker]='last_high_eod'
            liquidities[ticker]='UNKNOWN' #TODO: fill this with liquidity based on volume
    print(*[t+','+correct_asset_file[t]+','+liquidities[t] for t in correct_asset_file],sep="\n")

ib.disconnect()
