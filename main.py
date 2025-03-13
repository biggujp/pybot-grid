import MetaTrader5 as mt5
import pandas as pd
import time

# Initialize MT5 connection
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# Define symbol and timeframe
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_H1

# Define grid strategy parameters
grid_size = 10  # in pips
take_profit = 20  # in pips
stop_loss = 10  # in pips
lot_size = 0.01  # Adjusted lot size for $100 capital

# Function to close all open orders
def close_all_orders(symbol):
    open_positions = mt5.positions_get(symbol=symbol)
    if open_positions is None:
        print("No positions to close")
        return

    for position in open_positions:
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,
            "magic": 234000,
            "comment": "Close all orders",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close order {position.ticket}, retcode={result.retcode}")

# Function to check if market is about to close
def is_market_closing():
    current_time = time.localtime()
    return current_time.tm_hour == 23 and current_time.tm_min >= 55

# Function to check if market is open
def is_market_open():
    current_time = time.localtime()
    return current_time.tm_hour == 0 and current_time.tm_min < 5

# Function to get historical data
def get_historical_data(symbol, timeframe, n=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# Function to place a buy order
def place_buy_order(symbol, lot_size, price, stop_loss, take_profit):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": price - stop_loss * 0.0001,
        "tp": price + take_profit * 0.0001,
        "deviation": 10,
        "magic": 234000,
        "comment": "Grid strategy buy",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    return result

# Function to place a sell order
def place_sell_order(symbol, lot_size, price, stop_loss, take_profit):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": price + stop_loss * 0.0001,
        "tp": price - take_profit * 0.0001,
        "deviation": 10,
        "magic": 234000,
        "comment": "Grid strategy sell",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    return result

# Main trading loop
while True:
    # Get the latest data
    data = get_historical_data(symbol, timeframe)
    last_close = data['close'].iloc[-1]
    print(data)
    for i in range(1, 6):
        buy_price = last_close - i * grid_size * 0.0001
        place_buy_order(symbol, lot_size, buy_price, stop_loss, take_profit)
    # last_close = data['close'].iloc[-1]

    # # Place grid orders
    # for i in range(1, 6):
    #     buy_price = last_close - i * grid_size * 0.0001
    #     sell_price = last_close + i * grid_size * 0.0001
    #     place_buy_order(symbol, lot_size, buy_price, stop_loss, take_profit)
    #     place_sell_order(symbol, lot_size, sell_price, stop_loss, take_profit)

    # # Wait for the next hour
    # time.sleep(3600)

# Shutdown MT5 connection
mt5.shutdown()