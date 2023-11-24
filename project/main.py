from IPython.display import display, Math, Latex

import pandas as pd
import numpy as np
import numpy_financial as npf
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

#========================
#private-functions
def csv_ticker_to_pd(csv_file):
    # reads csv_file with pandas
    return pd.read_csv(csv_file, header=None)

def read_ticker(ticker_strs):
    # creates a dictionary that assigns the str with it's respective ticker
    ticker = {}
    for ticker_str in ticker_strs:
        ticker[ticker_str] = yf.Ticker(ticker_str)
    return ticker

def filter_invalid(data):
    # removes elements that have 0 length (i.e. unlisted stocks)
    data2 = {}
    for e in data:
        if (len(data[e]) != 0):
            data2[e] = data[e]
        else:
            print('removed',e,'; no data')
    return data2

def get_vols(tickers,start,end,interval):
    # gets the volume given a ticker dictionary
    closes = {}
    for e in tickers:
        closes[e] = (tickers[e].history(start=start,end=end,interval=interval).Volume)
    return closes

def get_days_in_month(year, month):
    # calculates the days in a year
    days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    if (year % 4 == 0 and month == 2): # leap year
        return 29
    return days_in_month[month]

def get_inactive_days(df, year, month): 
    # function that gets the days in a month
    start = '{}-{}-{}'.format(year,month,'01')
    end = '{}-{}-{}'.format(year,month+1,'01')
    return get_days_in_month(year,month)-len(df.loc[start:end])

def purge_inactive_months(daily, monthly):
    # removes months that have more than 18 inactive days
    monthly2 = pd.DataFrame()
    for date in monthly.index:
        inactive_days = get_inactive_days(daily, date.year, date.month)
        if (inactive_days < 18): # keep months that have less than 18 inactive days
            monthly2.at[date, 'Close'] = monthly[date]
    return monthly2

def filter_volume(monthlies, dailies):
    # removes monthly data that do not have enough volume
    monthlies2 = {}
    for e in monthlies:
        if (not (e in dailies.keys())): continue # if daily data does not exist for some reason
        
        monthly_vol = purge_inactive_months(monthlies[e], dailies[e])
        average = np.average(monthly_vol)
        if (average >= 150000): # keep stock if average is at least 150000
            monthlies2[e] = monthlies[e]
        else:
            print('removed',e,'; not enough average volume: ',average)
    return monthlies2

def filter_currency(tickers):
    tickers2 = {}
    for e in tickers:
        if (not ('currency' in tickers[e].info)): continue
        if (tickers[e].info['currency'] == 'USD' or tickers[e].info['currency'] == 'CAD'):
            tickers2[e] = tickers[e]
    return tickers2
            

filtering_start_date = '2023-01-01'
fltering_end_date = '2023-10-31'
max_inactive_days = 18
#=========================
# public function
# returns a list of tickers, inputs csv_file
def get_valid_tickers(filename):
    ticker_df = csv_ticker_to_pd(filename) # dataframe with one column (tickers)
    tickers_lst = ticker_df[0].tolist() # list of tickers
    tickers = filter_currency(read_ticker(tickers_lst)) # dictionary (ticker str : ticker object)
    monthlies = filter_invalid(get_vols(tickers,filtering_start_date,fltering_end_date,'1mo'))
    dailies = filter_invalid(get_vols(tickers,filtering_start_date,fltering_end_date,'1d'))
    monthlies = filter_volume(dailies,monthlies) # filter by volumes
    return list(monthlies.keys())

#=============================================================================
#public function

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
# public function

# Globally defined variable, to be used in multiple functions
closing_date = '2023-11-20'
exchange_rate = yf.Ticker('CADUSD=x').history().loc[closing_date, 'Close']

#Function to convert stock price from USD to CAD, consumes a USD price and returns a CAD price
def USD_to_CAD_converter(usd_price):
    cad_price = usd_price/exchange_rate
    return cad_price

USD_to_CAD_converter(12)

#==========

def weighter(ticker):
    df = pd.DataFrame()
    df['tickers']=ticker
    df['Weight']=[0.20,0.20,0.20,0.10,0.05,0.05,0.05,0.05,0.05,0.05]
    return (df.set_index('tickers'))

#=============================================================================
# public function

#Function to produce dataframe portfolio, consumes a dataframe that has tickers as index and stores their chosen weights in a column labelled 'Weight'
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
        ticker_lst[i] = dataframe.index[i]
        currency_lst[i] = yf.Ticker(ticker_lst[i]).fast_info['currency']      
        # If stock currency is in USD, convert price to CAD
        if currency_lst[i]=='USD':
            price_lst[i] = USD_to_CAD_converter(yf.Ticker(ticker_lst[i]).history().loc[closing_date, 'Close'])
        else:
            price_lst[i] = yf.Ticker(ticker_lst[i]).history().loc[closing_date, 'Close']
        num_shares_lst[i] = (money*dataframe.loc[ticker_lst[i], 'Weight'])/price_lst[i]
        value_lst[i] = num_shares_lst[i]*price_lst[i]
        weight_lst[i] = dataframe.loc[ticker_lst[i], 'Weight']
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
#======

def make_stocks_final(portfolio, filename):
    Stocks_Final = portfolio
    Stocks_Final.drop(columns=['Price', 'Currency', 'Value', 'Weight', 'Total Weight', 'Total Value'], inplace=True)
    
    return Stocks_Final.to_csv(filename+'.csv')

#===========================



#Function that consumes list of tickers and produces a dictionary, where key is the ticker, value is a dataframe of closing prices

def closing_prices(lst_tickers):
    start_date = '2021-10-20'
    end_date = '2023-11-20'
    i = 0
    prices_dict={}
    
    while i < len(lst_tickers):
        prices_data = pd.DataFrame(yf.Ticker(lst_tickers[i]).history(start=start_date, end=end_date, interval='1mo').Close)
        prices_dict[lst_tickers[i]] = prices_data
        i += 1
    
    return prices_dict
