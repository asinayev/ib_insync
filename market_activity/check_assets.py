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
asset_tickers={}
issues = []
for row in stockdict:
    if row['symbol'] in asset_tickers:
        issues.append("Repeated in asset file: "+ row['symbol'])
    else:
        asset_tickers[row['symbol']]=row['asset_type']

openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}

issues +=["In asset file but is not held: "+ticker for ticker in asset_tickers if ticker not in position_tickers]
issues +=["Held but absent from asset file: "+ticker for ticker in position_tickers if ticker not in asset_tickers]

if issues:
    print(*issues, sep = "\n")
    print("Correct asset file:\n")
    correct_asset_file={sym:asset_tickers[sym] for sym in asset_tickers if sym in position_tickers}
    for ticker in position_tickers: 
        if ticker not in asset_tickers:
            correct_asset_file[ticker]='liquid'
    print(*[t+','+correct_asset_file[t] for t in correct_asset_file],sep="\n")

ib.disconnect()
