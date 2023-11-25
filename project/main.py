from IPython.display import display, Math, Latex

import pandas as pd
import numpy as np
import numpy_financial as npf
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

##======================================================
#======================== START OF FILTERING
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
        # do not add if currency not specified
        if (not ('currency' in tickers[e].info)): continue
        # keep only if CAD if USD currency
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

#======== END OF FILTERING
#===========================




#=========== START OF DATA IMPORT===============
#================================================

start_date = '2021-10-20'
end_date = '2023-11-20'
    
# Create dataframe of exchange rates
exchange_rates = pd.DataFrame(yf.Ticker('CADUSD=x').history(start=start_date, end=end_date, interval='1mo'))
exchange_rates_df = pd.DataFrame(exchange_rates.Close)
exchange_rates_df.index = exchange_rates_df.index.strftime('%Y-%m-%d')

#Function that consumes list of tickers, produces a dictionary, where key is the ticker, value is a dataframe of only closing prices
def closing_prices(lst_tickers):
    i = 0
    prices_dict={}
    
    # While loop to fill up dictionary
    while i < len(lst_tickers):
        close_prices = pd.DataFrame(yf.Ticker(lst_tickers[i]).history(start=start_date, end=end_date, interval='1mo').Close)
        close_prices.index = close_prices.index.strftime('%Y-%m-%d')
        
        # Convert historical prices to CAD if currency is in USD
        if yf.Ticker(lst_tickers[i]).fast_info['currency'] == 'USD':
            prices_data = pd.DataFrame(close_prices/exchange_rates_df).dropna()
            
            # Assign dictionary key and value
            prices_dict[lst_tickers[i]] = prices_data
        else:
            prices_data = pd.DataFrame(close_prices).dropna()
            
            # Assign dictionary key and value
            prices_dict[lst_tickers[i]] = prices_data
        i += 1
    
    return prices_dict
#==============

# Globally defined variable, to be used in multiple functions
closing_date = '2023-11-20'
exchange_rate = yf.Ticker('CADUSD=x').history().loc[closing_date, 'Close']

#Function to convert stock price from USD to CAD, consumes a USD price and returns a CAD price
def USD_to_CAD_converter(usd_price):
    cad_price = usd_price/exchange_rate
    return cad_price


#===========END OF DATA IMPORT====================
#================================================


#=========START OF STATS==================
#=========================================

weights = [0.20,0.20,0.20,0.10,0.05,0.05,0.05,0.05,0.05,0.05]

#Function that calculates covariance given two stocks (strings), produces a dataframe with correlation values
def correlation(stock1_hist, stock2_hist):
    
    #Create DataFrame
    prices = pd.DataFrame(stock1_hist)
    prices.columns = ['stock1']
    prices['stock2'] = stock2_hist
    
    #Drop NaN values
    returns = prices.pct_change().dropna()
    
    #Calculate correlation between two stocks   
    return returns.corr()['stock2']['stock1']

def calc_modified_sharpe(close):
    return abs(calc_mean(close))*calc_std(close) # modified sharpe ratio = |mean|/std

def calc_mean(close):
    return close.mean()
    
def calc_std(close):
    return close.std()

def relativize(close):
    return close/close.iloc[0] # makes the close relative to the initial price



# METHOD 1
def CalcTop10Sharpe(close_df, p):
    # creates a column with values being the correlation between the anchor 'p' against rest of portfolio
    close_df['Corr'] = close_df['Close'].apply(lambda x : correlation(x.Close.pct_change().dropna(), p.Close.pct_change()))
    
    #sort the portfolio and get the head(10)
    sorted_close = close_df.sort_values('Corr', ascending=False).head(10)
    
    # sums up the portfolios based on our weighting procedure
    close_column = pd.DataFrame()
    i = 0
    for obj in sorted_close['Close']:
        if (not('Sum' in close_column.columns)):
            close_column['Sum'] = relativize(obj.Close) * weights[i]
        else:
            close_column['Sum'] += relativize(obj.Close) * weights[i]
        i+=1
            
            #returns the top10 tickers and the sharpe ratio
    return sorted_close['Ticker'].tolist(), calc_modified_sharpe(close_column['Sum'].pct_change().dropna())



# METHOD 2
def CalcTop10Sharpe2(close_df, p):
    # creates a column with values being the correlation between the anchor 'p' against rest of portfolio
    close_df['Corr'] = close_df['Close'].apply(lambda x : calc_modified_sharpe(x.Close.pct_change().dropna() + p.Close.pct_change()))
    #sort the portfolio and get the head(10)
    sorted_close = close_df.sort_values('Corr', ascending=False).head(10)
    # sums up the portfolios based on our weighting procedure
    corr_sum = 0
    
    for obj1 in sorted_close['Close']:
        for obj2 in sorted_close['Close']:
            corr_sum += correlation(obj1.Close.pct_change().dropna(), obj2.Close.pct_change().dropna())
            
    #returns the top10 tickers and the sharpe ratio
    return sorted_close['Ticker'].tolist(), corr_sum






def CalcTop10Tickers(dict_prices): #dict_prices 
    top10 = []
    sharpe = 0

    # dataframe with ticker and close
    close_df = pd.DataFrame(dict_prices.items(), columns=['Ticker', 'Close'])

    for e in dict_prices:
        p = dict_prices[e]     # choose p is the 'anchor'
        ntop10, nsharpe = CalcTop10Sharpe2(close_df, p)
        if (nsharpe > sharpe): # choose the best combination of 'p'
            top10 = ntop10
            sharpe = nsharpe
    return top10

#===========END OF STATS=============
#=================================



#==========START OF PORTFOLI0===========
#==================================
def weighter(ticker): # takes a ticker lst and turns into a dataframe with ticker as index and weight as value
    df = pd.DataFrame()
    df['tickers']=ticker 
    df['Weight']=weights
    return df.set_index('tickers')

#=============================================================================
# public function
#Function to produce dataframe portfolio, consumes a dataframe that has tickers as index and stores their chosen weights in a column labelled 'Weight'
flat_fee = 4.95

def make_portfolio(dataframe):
    #Define Variables
    money = 750000
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
    
    #Change index of portfolio
    Portfolio_Final.set_index(pd.Series(index_lst), inplace = True)
    
    return Portfolio_Final

#==========


def make_stocks_final(portfolio, filename):
    Stocks_Final = portfolio
    Stocks_Final.drop(columns=['Price', 'Currency', 'Value', 'Weight'], inplace=True)
    
    return Stocks_Final.to_csv(filename)


#=============END OF PORTFOLI=========
#==================================


lst_tickers = get_valid_tickers('Tickers_Example.csv') # lst with only valid tickers
dict_prices = closing_prices(lst_tickers) # dictionary of ticker to close


top10 = CalcTop10Tickers(dict_prices) # gets the top 10 portfolio


Portfolio_Final = make_portfolio(weighter(top10)) # final portfolio


print('Total Weight of the portfolio: ', Portfolio_Final.Weight.sum(), sep='')
print('Total Value of the portfolio: $', Portfolio_Final.Value.sum() + flat_fee*len(Portfolio_Final), sep='')


Portfolio_Final
