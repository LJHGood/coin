# -*- coding: utf-8 -*-

import time
import pyupbit
import datetime
import requests
import json


with open("../access.json", "r") as f:
    data = json.load(f)
    ACCESS = data["ACCESS"]
    SECRET = data["SECRET"]
    SLACK_BOT_TOKEN = data["SLACK_BOT_TOKEN"]
    SLACK_APP_TOKEN = data["SLACK_APP_TOKEN"]

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
    ma25 = df['close'].rolling(25).mean()[-1]

    ma5b = ma5[-2]
    ma5 = ma5[-1]

    return {"ma5":ma5, "ma5b":ma5b, "ma25":ma25}


# 매수금액, 수량, 매도금액
# 수익률
def tndlrfbf(aotneksrk, aotntnfid, aoeheksrk):
    return ((aoeheksrk * aotntnfid) - (aotneksrk * aotntnfid), # 손익가
        ((aoeheksrk-aotneksrk)/aotneksrk)* 100) #손익률


def start():
    notValue = 15000

    try:
        while True:
            df = pyupbit.get_ohlcv(TICKER, interval="minute" + str(MINUTE))

            ma = getMa(df)
            ma5 = ma["ma5"]
            ma5b = ma["ma5b"]
            ma25 = ma["ma25"]
    
            if ma5 > ma25:
                b = True
                # 골든
            else:
                # 데스
                b = False


            if (ma25 <= ma5 <= ma25) == False:
                if b: # 골든 영역 # 파는 영역
                    btc = get_balance("BTC")
                    if btc > 0:
                        # print("골든 btc > 0 True")

                        # 추세 하락하면 판다.(기존에 이미 골든영역임)
                        current_price = pyupbit.get_current_price(TICKER)

                        # 이전 ma5가 ma5b 이상이고, ma25가 현재가격 이상일 때
                        if ma5 <= ma5b - notValue and ma25 < current_price:
                            # print("골든 매도")
                            upbit.sell_market_order(TICKER, btc)
                            message = ", 매도 수 : " + str(btc) + "골드 영역 추세선 하락 "
                            status = "매도"
                            printMessage(status, current_price, message)
                            
                            time.sleep(60)
                    else:
                        pass
                        # print("골든 btc > 0 False")

                else: # 데스 영역 # 사는 영역
                    krw = get_balance("KRW")
                    if krw >= 5000:
                        # print("데스 krw >= 5000 True")
                        current_price = pyupbit.get_current_price(TICKER)

                        # 추세 상승하면 산다.(기존에 이미 데스영역임)
                        if ma5b <= ma5 - notValue and current_price < ma25:
                            upbit.buy_market_order(TICKER, krw*FEES)
                            # print("데스 매수")

                            message = ", 매수 수 : " + str(krw*FEES) + "데스 영역 추세선 상승 "
                            status = "매수"
                            printMessage(status, current_price, message)

                            time.sleep(60)

                    else:
                        pass
                        # print("데스 krw >= 5000 False")

            time.sleep(1)
    except Exception as e:
        print(e + " 에러")
        post_message(str(e) + " 에러")

start()