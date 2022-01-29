# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import requests

ACCESS = "aggFxh5VPtu0JOx6ibVwWg9K00xdTgaJ5eOGJwao"
SECRET = "xZpuFUMldXHSZrLBxuqfP8MRD0Rb9mv9wUx7xhkX"

SLACK_TOKEN = "" # 슬랙 키

FEES = 0.9995
TICKER = "KRW-BTC"
DATA_LEN = 500
BTC = "BTC"

MINUTE = 15

current_price = 0



###

# 로그인
upbit = pyupbit.Upbit(ACCESS, SECRET)

###

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
    print(str(datetime.datetime.now()) + "\t" + text)

    # print(response, type(response))
    # print("<Response [200]>" == str(response), str(response))
    print("슬랙 전송 성공 port success" if str(response) else "슬랙 전송 실패 port fail")


def printMessage(status, cp, message):
    btc = get_balance(BTC)
    krw = get_balance("KRW")


    post_message("\t" + status  + 
    "\n, 현재 코인 금액 : " + str(cp) + 
    "\n, 현재 보유 코인 수 : " + str(btc) + 
    "\n, 잔고 : " + str(krw) + message +
    "\n, 수수료 : " + str(krw - (krw*FEES))  +
    "\n =======================================\n")
        


###
# post_message(myToken, "#coin-message", "ㄴ")
post_message("auto trade start")



def getMa(df):
    ma5 = df['close'].rolling(5).mean()[-1]
    ma10 = df['close'].rolling(10).mean()[-1]
    ma15 = df['close'].rolling(15).mean()[-1]
    ma25 = df['close'].rolling(25).mean()[-1]

    return (ma5, ma10, ma15, ma25)


def getLow(df):
    return df['low'][-1]

def dmaqhd(df):
    return df['low'][-1]



# (이전현재값, 최소값, 현재가)
# 몇배
# def aucqo(num1, num2, num):

#     result1 = num1 - num2
#     result2 = num - num1

#     if result1 == 0 or result2 == 0:
#         return 0
#     # print(result1, result2)
    
#     return result2 / result1

# 매수금액, 수량, 매도금액
# 수익률
def tndlrfbf(aotneksrk, aotntnfid, aoeheksrk):

    return ((aoeheksrk * aotntnfid) - (aotneksrk * aotntnfid), # 손익가
        ((aoeheksrk-aotneksrk)/aotneksrk)* 100) #손익률



def isDown(df):
    last_close = df['close'][-1]
    last_open_price = df['open'][-1]
    if last_close - last_open_price > 0:
        return False
    else:
        return True

def start():
    m5Value = m10Value = m15Value = m25Value = bCurrentPrice = 0

    try:
        while True:
            time.sleep(1)

            df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE))
            ma5, ma10, ma15, ma25 = getMa(df)


            # print(df)

            # df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE), count=DATA_LEN) 

            # # 비트코인 현재가
            # cp = get_current_price(TICKER)
            

            # percent = percents(value, current_price, cp)

            # btc = get_balance(BTC)

            # 정배열일 경우
            if ma5 > ma10 > ma15 > ma25:
                krw = get_balance("KRW")
                # 음봉일때 돈있으면 매수
                if isDown(df) and krw >= 5000:
                    current_price = pyupbit.get_current_price(TICKER)
                    print(current_price)
                    upbit.buy_market_order(TICKER, krw*FEES)
                    message = ", 매수 수 : " + str(krw*FEES) + "정배열음봉"
                    status = "매수"

                    printMessage(status, current_price, message)

                    m5Value = ma5
                    m10Value = ma10
                    m15Value = ma15
                    m25Value = ma25

                    bCurrentPrice = current_price




                # 돈 없으면 
                elif krw < 5000:

                    current_price = pyupbit.get_current_price(TICKER)
                    btc = get_balance(BTC)

                    # 2배 이상일 경우 팔기
                    # 익절가
                    # (매수금액, 수량, 매도금액)
                    upValue = tndlrfbf(bCurrentPrice, btc, current_price)
                    ######
                    if upValue[1] >= 2:
                        upbit.sell_market_order(TICKER, btc)
                        message = ", 매도 수 : " + str(btc) + "익절 2% 이상"
                        status = "매도"

                        printMessage(status, current_price, message)
                        m5Value = m10Value = m15Value = m25Value = bCurrentPrice = 0

            # 정배열이 아닐 경우
            else:
                btc = get_balance(BTC)
                # 코인 가격이 있다면 팔기
                if btc > 0:
                    current_price = pyupbit.get_current_price(TICKER)

                    upbit.sell_market_order(TICKER, btc)
                    message = ", 매도 수 : " + str(btc) + "이평선 변경"
                    status = "매도"
                    # m5Value = m10Value = m15Value = m25Value = bCurrentPrice = 0
                    print(current_price)
                    printMessage(status, current_price, message)
                    m5Value = m10Value = m15Value = m25Value = bCurrentPrice = 0





    except Exception as e:
        post_message("에러\n" + str(e))

    finally:
        post_message("끝")

start()

# ps ax | grep .py
# nohup python3 abc.py > output.log & 