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

#=============================================================================

#Function that calculates correlation given two stocks (strings), produces a dataframe with correlation values
def correlation(stock1, stock2):
    #Create portfolio of monthly returns 
    start_date = '2021-10-20'
    end_date = '2023-11-20'
    stock1_hist = yf.Ticker(stock1).history(start=start_date, end=end_date, interval='1mo')
    stock2_hist = yf.Ticker(stock2).history(start=start_date, end=end_date, interval='1mo')
    
    #Create DataFrame
    prices = pd.DataFrame(stock1_hist.Close)
    prices.columns = [stock1]
    prices[stock2] = stock2_hist.Close
    returns = prices.pct_change()
    #Drop NaN values
    returns.drop(index=returns.index[0], inplace=True)
    
    #Calculate correlation between two stocks   
    return returns.corr()
    
#=============================================================================

# Globally defined variable, to be used in multiple functions
closing_date = '2023-11-20'
exchange_rate = yf.Ticker('CADUSD=x').history().loc[closing_date, 'Close']

#Function to convert stock price from USD to CAD, consumes a USD price and returns a CAD price
def USD_to_CAD_converter(usd_price):
    cad_price = usd_price/exchange_rate
    return cad_price

USD_to_CAD_converter(12)

#=============================================================================

#Function to produce dataframe portfolio, consumes a dataframe that stores tickers and their chosen weights
def make_portfolio(dataframe):
    #Define Variables
    money = 750000
    flat_fee = 4.95
    i = 0
    
    # Create Empty DataFrame and lists
    Portfolio_Final = pd.DataFrame()
    ticker_lst = [0]*len(dataframe)
    price_lst = [0]*len(dataframe)
    currency_lst = [0]*len(dataframe)
    num_shares_lst = [0]*len(dataframe)
    value_lst = [0]*len(dataframe)
    weight_lst = [0]*len(dataframe)
    index_lst = [0]*len(dataframe)
    
    # Subtract flat fee of purchasing stocks from total investment funds
    money -= flat_fee*len(dataframe)
    
    # Create lists to store data for each ticker
    while i < len(dataframe):
        ticker_lst[i] = dataframe.Ticker[i]
        currency_lst[i] = yf.Ticker(dataframe.Ticker[i]).fast_info['currency']      
        # If stock currency is in USD, convert price to CAD
        if currency_lst[i]=='USD':
            price_lst[i] = USD_to_CAD_converter(yf.Ticker(dataframe.Ticker[i]).history().loc[closing_date, 'Close'])
        else:
            price_lst[i] = yf.Ticker(dataframe.Ticker[i]).history().loc[closing_date, 'Close']
        num_shares_lst[i] = (money*dataframe.Weight[i])/price_lst[i]
        value_lst[i] = num_shares_lst[i]*price_lst[i]
        weight_lst[i] = dataframe.Weight[i]
        index_lst[i] = i+1
        i += 1
    
    # Create DataFrame with required stock information
    Portfolio_Final['Ticker'] = ticker_lst
    Portfolio_Final['Price'] = price_lst
    Portfolio_Final['Currency'] = currency_lst
    Portfolio_Final['Shares'] = num_shares_lst
    Portfolio_Final['Value'] = value_lst
    Portfolio_Final['Weight'] = weight_lst
    Portfolio_Final['Total Weight'] = Portfolio_Final.Weight.sum()
    Portfolio_Final['Total Value'] = Portfolio_Final.Value.sum() + flat_fee*len(dataframe)
    
    #Change index of portfolio
    Portfolio_Final.set_index(pd.Series(index_lst), inplace = True)
    
    return Portfolio_Final



