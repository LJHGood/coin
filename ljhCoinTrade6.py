# -*- coding: utf-8 -*-

from curses.ascii import SI
import time
import pyupbit
import datetime
import requests
import json


with open("./access.json", "r") as f:
    data = json.load(f)
    ACCESS = data['ACCESS']
    SECRET = data['SECRET']
    SLACK_BOT_TOKEN = data['SLACK_BOT_TOKEN']
    SLACK_APP_TOKEN = data['SLACK_APP_TOKEN']

# 수수료 0.9995
FEES = 1 - 0.0005
TICKER = "KRW-BTC"
DATA_LEN = 500
BTC = "BTC"

MINUTE = 15

# 로그인
upbit = pyupbit.Upbit(ACCESS, SECRET)


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


def avg_buy_price(ticker):
    """매수 평균가 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0



# [
#     {
#         'currency': 'KRW', 
#         'balance': '2439680.19221779',
#         'locked': '0.0', 
#         'avg_buy_price': '0', 
#         'avg_buy_price_modified': True, 
#         'unit_currency': 'KRW'
#     }, 
#     {
#         'currency': 'BTC', 
#         'balance': '0.00495656', 
#         'locked': '0.0', 
#         'avg_buy_price': '54691000', 
#         'avg_buy_price_modified': False, 
#         'unit_currency': 'KRW'
#     }
# ]



        
    # {'currency': 'BTC', 'balance': '0.00940771', 'locked': '0.0', 'avg_buy_price': '54743518.3759', 'avg_buy_price_modified': False, 'unit_currency': 'KRW'}]


# print(get_balance("BTC"), upbit.get_balances("BTC"))
# print(upbit.get_balance("BTC"))
# 위  똑같 확인해보자
def post_message(text):
    channel = "#coin-message",
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + SLACK_BOT_TOKEN},
        data={"channel": channel,"text": str(datetime.datetime.now()) + "\t" + text}
    )
    print(str(datetime.datetime.now()) + "\t" + text)

    # print(response, type(response))
    # print("<Response [200]>" == str(response), str(response))
    print("슬랙 전송 성공 port success" if str(response) else "슬랙 전송 실패 port fail")


def printMessage(text):
    current_price = pyupbit.get_current_price(TICKER)

    text = text + "현재 코인 가격 " + str(current_price) + "\n =======================================\n"
    post_message(text)
    print(text)


printMessage("auto trade start")


def getMa(df):
    df = df['close']

    ma5 = df.rolling(5).mean()
    ma10 = df.rolling(10).mean()[-1]
    ma15 = df.rolling(15).mean()[-1]
    ma25 = df.rolling(25).mean()[-1]

    ma5b = ma5[-2]
    ma5bb = ma5[-3]

    return {"ma5":ma5[-1], 
        "ma5b":ma5b,
        "ma5bb":ma5bb, 
        "ma10":ma10, 
        "ma15":ma15, 
        "ma25":ma25, 
    }



# 매수금액, 수량, 매도금액
# 수익률

def tndlrfbf(aotneksrk, aotntnfid, aoeheksrk):
    return ((aoeheksrk * aotntnfid) - (aotneksrk * aotntnfid), # 손익가
        ((aoeheksrk-aotneksrk)/aotneksrk)* 100) #손익률


# 매수금액, 매도금액
def rateOfReturn(aotneksrk, aoeheksrk):
    if aotneksrk == 0 or aoeheksrk == 0:
        return 0
    return ((aoeheksrk-aotneksrk)/aotneksrk)* 100 #손익률


def start():
    notValue = 15000

    buyMeanPrice = 0
    bList = [4, 3, 2, 1]    # 산 금액 비율 /

    sPList = [1, 2, 2.5, 5]    # 팔 때 기준치 /
    bPList = [-1, -1.5, -2, -2.5]    # 살 때 기준치 /

    bIndex = 0              # 산 인덱스
    sIndex = 0              # 판 인덱스
    start = True

    try:
        while True:
            df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE))


            ma = getMa(df)
            ma5 = ma["ma5"]
            ma5b = ma["ma5b"]
            ma5bb = ma["ma5bb"]
            # ma10 = ma["ma10"]
            # ma15 = ma["ma15"]
            # ma25 = ma["ma25"]

            # 내려갔다 올라가는 추세 -> 전부 사기
            if ma5bb > ma5b and ma5 - 30000 > ma5b:
                krw = get_balance("KRW" )

                current_price = pyupbit.get_current_price(TICKER)

                if krw * FEES > 5000:
                    buyPrice = krw * FEES

                    upbit.buy_market_order(TICKER, buyPrice)
                    printMessage("산다" + str(buyPrice) + "무조건 올라가는 추세")


            # 올라갔다가 내려가는 추세 -> 전부 팔기
            elif ma5b > ma5bb and ma5b > ma5 + 30000:
                btc = get_balance("BTC")

                if btc > 0 :
                    sellPrice = btc
                    upbit.sell_market_order(TICKER, sellPrice)
                    printMessage("판다" + str(sellPrice) + "이제 내려가니깐 다판다")


                

            # 올라가는 추세 -> 일부 팔기
            elif  ma5 + 30000 > ma5b > ma5bb:              
                btc = get_balance("BTC")

                current_price = pyupbit.get_current_price(TICKER)
                buyMeanPrice = avg_buy_price("BTC")


                if sIndex >= len(sPList):
                    sIndex = 0

                if btc > 0 and rateOfReturn(buyMeanPrice, current_price) >= sPList[sIndex]:
                    sellPrice = (btc / bList[bIndex])

                    upbit.sell_market_order(TICKER, btc)
                    printMessage("판다" + str(sellPrice) + " " + str(sIndex + 1) + "차 매도")
                    sIndex += 1



            # 내려가는 추세 -> 일부 사기
            elif ma5b > ma5 - 30000:
                krw = get_balance("KRW" )

                current_price = pyupbit.get_current_price(TICKER)

                if bIndex > len(bList):
                    bIndex = 0


                if krw * FEES > 5000:
                    if start:
                        buyMeanPrice = current_price
                        start = False
                    else:
                        buyMeanPrice = avg_buy_price("BTC")

                    if bPList[bIndex] > rateOfReturn(buyMeanPrice, current_price):
                        buyPrice = (krw / bList[bIndex]) * FEES

                        upbit.buy_market_order(TICKER, buyPrice)
                        printMessage("산다" + str(buyPrice) + " " + str(bIndex + 1) + "차 매수")
                        bIndex += 1

            time.sleep(1)

    except Exception as e:
        printMessage(e + " 에러")

start()