import pytz
import streamlit as st
import pandas as pd
import yfinance
import pickle
import datetime


st.write("# Creating a portfolio out of Nifty50 Stocks")

URL = "https://www1.nseindia.com/content/indices/ind_nifty50list.csv"
start = st.date_input("Input Simulation Start date", value=(datetime.datetime(year=2020, month=10, day=1)))
simulation_start = datetime.datetime(start.year, start.month, start.day).replace(tzinfo=pytz.UTC)
end = datetime.datetime.utcnow()
d_100 = datetime.timedelta(days=100)
d_1 = datetime.timedelta(days=1)
strategy_end = simulation_start - d_1
strategy_start = strategy_end - d_100

try:
    with open(f"nifty50_symbols_{datetime.datetime.now().month}.pickle", "rb") as f:
        symbols = pickle.load(f)

    with open(f"nifty50_{datetime.datetime.now().month}.pickle", "rb") as f:
        df = pickle.load(f)

    with open("company_prices_df_dict.pickle", "rb") as f:
        company_prices_df_dict = pickle.load(f)

except FileNotFoundError:
    df = pd.read_csv(URL, index_col="Company Name")
    symbols = df["Symbol"].to_list()

    with open(f"nifty50_{datetime.datetime.now().month}.pickle", "wb") as f:
        pickle.dump(df, f)

    with open(f"nifty50_symbols_{datetime.datetime.now().month}.pickle", "wb") as f:
        pickle.dump(symbols, f)

    company_prices_df_dict = {}
    for symbol in symbols:
        data = yfinance.download(f"{symbol}.NS", start=simulation_start, end=end, progress=False)
        company_prices_df_dict[symbol] = data
    with open("company_prices_df_dict.pickle", "wb") as f:
        pickle.dump(company_prices_df_dict, f)

# strategy_company_prices_df_dict = {}
# for symbol in symbols:
#     data = yfinance.download(f"{symbol}.NS", start=strategy_start, end=strategy_end, progress=False)
#     strategy_company_prices_df_dict[symbol] = data
# with open("strategy_company_prices_df_dict.pickle", "wb") as f:
#     pickle.dump(strategy_company_prices_df_dict, f)

with open("strategy_company_prices_df_dict.pickle", "rb") as f:
    strategy_company_prices_df_dict = pickle.load(f)

starting_stocks_dict = {}

for symbol in symbols:
    starting_stocks = 20000 / company_prices_df_dict[symbol]['Open'][simulation_start]
    starting_stocks_dict[symbol] = starting_stocks

strategy_dict = {}

for symbol in strategy_company_prices_df_dict:
    strategy_df = strategy_company_prices_df_dict[symbol]
    strategy_dict[symbol] = (strategy_df["Close"][-1]
                             / strategy_df["Close"][-0]) - 1

strategy_top_10 = sorted(strategy_dict.items(), key=lambda x: x[1], reverse=True)[:10]

equity_curve = [company_prices_df_dict[symbol]["Close"] * starting_stocks_dict[symbol] for symbol in symbols]

index_df = yfinance.download("^NSEI", start=simulation_start, end=end, progress=False)
index_stocks = 1000000 / index_df["Open"][simulation_start]
index_curve = index_df["Close"] * index_stocks

strategy_stocks = {}

for stock in strategy_top_10:
    starting_stocks_amount = 100000 / company_prices_df_dict[stock[0]]["Open"][simulation_start]
    strategy_stocks[stock[0]] = starting_stocks_amount

strategy_curve = [company_prices_df_dict[stock[0]]["Close"] * strategy_stocks[stock[0]] for stock in strategy_top_10]

curve_df = pd.DataFrame({"Equal alloc buy hold": sum(equity_curve),
                         "Nifty": index_curve, "Performance_strat": sum(strategy_curve)})


st.line_chart(curve_df)
