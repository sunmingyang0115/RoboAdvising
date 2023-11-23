from IPython.display import display, Math, Latex

import pandas as pd
import numpy as np
import numpy_financial as npf
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

#========================

def csv_ticker_to_pd(csv_file):
    return pd.read_csv(csv_file, header=None)

def read_ticker(ticker_strs):
    ticker = {}
    for ticker_str in ticker_strs:
        ticker[ticker_str] = yf.Ticker(ticker_str)
    return ticker

def filter_invalid(monthlies):
    monthlies2 = {}
    for e in monthlies:
        if (len(monthlies[e]) != 0):
            monthlies2[e] = monthlies[e]
    return monthlies2

def get_vols(tickers,start,end,interval):
    closes = {}
    for e in tickers:
        closes[e] = (tickers[e].history(start=start,end=end,interval=interval).Volume)
    return closes

def get_days_in_month(year, month):
    days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    if (year % 4 == 0 and month == 2):
        return 29
    return days_in_month[month]

def filter_volume(monthlies, dailies):
    monthlies2 = {}
    for e in monthlies:
        monthly_vol = purge_inactive_months(monthlies[e], dailies[e])
        if (np.average(monthly_vol) >= 150000):
            monthlies2[e] = monthlies[e]
    return monthlies2

filtering_start_date = '2023-01-01'
fltering_end_date = '2023-10-31'
max_inactive_days = 18

# the function
def filter_tickers_from_csv(csv_file):
  tickers = read_ticker(csv_ticker_to_pd(csv_file))

  monthlies = filter_invalid(get_vols(tickers,filtering_start_date,fltering_end_date,'1mo'))
  dailies = filter_invalid(get_vols(tickers,filtering_start_date,fltering_end_date,'1d'))
  monthlies = filter_volume(dailies,monthlies)
  return monthlies.keys()
  




