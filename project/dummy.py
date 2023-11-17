def fix_timezone(df):
    df.index = pd.DatetimeIndex(df.index).tz_localize(None, ambiguous='infer').tz_localize('UTC')
    return df
