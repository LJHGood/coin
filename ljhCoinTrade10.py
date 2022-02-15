# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
import requests
import json
import threading
import pandas

with open("../access.json", "r") as f:
    data = json.load(f)
    ACCESS = data['ACCESS']
    SECRET = data['SECRET']
    SLACK_BOT_TOKEN = "data['SLACK_BOT_TOKEN']"
    # SLACK_APP_TOKEN = "data['SLACK_APP_TOKEN']"


FEES = 1 - 0.0005

MINUTE = 15

buyList = []
buyListWait = []

upbit = pyupbit.Upbit(ACCESS, SECRET)

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


def printMessage(text, ticker):
    if ticker != "":
        current_price = pyupbit.get_current_price(ticker)

        text = "테스트2 " + text + "현재 코인 가격 " + str(current_price) + "\n =======================================\n"

    post_message(text)
    # print(text)


printMessage("test auto trade start", "")

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

# 수익률 매수금액, 매도금액
def rateOfReturn(aotneksrk, aoeheksrk):
    if aotneksrk == 0 or aoeheksrk == 0:
        return 0
    return ((aoeheksrk-aotneksrk)/aotneksrk)* 100 #손익률


# RSI 확인
def getRsi(ohlc: pandas.DataFrame, period: int = 14):
    delta = ohlc["close"].diff()
    ups, downs = delta.copy(), delta.copy()

    ups[ups < 0] = 0 
    downs[downs > 0] = 0 

    AU = ups.ewm(com = period-1, min_periods = period).mean() 
    AD = downs.abs().ewm(com = period-1, min_periods = period).mean() 
    RS = AU/AD 
    return pandas.Series(100 - (100/(1 + RS)), name = "RSI").iloc[-1]


def sellBuyThread(target, ma5, ma10, ma15, ma25, buyList, buyListWait):

    targetPrice = get_balance(target[4:])

    while True:

        currentPrice = pyupbit.get_current_price(target)


        # if ma15 <= currentPrice < ma25 and target in buyList == False:
        if ma5 > currentPrice:
            krw = get_balance("KRW")
            krw = krw + upbit.get_amount('ALL')
            buyPrice = (krw / 10) * FEES

            upbit.buy_market_order(target, buyPrice)
            printMessage("{} 매수 성공 {}원 ".format(target, buyPrice), target)
            buyList.append(target)
            buyListWait.remove(target)

            continue


        if ma25 >= currentPrice:
            if target in buyList:
                buyList.remove(target)

                upbit.sell_market_order(target, targetPrice)
                printMessage("{} 매도 25분봉 이하 (손절 ㅠㅠ) 쓰레드 종료".format(target), target)

            else:
                buyListWait.remove(target)
                printMessage("{} 매수 전 25분봉 이하 쓰레드 나감 ".format(target), target)
            break


        df = pyupbit.get_ohlcv(target, interval="minute" + str(MINUTE))

        cMa5 = getMa(df)
        cMa5b = cMa5["ma5b"]

        cMa10 = cMa5["ma10"]
        cMa15 = cMa5["ma15"]
        cMa25 = cMa5["ma25"]
        cMa5 = cMa5["ma5"]

        # 정배열 깨질 때 팔기
        if (cMa5 > cMa10 > cMa15 > cMa25) == False:
            if target in buyList:
                buyList.remove(target)

                upbit.sell_market_order(target, targetPrice)
                printMessage("{} 매도 정배열 깨짐 (익절) 쓰레드 종료".format(target), target)

            else:
                buyListWait.remove(target)
                printMessage("{} 매수 전 정배열 깨짐 쓰레드 나감 ".format(target), target)

            break



        if cMa5b > cMa5 + 30000:
            if target in buyList:
                buyList.remove(target)

                upbit.sell_market_order(target, targetPrice)
                printMessage("{} 매도 추세선 변화 (익절) 쓰레드 종료".format(target), target)
            else:
                buyListWait.remove(target)
                printMessage("{} 매수 전 추세선 변화 쓰레드 나감 ".format(target), target)
            break

        time.sleep(3)


# upbit.buy_market_order("KRW-BTC", 30000)
# bb = pyupbit.get_current_price("KRW-BTC")
# sellThread("KRW-BTC", bb)
# exit()


def allSell():
    delCurrencys = upbit.get_balances()
    # print(a)

    for delCurrency in delCurrencys:
        currency = delCurrency["currency"]
        balance = delCurrency['balance']
        if currency == "KRW": continue

        upbit.sell_market_order("KRW-" + currency, balance)

def run(tickers):
    try:
        printMessage("종목 검색", "")


        for ticker in tickers:
            b = True

            krw = get_balance("KRW")

            while True:
                if  5000 > krw and b:
                    printMessage(" 원화부족 현금 회수 대기중 ", "")
                    time.sleep(3)
                    b = False

                elif (5000 > krw) == False:
                    break



            time.sleep(3)

            if ticker in buyList or len(buyList) == 10 or len(buyListWait) == 10:
                continue


            df = pyupbit.get_ohlcv(ticker, interval="minute" + str(MINUTE))

            ma = getMa(df)
            ma5 = ma["ma5"]

            ma10 = ma["ma10"]
            ma15 = ma["ma15"]
            ma25 = ma["ma25"]

            ma = getMa(df.iloc[:-1])
            ma5b = ma["ma5"]

            ma10b = ma["ma10"]
            ma15b = ma["ma15"]
            ma25b = ma["ma25"]

            # orderbook = pyupbit.get_orderbook(ticker)
            # ask =  orderbook["total_ask_size"] # 매도량
            # bid = orderbook["total_bid_size"] # 매수량


            # 정배열 전략
            # if ma5 > ma10 > ma15 > ma25 and ask > bid * 1.5:
            if ma5 > ma10 > ma15 > ma25 and (ma5b > ma10b > ma15b > ma25b) == False:
                printMessage("{} 진입 시도".format(ticker), ticker)
                buyListWait.append(ticker)

                # 데몬 쓰레드
                sellThreading = threading.Thread(target=sellBuyThread, args=(ticker, ma5, ma10, ma15, ma25, buyList, buyListWait))
                sellThreading.daemon = True 
                sellThreading.start()

        printMessage(" 종목 검색 끝\n 매수된 종목 : {} 매수 대기 종목 : {} ".format(buyList, buyListWait), "")

    except Exception as e:
        allSell()
        printMessage(str(e) + "error", "")
        # printMessage(str(e), "에러")



def start():
    allSell()

    tickers = pyupbit.get_tickers()
    tickers = [ticker for ticker in tickers if "KRW" in ticker]

    while True:
        # schedule.run_pending() 
        run(tickers)

start()