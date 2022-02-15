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

cnt = 0

buyList = []

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

def sellBuyThread(target, ma5, ma10, ma15, ma25):
    global cnt
    while True:
        time.sleep(3)

        currentPrice = pyupbit.get_current_price(target)

        b = False
        text = ""

        # if ma15 <= currentPrice < ma25 and target in buyList == False:
        if ma5 > currentPrice and target in buyList == False:
            krw = get_balance("KRW")

            if  5000 > krw :
                b = True
            else:
                krw = krw + upbit.get_amount('ALL')
                buyPrice = (krw / 10) * FEES

                currentPrice
                upbit.buy_market_order(target, buyPrice)
                printMessage("{} 매수 성공 {}원 ".format(target, buyPrice), target)
                buyList.append(target)
                cnt -= 1
                continue

        elif ma25 >= currentPrice:
            text = "{} 손절 ㅠㅠ ".format(target)
            b = True


        if b == False:
            df = pyupbit.get_ohlcv(target, interval="minute" + str(MINUTE))

            cMa5 = getMa(df)
            cMa5b = cMa5["ma5b"]

            cma10 = cMa5["ma10"]
            cMa15 = cMa5["ma15"]
            cMa25 = cMa5["ma25"]
            cMa5 = cMa5["ma5"]


            # 정배열 깨질 때 팔기
            if ma5 > ma10 > ma15 > ma25 == False:
                text = "{} 정배열 깨짐 익절 성공 ".format(target)
                b = True

            if cMa5b > cMa5 + 30000:
                text = "{} 익절 성공 ".format(target)
                b = True
        

        if b:
            targetPrice = get_balance(target[4:])
            if targetPrice == 0:
                printMessage("{} 매수 전 쓰레드 나감(원화 부족 또는 매수조건 불일치) ".format(target), target)

            else:
                if target in buyList:
                    print(target + "삭제")
                    buyList.remove(target)

                upbit.sell_market_order(target, targetPrice)
                printMessage(text, target)
            
            break


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
    global cnt

    try:
        # 이거 계쏙 반복되는데 한번만 가능할듯        
        printMessage("종목 검색", "")

        for ticker in tickers:
            time.sleep(3)

            if ticker in buyList or cnt == 10:
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

                # 데몬 쓰레드
                sellThreading = threading.Thread(target=sellBuyThread, args=(ticker, ma5, ma10, ma15, ma25))
                sellThreading.daemon = True 
                sellThreading.start()
                cnt += 1

        printMessage(" 종목 검색 끝\n 매수된 종목 : {} 매수 대기 종목 개수 : {} ".format(buyList, cnt), "")

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