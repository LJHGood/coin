import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet


access = "aggFxh5VPtu0JOx6ibVwWg9K00xdTgaJ5eOGJwao"          # 본인 값으로 변경
secret = "xZpuFUMldXHSZrLBxuqfP8MRD0Rb9mv9wUx7xhkX"          # 본인 값으로 변경

# 로그인
upbit = pyupbit.Upbit(access, secret)
# f = open("log10m.txt", "a")
f = open("log5m.txt", "a")
# f = open("log3m.txt", "a")

f.write(str(datetime.datetime.now()) + "\t autotrade start " +  "\n")
f.close()


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


def predict_price_(ticker, df):
    """Prophet으로 당일 종가 가격 예측"""
    # df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=5, freq='min')
    forecast = model.predict(future)
    closeDf = forecast.iloc[-1]
    return closeDf.yhat

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0



fees = 0.9995
ticker = "KRW-BTC"
dataLen = 500
BTC = "BTC"

def m10():
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=500) 

    value = predict_price_(ticker, df)
    f = open("log10m.txt", "a")
    # f = open("log3m.txt", "a")

    btc = get_balance(BTC)
    krw = get_balance("KRW")
    current_price = get_current_price(ticker)
            

    if value - current_price >= 0:
        if krw > 5000:
            upbit.buy_market_order(ticker, krw*fees)
            f.write(str(datetime.datetime.now()) + "\t buy coin " + str(btc) + " krw " + str(krw) + "\n")
        else:
            f.write(str(datetime.datetime.now()) + "\t good coin " + str(btc) + " krw " + str(krw) + "\n")
    else:
        if btc > 0:
            upbit.sell_market_order(ticker, btc)
            f.write(str(datetime.datetime.now()) + "\t sell coin " + str(btc) + " krw " + str(krw) + "\n")
        else:
            f.write(str(datetime.datetime.now()) + "\t wait coin " + str(btc) + " krw " + str(krw) + "\n")

    f.close()

def m5():
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=500) 

    value = predict_price_(ticker, df)
    f = open("log5m.txt", "a")

    btc = get_balance(BTC)
    krw = get_balance("KRW")
    current_price = get_current_price(ticker)
            

    if value - current_price >= 0:
        if krw > 5000:
            upbit.buy_market_order(ticker, krw*fees)
            f.write(str(datetime.datetime.now()) + "\t buy coin " + str(btc) + " krw " + str(krw) + "\n")
        else:
            f.write(str(datetime.datetime.now()) + "\t good coin " + str(btc) + " krw " + str(krw) + "\n")
    else:
        if btc > 0:
            upbit.sell_market_order(ticker, btc)
            f.write(str(datetime.datetime.now()) + "\t sell coin " + str(btc) + " krw " + str(krw) + "\n")
        else:
            f.write(str(datetime.datetime.now()) + "\t wait coin " + str(btc) + " krw " + str(krw) + "\n")

    f.close()


def m3():
    df = pyupbit.get_ohlcv(ticker, interval="minute3", count=500) 

    value = predict_price_(ticker, df)
    f = open("log3m.txt", "a")

    btc = get_balance(BTC)
    krw = get_balance("KRW")
    current_price = get_current_price(ticker)
            

    if value - current_price >= 0:
        if krw > 5000:
            upbit.buy_market_order(ticker, krw*fees)
            f.write(str(datetime.datetime.now()) + "\t buy coin " + str(btc) + " krw " + str(krw) + "\n")
        else:
            f.write(str(datetime.datetime.now()) + "\t good coin " + str(btc) + " krw " + str(krw) + "\n")
    else:
        if btc > 0:
            upbit.sell_market_order(ticker, btc)
            f.write(str(datetime.datetime.now()) + "\t sell coin " + str(btc) + " krw " + str(krw) + "\n")
        else:
            f.write(str(datetime.datetime.now()) + "\t wait coin " + str(btc) + " krw " + str(krw) + "\n")

    f.close()

# m10()
# 10분에 한번씩 실행
# schedule.every(10).minutes.do(lambda: m10())
# schedule.every(10).minutes.do(m10)
m5()
schedule.every(5).minutes.do(m5)
# m3()
# schedule.every(3).minutes.do(m3)


def start():
    try:

        while True:
            schedule.run_pending()

    except:
        f = open("log5m.txt", "a")
        f.write(str(datetime.datetime.now()) + "\t error " +  "\n")
        f.close()
    finally:
        f = open("log5m.txt", "a")
        f.write(str(datetime.datetime.now()) + "\t 끝 " +  "\n")
        f.close()


start()