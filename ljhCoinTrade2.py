# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
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
    # print(str(datetime.datetime.now()) + "\t" + text)

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

def getMa5(df):
    ma5 = df['close'].rolling(5).mean()[-1]
    return ma5

# 매수금액, 수량, 매도금액
# 수익률
def tndlrfbf(aotneksrk, aotntnfid, aoeheksrk):

    # result = ((aoeheksrk * aotntnfid) - (aotneksrk * aotntnfid), # 손익가
    #     ((aoeheksrk-aotneksrk)/aotneksrk)* 100) #손익률

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
def checkUp(data):
    sumValue = 0
    for ii in range(len(data) - 1):
        sumValue += data[ii] - data[ii + 1]

    return -(sumValue / len(data))

def checkUpTrue(ma5, listData, resultData):
    # + 개수 제한 : 플러스 70개 이상 시 True 반환(상승)
    L = 100
    checkLen = 80

    if len(listData) >= L:
        del listData[0]
    
    listData.append(ma5)

    if len(resultData) >= L:
        del resultData[0]

    resultData.append(checkUp(listData))

    cnt = 0

    for ii in resultData:
        if ii > 0:
            cnt = cnt + 1
    # print(resultData, cnt > checkLen)
    return cnt > checkLen






def start():
    listData = []
    resultData = []
    bCurrentPrice = 0

    try:
        while True:
            time.sleep(1)

            df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE))
            ma5 = getMa5(df)



            krw = get_balance("KRW")
            # 5분 추세선 올라가면서, 음봉일때 돈있으면 매수
            checkUpTrueV = checkUpTrue(ma5, listData, resultData)

            if checkUpTrueV and isDown(df) and krw >= 5000:
            # if checkUpTrueV and krw >= 5000:
                print(checkUpTrueV, " ffasdfasdfsadfas")
                current_price = pyupbit.get_current_price(TICKER)
                upbit.buy_market_order(TICKER, krw*FEES)
                message = ", 매수 수 : " + str(krw*FEES) + "정배열음봉"
                status = "매수"
                bCurrentPrice = current_price

                printMessage(status, current_price, message)

            if bCurrentPrice == 0:
                bCurrentPrice = 46700000.0

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

                    listData = []
                    resultData = []
                
                elif upValue[1] < -0.5:
                    upbit.sell_market_order(TICKER, btc)
                    message = ", 매도 수 : " + str(btc) + "손절 0.5% 이상 CheckTrue==True"
                    status = "매도"
                    printMessage(status, current_price, message)
                    listData = []
                    resultData = []

            if krw < 5000 and checkUpTrueV == False:
                current_price = pyupbit.get_current_price(TICKER)
                btc = get_balance(BTC)

                upbit.sell_market_order(TICKER, btc)
                message = ", 매도 수 : " + str(btc) + "이동평균선 변화"
                status = "매도"
                printMessage(status, current_price, message)
                listData = []
                resultData = []

    except Exception as e:
        post_message("에러\n" + str(e))

    finally:
        post_message("끝")

start()

# ps ax | grep .py
# nohup python3 abc.py > output.log & 