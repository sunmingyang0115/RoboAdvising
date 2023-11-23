filtering_start_date = '2023-01-01'
fltering_end_date = '2023-10-31'
max_inactive_days = 18

def foreach(data, f):
    newdata = data.copy
    for i in range(len(data)):
        newdata[i] = f(data[i])
    return newdata

def fix_timezone(df):
    df.index = pd.DatetimeIndex(df.index).tz_localize(None, ambiguous='infer').tz_localize('UTC')
    return df
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

def get_inactive_days(df, year, month):
    days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    start = '{}-{}-{}'.format(year,month,'01')
    end = '{}-{}-{}'.format(year,month+1,'01')
    return get_days_in_month(year,month)-len(df.loc[start:end])

def purge_inactive_months(daily, monthly):
    monthly2 = pd.DataFrame()
    for date in monthly.index:
        inactive_days = get_inactive_days(daily, date.year, date.month)
        if (inactive_days < 18):
            monthly2.at[date, 'Close'] = monthly[date]
    return monthly2
  
def filter_volume(monthlies, dailies):
    monthlies2 = {}
    for e in monthlies:
        monthly_vol = purge_inactive_months(monthlies[e], dailies[e])
        if (np.average(monthly_vol) >= 150000):
            monthlies2[e] = monthlies[e]
    return monthlies2

#tickers = read_ticker(['AAPL','TSLA','123'])
#monthlies = filter_invalid(get_vols(tickers,filtering_start_date,fltering_end_date,'1mo'))
#dailies = filter_invalid(get_vols(tickers,filtering_start_date,fltering_end_date,'1d'))
#monthlies = filter_inactive(dailies,monthlies)
#monthlies = filter_volume(dailies,monthlies)
#print(monthlies.keys()) # list of tickers
