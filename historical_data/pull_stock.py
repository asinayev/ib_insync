from connection import initiate
from historical_data import pull_stock
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--real', dest='real', action = 'store_true') 

args = parser.parse_args()
args.real=True
ib = initiate.initiate_ib(args, 134)

def pull_contract_data(contract, ib):
    dt = '20220101 00:00:00'
    barsList = []
    print('starting loop')
    retries=0
    while True:
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=dt,
            durationStr='10 Y',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1)
        if not bars or bars[0].date==dt:
            retries+=1
            if retries>=3:
                break
        else:
            barsList+=bars
            print(bars[-1].date)
            dt = bars[0].date
            print(dt)
    barsDF=util.df(barsList)
    barsDF['symbol']=contract.symbol
    return(barsDF)

symbols = ['VTV','AGG','USO','GLD','FXI','VGT','LQD','VBR','BBH','DIA','DVY','EFA','EWA','FEU','EWJ','EWZ','XLY','XLU']
contracts = [Stock(s, exchange='SMART', currency='USD') for s in symbols]
out=pd.concat([pull_contract_data(contract, ib) for contract in contracts])

out.to_csv('/tmp/stonks.csv')
