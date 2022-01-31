# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
import requests
import numpy

ACCESS = "aggFxh5VPtu0JOx6ibVwWg9K00xdTgaJ5eOGJwao"
SECRET = "xZpuFUMldXHSZrLBxuqfP8MRD0Rb9mv9wUx7xhkX"

SLACK_TOKEN = "" # 슬랙 키
# SLACK_TOKEN = ""


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
    ma5 = df['close'].rolling(5).mean()
    ma5b = ma5[-2]
    ma5 = ma5[-1]

    return (ma5, ma5b)


# 매수금액, 수량, 매도금액
# 수익률
def tndlrfbf(aotneksrk, aotntnfid, aoeheksrk):
    return ((aoeheksrk * aotntnfid) - (aotneksrk * aotntnfid), # 손익가
        ((aoeheksrk-aotneksrk)/aotneksrk)* 100) #손익률

# 음봉인지
def isDown(df):
    last_close = df['close'][-1]
    last_open_price = df['open'][-1]
    if last_close - last_open_price > 0:
        return False
    else:
        return True


# 이동평균선 업 되고 있는지
def checkUpTrue(ma5, ma5b):
    return ma5 - 20000 > ma5b




def start():
    bCurrentPrice = 0
    TIME_SLEEP = 120
    while True:
        df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE))

        ma5 = getMa(df)
        ma5b = ma5[1]
        ma5 = ma5[0]

        
        checkUpTrueV = checkUpTrue(ma5, ma5b)

        krw = get_balance("KRW")

        if checkUpTrueV and isDown(df) and krw >= 5000:
            current_price = pyupbit.get_current_price(TICKER)
            upbit.buy_market_order(TICKER, krw*FEES)
            message = ", 매수 수 : " + str(krw*FEES) + "정배열음봉"
            status = "매수"
            bCurrentPrice = current_price

            printMessage(status, current_price, message)
            time.sleep(TIME_SLEEP)

        if bCurrentPrice == 0:
            bCurrentPrice = 46784400.0

        krw = get_balance("KRW")

        if krw < 5000 and checkUpTrueV:
            current_price = pyupbit.get_current_price(TICKER)
            btc = get_balance(BTC)

            # 2배 이상일 경우 팔기
            # 익절가
            # (매수금액, 수량, 매도금액)
            upValue = tndlrfbf(bCurrentPrice, btc, current_price)

            if upValue[1] >= 2:
                upbit.sell_market_order(TICKER, btc)
                message = ", 매도 수 : " + str(btc) + "익절 2% 이상"
                status = "매도"
                printMessage(status, current_price, message)

            
            elif upValue[1] < -0.5:
                upbit.sell_market_order(TICKER, btc)
                message = ", 매도 수 : " + str(btc) + "손절 -0.5% 이하"
                status = "매도"
                printMessage(status, current_price, message)
                time.sleep(TIME_SLEEP)

        if krw < 5000 and checkUpTrueV == False:
            current_price = pyupbit.get_current_price(TICKER)
            btc = get_balance(BTC)

            upbit.sell_market_order(TICKER, btc)
            message = ", 매도 수 : " + str(btc) + "이동평균선 변화"
            status = "매도"
            printMessage(status, current_price, message)
            time.sleep(TIME_SLEEP)


# 220130 09:22 47,320,000,  738158 -> 725464 = 12,694
# 매도, 매수 후 약 2분정도 잠시 대기 수정
# 220130 09:38 47,009,000,  725464 -> 



        time.sleep(1)


start()

# ps ax | grep .py
# nohup python3 abc.py > output.log & 