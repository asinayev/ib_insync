import asyncio
import pandas as pd
from ib_async import *
import time

# Create a semaphore that will allow 5 tasks to run concurrently
SEMAPHORE_LIMIT = 5
semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

async def fetch_one_stock(ib, contract):
    """
    Safely fetches data for one stock by acquiring the semaphore first.
    """
    # async with will wait here until a "shopping cart" is free
    async with semaphore:
        ticker = ib.reqMktData(contract, '', snapshot=True)
        await asyncio.sleep(0.2)
        bars = await ib.reqHistoricalDataAsync(
            contract, endDateTime='', durationStr='6 D',
            barSizeSetting='1 day', whatToShow='TRADES', useRTH=True
        )
        
        # More robust check to ensure all required data points exist
        if not all([ticker.close, ticker.last, bars]):
            print(f"--> Skipping {contract.symbol}, incomplete data.")
            return None
        
        print(f"🏁 {contract.symbol}: Finished")
        return {
            'Contract': contract,
            'Symbol': contract.symbol,
            'Last Price': ticker.last, 
            'Close': ticker.close,
            'Open': ticker.open,
            'Volume': ticker.volume,
            'Close 5 Days Ago': bars[0].close,
            'meets conditions': ticker.last<ticker.open*.825 and ticker.volume>500000 and ticker.last>7 and ticker.last<bars[0].close
        }

async def get_drops():
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    ib = IB()
    try:
        # NOTE: Ensure your port is correct (e.g., 7497 for TWS, 4001 for Gateway)
        await ib.connectAsync('127.0.0.1', 4001, clientId=1)
        print("✅ Successfully connected to IB.")
        
        sub = ScannerSubscription(instrument='STK', locationCode='STK.US.MAJOR', scanCode='TOP_OPEN_PERC_LOSE')
        scan_data = await ib.reqScannerDataAsync(sub)
        contracts = [item.contractDetails.contract for item in scan_data]
        
        if not contracts:
            print("Scanner returned no contracts.")
            return
            
        print(f"Scanner found {len(contracts)} results. Fetching data with a concurrency limit of {SEMAPHORE_LIMIT}...")
        ib.reqMarketDataType(1) 
        
        tasks = [fetch_one_stock(ib, contract) for contract in contracts]
        
        results = await asyncio.gather(*tasks)
        valid_results = [res for res in results if res is not None and res['meets conditions']]
        
        print("\n--- All results ---")
        print(pd.DataFrame(results)[['Symbol','Last Price','Open','Volume','Close 5 Days Ago','meets conditions']])
        print("Number of valid results: ",len(valid_results))
        if valid_results:
            top_result=valid_results[0]
            print("\n--- Top result ---")
            print(top_result)
            df = pd.DataFrame([{'symbol':top_result['Symbol'],'strike_price':top_result['Last Price'],'action':"BUY",'order_type':"MKT",'time_in_force':"close"}])
            df.to_csv("/tmp/stonksanalysis/night_rebound.csv")
    finally:
        if ib.isConnected():
            print("\nDisconnecting from IB.")
            ib.disconnect()

if __name__ == "__main__":
    asyncio.run(get_drops())

