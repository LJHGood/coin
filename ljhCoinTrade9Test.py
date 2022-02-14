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

# 매수금액, 매도금액
def rateOfReturn(aotneksrk, aoeheksrk):
    if aotneksrk == 0 or aoeheksrk == 0:
        return 0
    return ((aoeheksrk-aotneksrk)/aotneksrk)* 100 #손익률



def getRsi(ohlc: pandas.DataFrame, period: int = 14):
    delta = ohlc["close"].diff()
    ups, downs = delta.copy(), delta.copy()

    ups[ups < 0] = 0 
    downs[downs > 0] = 0 

    AU = ups.ewm(com = period-1, min_periods = period).mean() 
    AD = downs.abs().ewm(com = period-1, min_periods = period).mean() 
    RS = AU/AD 
    return pandas.Series(100 - (100/(1 + RS)), name = "RSI").iloc[-1]


def sellThread(target, cPrice):
    b = True
    sellDownListIf = [-1, -1.5]
    sellDownListPrice = [4, 1]
    sellDownIndex = 0

    sellUpListIf = [2, 2.5, 3, 4, 5]
    sellUpListPrice = [2, 2, 2, 2, 1]
    sellUpIndex = 0


    while b:
        time.sleep(1)
    
        targetPrice = get_balance(target[4:])
        if targetPrice == 0:
            if target in buyList:
                buyList.remove(target)

            b = False
            continue


        currentPrice = pyupbit.get_current_price(target)
        

        # print(cPrice, currentPrice)
        pp = rateOfReturn(cPrice, currentPrice)

#       익절가
        if pp >= sellUpListIf[sellUpIndex]:
            if pp >= sellUpListIf[sellUpIndex] and sellUpIndex + 1 != len(sellUpListIf):
                time.sleep(1)
                upbit.sell_market_order(target, targetPrice)
                continue

            targetPrice = targetPrice / sellUpListPrice[sellUpIndex]

            upbit.sell_market_order(target, targetPrice)

            printMessage("{} 종목 {} 개 {}% 충족 익절 {}%".format(target, targetPrice, pp, (10 / sellUpListIf[sellUpIndex]) * 10), target)

            sellUpIndex += 1            

#       손절가
        elif pp <= sellDownListIf[sellDownIndex]:
            if pp <= sellDownListIf[-1] and sellDownIndex + 1 != len(sellDownListIf):
                time.sleep(1)
                upbit.sell_market_order(target, targetPrice)
                continue


            targetPrice = targetPrice / sellDownListPrice[sellDownIndex]

            upbit.sell_market_order(target, targetPrice)

            printMessage("{} 종목 {} 개 {}% 충족 손절 {}%".format(target, targetPrice, pp, (10 / sellDownListIf[sellDownIndex]) * 10), target)

            sellDownIndex += 1





# RSI 확인
# 

def run():
    try:
        tickers = pyupbit.get_tickers()
        tickers = [ticker for ticker in tickers if "KRW" in ticker]

        print("서치")
        cnt = 0

        for i, ticker in enumerate(tickers):
            time.sleep(3)

            if ticker in buyList:
                continue            

            df = pyupbit.get_ohlcv(ticker, interval="minute" + str(MINUTE))

            ma = getMa(df)
            ma5 = ma["ma5"]
            ma5b = ma["ma5b"]
            ma5bb = ma["ma5bb"]

            ma10 = ma["ma10"]
            ma15 = ma["ma15"]
            ma25 = ma["ma25"]

            currentPrice = pyupbit.get_current_price(ticker)

            # print(currentPrice)
            # if ma25 > ma15 > ma10 > ma5 and ma5b < currentPrice:
            #     print("{} {} 역배열 가격 : {}".format(i, ticker, currentPrice))
            rsiValue = getRsi(df)
            
            if 30 > rsiValue:
                # 총 보유 자산
                krw = get_balance("KRW") + upbit.get_amount('ALL')
                buyPrice = (krw / 10) * FEES

                if buyPrice > 5000:
                    upbit.buy_market_order(ticker, buyPrice)
                    printMessage("{} {} 조건2 매수".format(i, ticker), ticker)
                    buyList.append(ticker)

                    # 데몬 쓰레드
                    sellThreading = threading.Thread(target=sellThread, args=(ticker, currentPrice))
                    sellThreading.daemon = True 
                    sellThreading.start()
                    cnt += 1
                    continue


            orderbook = pyupbit.get_orderbook(ticker)
            ask =  orderbook["total_ask_size"] # 매도량
            bid = orderbook["total_bid_size"] # 매수량

            # 상승 전략
            # 정배열 조건, 5분봉이 현재가 이상 조건, 거래량 매도가가 1.5배 높을 조건 모두 만족 시


            if ma5 > ma10 > ma15 > ma25 and ma5 < currentPrice and ask > bid * 1.5:
                # 총 보유 자산
                krw = get_balance("KRW") + upbit.get_amount('ALL')
                buyPrice = (krw / 10) * FEES

                if buyPrice > 5000:
                    upbit.buy_market_order(ticker, buyPrice)
                    printMessage("{} {} 조건1 매수".format(i, ticker), ticker)
                    buyList.append(ticker)

                    # 데몬 쓰레드
                    sellThreading = threading.Thread(target=sellThread, args=(ticker, currentPrice))
                    sellThreading.daemon = True 
                    sellThreading.start()

            cnt += 1

        printMessage("{} 종목 서치 끝\n 매수종목 : {} , 개수 : {}".format(cnt, buyList, len(buyList)), "")

    except Exception as e:
        printMessage(str(e), "에러")


def start():
    while True:
        # schedule.run_pending() 
        run()

start()