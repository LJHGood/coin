# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import requests

ACCESS = "aggFxh5VPtu0JOx6ibVwWg9K00xdTgaJ5eOGJwao"
SECRET = "xZpuFUMldXHSZrLBxuqfP8MRD0Rb9mv9wUx7xhkX"
SLACK_TOKEN = "xoxb-2986537769862-3005858119809-2PibeSQ6U0ssj0HsIFSW2NYC" # 슬랙 키

FEES = 0.9995
TICKER = "KRW-BTC"
DATA_LEN = 500
BTC = "BTC"

MINUTE = 3

get_current_price = 0
predict_price = 0


###

# 로그인
upbit = pyupbit.Upbit(ACCESS, SECRET)

###

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


def predict_price(df):
    """Prophet으로 당일 종가 가격 예측"""
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)

    future = model.make_future_dataframe(periods=MINUTE, freq='min')
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

def post_message(text):
    channel = "#coin-message",
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + SLACK_TOKEN},
        data={"channel": channel,"text": str(datetime.datetime.now()) + "\t" + text}
    )
    # print(response, type(response))
    # print("<Response [200]>" == str(response), str(response))
    print("슬랙 전송 성공" if str(response) else "슬랙 전송 실패")

def buySellManager(df):
    global value
    global current_price

    # 기대가
    value = predict_price(df)

    btc = get_balance(BTC)
    krw = get_balance("KRW")

    # 비트코인 현재가
    current_price = get_current_price(TICKER)

    message = ""
    
    # True : 매도
    # False : 매수
    status = True

    if value - current_price >= 0:
        if krw > 5000:
            upbit.buy_market_order(TICKER, krw*FEES)
            message = ", 매수 수 : " + str(krw*FEES)
        else:
            message = ", 매도기다리는중"
        status = True
    else:
        if btc > 0:
            upbit.sell_market_order(TICKER, btc)
            message = ", 매도 수 : " + str(btc)
        else:
            message = ", 매수기다리는중"
        status = False
    
    btc = get_balance(BTC)
    krw = get_balance("KRW")

    post_message("\t" + ("  " if status else "    ") + "기대금액 : " + str(value) + 
        ", 현재 코인 금액 : " + str(current_price) + 
        ", 현재 보유 코인 수 : " + str(btc) + 
        ", 잔고 : " + str(krw) + message)



def mTime(MINUTE):
    df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE), count=DATA_LEN) 
    buySellManager(df)


###

# (기대값, 기존값, 현재값)
def percents(num1, num2, num):
    result1 = num2 - num1
    result2 = num2 - num

    # print(result1, result2)

    if result1 == 0 or result2 == 0:
        return False

    print((100 / result1) * result2)
    if (100 / result1) * result2 >= 80:
        return True
    return False



###
# post_message(myToken, "#coin-message", "ㄴ")
post_message("auto trade start")


# MINUTE 분에 한번씩 실행
mTime(MINUTE)
schedule.every(MINUTE).minutes.do(lambda: mTime(MINUTE))
# m10()
# schedule.every(10).minutes.do(m10)


def start():
    try:
        while True:
            time.sleep(1)

            # (기대값, 기존값, 현재값)
            if percents(value, current_price, get_current_price(TICKER)):
                mTime(MINUTE)

            schedule.run_pending()

    except:
        post_message("에러")
        print("에러")
    finally:
        post_message("끝")

start()

# ps ax | grep .py
# nohup python3 abc.py > output.log &