from connection import initiate
from ib_async import *
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--real', dest='real', action = 'store_true') 

args = parser.parse_args()
args.real=True
ib = initiate.initiate_ib(args, 134)

def pull_contract_data(contract, ib):
    dt = '20250522 00:00:00'
    barsList = []
    print('starting loop',contract)
    retries=0
    while True:
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=dt,
            durationStr='1 Y',
            barSizeSetting='1 day',
            whatToShow='MIDPOINT',
            useRTH=False,
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
    try:
        barsDF['symbol']=contract.pair()
    except:
        return(None)
    return(barsDF)

symbols = ['AUDZAR',
'AUDCNH',
'AUDSGD',
'AUDNZD',
'AUDCAD',
'AUDJPY',
'AUDHKD',
'AUDCHF',
'CADCHF',
'CADCNH',
'CADJPY',
'CADHKD',
'CHFUSD',
'CHFTRY',
'CHFPLN',
'CHFHUF',
'CHFCZK',
'CHFZAR',
'CHFCNH',
'CHFNOK',
'CHFDKK',
'CHFSEK',
'CHFJPY',
'CNHJPY',
'CNHHKD',
'DKKSEK',
'DKKJPY',
'DKKNOK',
'EURUSD',
'EUROMR',
'EURKWD',
'EURBHD',
'EURQAR',
'EURAED',
'EURSAR',
'EURZAR',
'EURCNH',
'EURRUB',
'EURPLN',
'EURCZK',
'EURHUF',
'EURNZD',
'EURILS',
'EURTRY',
'EURNOK',
'EURDKK',
'EURSGD',
'EURSEK',
'EURMXN',
'EURCAD',
'EURAUD',
'EURJPY',
'EURHKD',
'EURCHF',
'EURGBP',
'GBPUSD',
'GBPSGD',
'GBPCZK',
'GBPHUF',
'GBPPLN',
'GBPZAR',
'GBPCNH',
'GBPDKK',
'GBPNZD',
'GBPTRY',
'GBPNOK',
'GBPMXN',
'GBPSEK',
'GBPCAD',
'GBPAUD',
'GBPJPY',
'GBPHKD',
'GBPCHF',
'HKDJPY',
'KRWUSD',
'KRWJPY',
'KRWHKD',
'KRWGBP',
'KRWEUR',
'KRWCHF',
'KRWCAD',
'KRWAUD',
'MXNJPY',
'NOKSEK',
'NOKJPY',
'NZDUSD',
'NZDCHF',
'NZDCAD',
'NZDJPY',
'SEKJPY',
'SGDJPY',
'SGDHKD',
'SGDCNH',
'USDCHF',
'USDBHD',
'USDOMR',
'USDKWD',
'USDQAR',
'USDSAR',
'USDAED',
'USDHKD',
'USDJPY',
'USDCAD',
'USDRUB',
'USDDKK',
'USDPLN',
'USDHUF',
'USDCZK',
'USDMXN',
'USDKRW',
'USDSEK',
'USDSGD',
'USDNOK',
'USDRON',
'USDTRY',
'USDBGN',
'USDILS',
'USDZAR',
'USDCNH',
'ZARJPY',]
contracts = [Forex(s, exchange='IDEALPRO') for s in symbols]
out=pd.concat([pull_contract_data(contract, ib) for contract in contracts])

out.to_csv('/tmp/stonks.csv')
