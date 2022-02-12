# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
import requests
import json
import schedule

with open("../access.json", "r") as f:
    data = json.load(f)
    ACCESS = "data['ACCESS']"
    SECRET = "data['SECRET']"
    SLACK_BOT_TOKEN = "data['SLACK_BOT_TOKEN']"
    SLACK_APP_TOKEN = "data['SLACK_APP_TOKEN']"

# 수수료 0.9995
FEES = 1 - 0.0005
TICKER = "KRW-BTC"
DATA_LEN = 500
BTC = "BTC"

MINUTE = 15

# 로그인
# upbit = pyupbit.Upbit(ACCESS, SECRET)



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

    text = "테스트1" + text + "현재 코인 가격 " + str(current_price) + "\n =======================================\n"
    post_message(text)
    # print(text)


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



def run():
    try:
        while True:
            df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE))

            ma = getMa(df)
            ma5 = ma["ma5"]
            ma5b = ma["ma5b"]
            ma5bb = ma["ma5bb"]

            print(ma5, ma5b, ma5bb)
            if ma5bb > ma5b and ma5 - 30000 > ma5b:
                    # upbit.buy_market_order(TICKER, buyPrice)
                    printMessage("무조건 올라가는 추세 다산다")


            # 올라갔다가 내려가는 추세 -> 전부 팔기
            elif ma5b > ma5bb and ma5b > ma5 + 30000:
                # upbit.sell_market_order(TICKER, sellPrice)
                printMessage("내려가니깐 다판다")


    except Exception as e:
        printMessage(str(e) + " 에러")


def start():
    while True:
        # schedule.run_pending() 
        run()

        time.sleep(1)

start()