import ccxt
import requests
import time, schedule
import pandas as pd
from dontshareconfig import API_KEY, SECRET_KEY


# Set up the testnet endpoint
phemex = ccxt.phemex({
    'enableRateLimit': True,
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
})
# phemex.set_sandbox_mode(True)


# Fetch the account balance
balance = phemex.fetch_balance()
# btc_balance = phemex.fetch_balance()['total']['BTC']

# set the symbol
symbol = 'uBTCUSD'

pos_size = 10 
params = {'timeInForce': 'PostOnly',} # if it does not work as a limit order, do not accept the order:
# market orders are meant to execute as quickly as possible at the current market price, 
# while limit orders are meant to specify a price at which an investor is willing to buy or sell
target = 2 

# open_positions() open_positions, openpos_bool, openpos_size, long
def open_positions():
    params = {'type':'swap','code':'USD'}
    phe_bal = phemex.fetch_balance(params=params)
    open_positions = phe_bal['info']['data']['positions']
    openpos_side = open_positions[0]['side']
    openpos_size = open_positions[0]['size']

    if openpos_side == 'Buy':
        openpos_bool = True
        long = True
    elif openpos_side == 'Sell':
        openpos_bool = True
        long = False
    else:
        openpos_bool = False
        long = None

    return open_positions, openpos_bool, openpos_size, long

# ask_bid[0] = ask, [1] = bid
def ask_bid():
    ob = phemex.fetch_order_book(symbol)
    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    return ask,bid

def kill_switch():
    #limit close us
    print('starting the kill switch')
    openposi = open_positions()[1] # true or fale
    long = open_positions()[3]
    kill_size = open_positions()[2]

    print(f'open position: {openposi} | long: {long} | size: {kill_size}')

    while openposi == True:

        print('starting kill switch loop')
        temp_df = pd.DataFrame()
        print('just made a temp df') # ?

        phemex.cancel_all_orders(symbol)
        openposi = open_positions()[1]
        long = open_positions()[3]
        kill_size = open_positions()[2]
        kill_size = int(kill_size)

        ask = ask_bid()[0]
        bid = ask_bid()[1]

        if long == False: # it means we're in a short and we need to buy it back
            phemex.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f'just made a BUY to close order of {kill_size} {symbol} at ${bid}')
            print('sleeping for 30 seconds to see if it fills') # avoid spamming orders
            time.sleep(30)
        elif long == True: # we want to sell at the ask bcs it's the limit
            phemex.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f'just made a SELL to close order of {kill_size} {symbol} at ${ask}')
            print('sleeping for 30 seconds to see if it fills')
            time.sleep(30)
        else:
            print('+++++++++ something I didn\'t expect in the kill switch function')

        openposi = open_positions()[1] # if the loop fails we don't want to keep running it

# Find daily sma

def daily_sma():

    timeframe = '1d'
    limit = 100
    
    # Fetch OHLC data for the past limit timeframe
    ohlcv_data = phemex.fetch_ohlcv(symbol, timeframe= timeframe, limit=limit)
    
    # Convert data to dataframe
    df_d = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Calculate daily SMA
    df_d['sma20_d'] = df_d['close'].rolling(window=20).mean()
    df_d['timestamp'] = pd.to_datetime(df_d['timestamp'], unit = 'ms')
    df_d = df_d.dropna()

    # if bid < 20 day sma : bearish, else bullish
    bid = ask_bid()[1]

    # signals
    df_d.loc[df_d['sma20_d'] > bid, 'sig'] = 'SELL'
    df_d.loc[df_d['sma20_d'] < bid, 'sig'] = 'BUY'

    return df_d

# Find 15 minutes sma

def f15_sma():
    
    timeframe = '15m'
    limit = 100
    
    # Fetch OHLC data for the past limit timeframe
    ohlcv_data = phemex.fetch_ohlcv(symbol, timeframe= timeframe, limit=limit)
    
    # Convert data to dataframe
    df_f = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Calculate daily SMA
    df_f['sma20_15'] = df_f['close'].rolling(window=20).mean()
    df_f['timestamp'] = pd.to_datetime(df_f['timestamp'], unit = 'ms')
    df_f = df_f.dropna()

    # buy price 1&2 and sell price 1&2
    # buy/sell to open around the 15m sma 0.1% under and 0.3% over
    df_f['bp_1'] = df_f['sma20_15'] * 1.001
    df_f['bp_2'] = df_f['sma20_15'] * 0.997
    df_f['sp_1'] = df_f['sma20_15'] * 0.999
    df_f['sp_2'] = df_f['sma20_15'] * 1.003

    return df_f


# pnl_close()[0] is pnlclose and [1] is in_pos [2] is size and [3] is long (True or False)
def pnl_close():
    print('checking to see if it\'s time to exit')

    params = {'type':"swap",'code':'USDT'}
    pos_dict = phemex.fetch_positions(params=params)
    pos_dict = pos_dict[0]

    side = pos_dict['side']
    size = pos_dict['contracts']
    entry_price = float(pos_dict['entryPrice'])
    leverage = pos_dict['leverage']

    current_price = ask_bid()[1] # price someone is willing to buy
    #print(f'side: {side} | entry price : {entry_price} | lev: {leverage}')

    # if hit target, then close
    if side == 'long':
        diff = current_price - entry_price
        long = True
    else:
        diff = entry_price - current_price
        long = False

    try:
        perc = round((diff/entry_price) * leverage, 10)
    except:
        perc = 0

    perc = 100*perc
    print(f'this is our pnl percentage {perc}')

    pnlclose = False
    in_pos = False

    if perc > 0:

        print('we are in a winning position')
        if perc > target:
            print(f'starting the kill switch because we hit our target')
            pnlclose = True
            kill_switch()
        else:   # this is where we would add a stop loss but right now we use the position size instead
            print('we have not hit our target yet')
    elif perc < 0:
        print('we are in a losing position for now')
        in_pos = True
    else:
        print('we are not in position')


    return pnlclose, in_pos,size,long

def bot():

    pnl_close()

    df_d = daily_sma() # 20 days daily sma determines long/short
    df_f = f15_sma() # 15 mins sma provides prices bp_1, bp_2, sp_1, sp_2
    ask = ask_bid()[0]
    bid = ask_bid()[1]

    sig = df_d.iloc[-1]['sig']

    open_size = pos_size/2 # because we want to make 2 orders

    # only run if not in position
    # pnl_close()[0] is pnlclose and [1] is in_pos
    in_pos = pnl_close()[1]
    if in_pos == False:
        if sig == 'BUY':
            print('making an opening order as a BUY')
            bp_1 = df_f.iloc[-1]['bp_1']
            bp_2 = df_f.iloc[-1]['bp_2']
            print(f'this is bp_1: {bp_1} and this is bp_2: {bp_2}')
            phemex.cancel_all_orders(symbol)
            phemex.create_limit_buy_order(symbol, open_size, bp_1, params)
            phemex.create_limit_buy_order(symbol, open_size, bp_2, params)

            print('just made an opening order so going to sleep for 2 mins')
            time.sleep(120) # in case the order is submitted then canceled you don't want to keep getting orders in
        elif sig == 'SELL':
            print('making an opening as a SELL')
            sp_1 = df_f.iloc[-1]['sp_1']
            sp_2 = df_f.iloc[-1]['sp_2']
            print(f'this is sp_1: {sp_1} and this is sp_2: {sp_2}')
            phemex.cancel_all_orders(symbol)
            phemex.create_limit_sell_order(symbol, open_size, sp_1, params)
            phemex.create_limit_sell_order(symbol, open_size, sp_2, params)

            print('just made an opening order so going to sleep for 2 mins')
            time.sleep(120)

    else:
        print('we are in a position already so not making new order')


schedule.every(28).seconds.do(bot) # around 30 secs with 2 secs to run through the code

while True:
    try:
        schedule.run_pending()
    except:
        print('++++ maybe an internet problem ++++')
        time.sleep(30)