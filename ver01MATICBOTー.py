import time  #定期的にプログラムを動作させるためのtime.sleep
import pandas as pd
from binance.client import Client
import math


#バイナンスAPIを取り扱うインスタンス
API_KEY = ''
SECRET_KEY = ''
binance = Client(API_KEY, SECRET_KEY,{"timeout":20}) #タイムアウト、インターネットの設定

#取引したい銘柄とトレード条件の設定
ticker = 'MATIC'          #取引したい銘柄
currency = 'USDT'       #USDT建て
interval = 60*5         #チャート足（5分足）
duration = 20           #移動平均サイズ
trading_amount = 60    #一回の売買で取引する金額（ドル）
kirisute =1  #切り捨てする数字、Step＿Size対策
                 
symbol = ticker + currency #自動売買のペア文字列
df = pd.DataFrame()
                 
#取引履歴を渡して購入レートを算出する関数       
def get_ex_rate(history):
    history.reverse()
    for i in range(len(history)):
        if history[i]['isBuyer'] == True:
            return float(history[i]['price'])

#定期的に処理を実行して価格情報を収集する
while True:
    time.sleep(interval)

    ticker_info = binance.get_ticker(symbol=symbol)
    kari = {'price': float(ticker_info['lastPrice'])}
    df2 = pd.DataFrame(kari,index = ["index1"])
    df = pd.concat([df,df2], ignore_index=True)

    if len(df) < duration:
        print("waiting")
        continue

    #ボリンジャーバンドを計算する
    df['SMA'] = df['price'].rolling(window=duration).mean()
    df['std'] = df['price'].rolling(window=duration).std()
    df['-2sigma'] = df['SMA'] - 2*df['std']
    df['+2sigma'] = df['SMA'] + 2*df['std']

    print("processing")

    #保有ポジションの確認
    ticker_balance = binance.get_asset_balance(asset=ticker)
    num = round(float(ticker_balance['free']),8) #とりあえず8ケタで四捨五入
    position = math.floor(num * 10 ** kirisute) / (10 ** kirisute) #step size対策で切り捨て
    #条件が揃ったら売り注文を出す
    if position:
        history = binance.get_my_trades(symbol=symbol)
        if df['price'].iloc[-1] > df['+2sigma'].iloc[-1] \
                and get_ex_rate(history) < df['price'].iloc[-1]:

            order = binance.order_market_sell(symbol=symbol, quantity=position)
            message = 'sell ' + str(position) + ticker + ' @' + ticker_info['lastPrice']
            print(message)
                 
    #条件が揃ったタイミングで買い注文を出す
    else:
        if df['price'].iloc[-1] < df['-2sigma'].iloc[-1]:
            last_price = float(ticker_info['lastPrice']) 
            amount = round(trading_amount / last_price,1) 
            #print(trading_amount)
            #print(last_price)
            #print(amount)
            order = binance.order_market_buy(symbol=symbol, quantity=amount) 
            message = 'buy ' + str(amount) + ticker + ' @' + ticker_info['lastPrice']
            print(message)
                 
    #価格やボリンジャーバンドの情報を更新する
    df = df.iloc[1:, :]