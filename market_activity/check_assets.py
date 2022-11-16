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
asset_tickers = [row['symbol'] for row in stockdict]

openPositions = ib.positions()
position_tickers = {p.contract.symbol:i for i,p in enumerate(openPositions)}

issues = ["Repeated "+str(count)+" times in asset file: "+ticker for ticker,count in Counter(asset_tickers).items() if count>1]
issues +=["In asset file but is not held: "+ticker for ticker in asset_tickers if ticker not in position_tickers]
issues +=["Held but absent from asset file: "+ticker for ticker in position_tickers if ticker not in asset_tickers]

print(*issues, sep = "\n")

ib.disconnect()
