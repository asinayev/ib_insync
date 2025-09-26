from connection import initiate  # Assuming this is your custom connection module
from ib_async import *
import argparse
import pandas as pd
from datetime import datetime, date  # FIX: 'date' is now imported
from dateutil.relativedelta import relativedelta  # For parsing duration strings

# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Fetch historical contract data from Interactive Brokers."
)
parser.add_argument(
    "--real",
    dest="real",
    action="store_true",
    help="Connect to real trading account (default is simulated).",
)
parser.add_argument(
    "--duration",
    dest="history_duration",
    type=str,
    nargs="?",
    default=None,
    help='How far back to fetch data (e.g., "3 M", "1 Y", "5 D"). Default goes as far as possible.',
)

args = parser.parse_args()

# --- Initialize IB Connection ---
# Assuming initiate.initiate_ib handles args.real and returns an IB client instance
ib = initiate.initiate_ib(args, 134)  # Port 134 used as an example


def parse_duration_to_relativedelta(duration_str: str):
    """
    Parses a duration string like "1 M", "6 M", "1 Y" into a relativedelta object.
    Returns None if parsing fails.
    """
    if not duration_str:
        return None
    try:
        parts = duration_str.split()
        if len(parts) != 2:
            print(
                f"Error: Invalid duration string format '{duration_str}'. Expected 'VALUE UNIT' (e.g., '6 M')."
            )
            return None
        value = int(parts[0])
        unit = parts[1].upper()

        if unit == "S":
            return relativedelta(seconds=value)
        if unit == "D":
            return relativedelta(days=value)
        if unit == "W":
            return relativedelta(weeks=value)
        if unit == "M":
            return relativedelta(months=value)
        if unit == "Y":
            return relativedelta(years=value)

        print(
            f"Error: Unknown duration unit '{parts[1]}' in '{duration_str}'. Use S, D, W, M, or Y."
        )
        return None
    except ValueError:
        print(
            f"Error: Invalid value for duration '{parts[0]}' in '{duration_str}'. Must be an integer."
        )
        return None
    except Exception as e:
        print(f"Error parsing duration string '{duration_str}': {e}")
        return None


def _fetch_and_process_data(contract, ib_client, history_duration_arg, what_to_show):
    """
    Internal helper function to fetch historical data for a given contract and data type.
    """
    barsList = []
    now_datetime = datetime.now()
    current_initial_dt_str = now_datetime.strftime("%Y%m%d %H:%M:%S")
    
    symbol_name = (
        contract.pair() if hasattr(contract, "pair")
        else contract.localSymbol if hasattr(contract, "localSymbol")
        else contract.symbol if hasattr(contract, "symbol")
        else "UNKNOWN_SYMBOL"
    )

    print(
        f"Attempting to pull '{what_to_show}' data for contract: {symbol_name}"
    )

    parsed_target_delta = None
    use_specific_duration_logic = False
    target_start_date_obj = None

    if history_duration_arg:
        parsed_target_delta = parse_duration_to_relativedelta(history_duration_arg)
        if parsed_target_delta:
            use_specific_duration_logic = True
            target_start_datetime = now_datetime - parsed_target_delta
            target_start_date_obj = target_start_datetime.date()
            print(
                f"Fetching data for approximately {history_duration_arg}, back to around {target_start_date_obj.strftime('%Y%m%d')}."
            )
        else:
            print(
                f"Warning: Could not parse provided duration '{history_duration_arg}'. Defaulting to fetching all available data."
            )

    dt_for_api_call = current_initial_dt_str
    retries = 0

    while True:
        api_call_duration_str = "1 Y"
        print(
            f"Requesting '{what_to_show}' for {symbol_name} ending {dt_for_api_call}, duration {api_call_duration_str}..."
        )

        current_bars_chunk = ib_client.reqHistoricalData(
            contract,
            endDateTime=dt_for_api_call,
            durationStr=api_call_duration_str,
            barSizeSetting="1 day",
            whatToShow=what_to_show,
            useRTH=False,
            formatDate=1,
        )
        ib_client.sleep(0.1)

        if not current_bars_chunk:
            print(f"No more '{what_to_show}' data returned by API for this period.")
            break

        oldest_bar_in_chunk = current_bars_chunk[0]
        oldest_bar_date_obj_in_chunk = oldest_bar_in_chunk.date

        if not isinstance(oldest_bar_date_obj_in_chunk, date):
            print(
                f"Warning: bar.date is not a datetime.date object, it's {type(oldest_bar_date_obj_in_chunk)}. Adjusting logic or expect errors."
            )

        if use_specific_duration_logic:
            eligible_bars_from_chunk = []
            stop_fetching_more_data = False

            for bar_data in current_bars_chunk:
                if bar_data.date >= target_start_date_obj:
                    eligible_bars_from_chunk.append(bar_data)
                else:
                    stop_fetching_more_data = True

            if eligible_bars_from_chunk:
                barsList = eligible_bars_from_chunk + barsList
            if stop_fetching_more_data:
                print(f"Duration Mode: Reached target history depth for '{what_to_show}'.")
                break
        else:
            barsList = current_bars_chunk + barsList

        dt_date_part_str = (
            dt_for_api_call.split()[0] if " " in dt_for_api_call else dt_for_api_call
        )

        if oldest_bar_date_obj_in_chunk.strftime("%Y%m%d") == dt_date_part_str:
            retries += 1
            if retries >= 3:
                print(
                    "Max retries reached. Assuming no more older distinct data available."
                )
                break
        else:
            retries = 0

        dt_for_api_call = oldest_bar_date_obj_in_chunk.strftime("%Y%m%d") + " 23:59:59"

    if not barsList:
        print(
            f"No historical '{what_to_show}' data ultimately collected for contract {symbol_name}."
        )
        return None

    print(f"Converting {len(barsList)} '{what_to_show}' bars to DataFrame...")
    
    # Process data based on what was requested
    if what_to_show == "MIDPOINT":
        df = util.df(barsList)
    elif what_to_show == "BID_ASK":
        # For BID_ASK, close = avg ask, open = avg bid. We calculate the spread.
        spread_data = [
            {"date": bar.date, "spread": bar.close - bar.open} for bar in barsList
        ]
        df = pd.DataFrame(spread_data)
    else:
        df = util.df(barsList)

    if df is None or df.empty:
        print(f"DataFrame is empty after processing '{what_to_show}' for {symbol_name}.")
        return None
    
    df["symbol"] = symbol_name
    return df


def pull_contract_data(contract, ib_client, history_duration_arg=None):
    """
    Pulls historical MIDPOINT and BID_ASK spread data for a given contract and merges them.
    """
    # 1. Pull Midpoint data
    midpoint_df = _fetch_and_process_data(
        contract, ib_client, history_duration_arg, "MIDPOINT"
    )

    # 2. Pull Bid/Ask data to calculate the spread
    spread_df = _fetch_and_process_data(
        contract, ib_client, history_duration_arg, "BID_ASK"
    )

    # 3. Merge the two DataFrames
    if midpoint_df is None or midpoint_df.empty:
        print(f"No midpoint data for {contract.localSymbol if hasattr(contract, 'localSymbol') else 'contract'}, cannot proceed with merge.")
        return None
    
    if spread_df is None or spread_df.empty:
        print(f"No spread data for {contract.localSymbol if hasattr(contract, 'localSymbol') else 'contract'}. Returning only midpoint data.")
        return midpoint_df

    print(f"Merging midpoint and spread data for {spread_df['symbol'].iloc[0]}...")
    # Merge on date and symbol to combine the datasets
    merged_df = pd.merge(midpoint_df, spread_df, on=["date", "symbol"], how="left")

    print(f"Successfully pulled and merged data for {merged_df['symbol'].iloc[0]}. Total points: {len(merged_df)}")
    return merged_df


# --- Main Execution ---
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
contracts = [Forex(s, exchange="IDEALPRO") for s in symbols]
out = pd.concat(
    [pull_contract_data(contract, ib, args.history_duration) for contract in contracts]
)

if out is not None and not out.empty:
    out.to_csv("/tmp/fx_prices.csv")
    print("Script finished and data saved to /tmp/stonks2.csv")
else:
    print("Script finished, but no data was collected to save.")
