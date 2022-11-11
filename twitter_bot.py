import random
import re
import time
from datetime import datetime, timezone
from enum import Enum

import gspread
import pandas
import pytz
import tweepy
from oauth2client.service_account import ServiceAccountCredentials

from user_settings import (
    SPREADSHEET_NAME,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_API_KEY,
    TWITTER_API_KEY_SECRET,
    TWITTER_ORDER,
)

# CSVファイル名
FILE_NAME = "tw_data.csv"
# スプレッドシートインデックス
class SheetIndex(Enum):
    START_ROW = 2
    MESSAGE = 1
    IMAGE = 2
    ONETIME = 3


# 取り出したデータをpandasのDataFrameに変換
# CSVファイルに出力するときの列の名前を定義
LABELS = [
    "ツイートID",
    "ツイート時刻",
    "ツイート本文",
    "いいね数",
    "リツイート数",
    "ID",
    "ユーザー名",
    "アカウント名",
    "自己紹介文",
    "フォロー数",
    "フォロワー数",
    "アカウント作成日時",
    "自分のフォロー状況",
    "アイコン画像URL",
    "ヘッダー画像URL",
    "WEBサイト",
]


def sleep_random():
    sleep_time = random.randint(1, 300)
    print("Random Sleep")
    print(sleep_time)
    time.sleep(sleep_time)


"""
概　要：UTCをJSTに変換する
引　数：u_time:日付
返り値：日本時間
"""


def change_time_JST(u_time):
    # イギリスのtimezoneを設定するために再定義する
    utc_time = datetime(
        u_time.year,
        u_time.month,
        u_time.day,
        u_time.hour,
        u_time.minute,
        u_time.second,
        tzinfo=timezone.utc,
    )
    # タイムゾーンを日本時刻に変換
    jst_time = utc_time.astimezone(pytz.timezone("Asia/Tokyo"))
    # 文字列で返す
    return jst_time.strftime("%Y-%m-%d_%H:%M:%S")


"""
概　要：スプレッドシート読み込み
引　数：なし
返り値：スプレッドシート
"""


def init_google_tools():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_info = ServiceAccountCredentials.from_json_keyfile_name(
        "client_secret.json", scope
    )
    client = gspread.authorize(credentials_info)
    return (
        client.open(SPREADSHEET_NAME).worksheet("シート1"),
        client.open(SPREADSHEET_NAME).worksheet("シート2"),
    )


"""
概　要：Twitter認証
引　数：なし
返り値：TwitterAPIインスタンス
"""


def twitter_oauth():
    # Twitterの認証
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    # api = tweepy.API(auth)

    # 　”wait_on_rate_limit = True”　利用制限にひっかかた時に必要時間待機する
    return tweepy.API(auth, wait_on_rate_limit=True)


"""
概　要：複数ツイート取得
引　数：api:TwitterAPIインスタンス, search_word:検索条件の設定, getting_count:取得件数
返り値：ツイートリスト
"""


def get_tweets(api, search_word="***** min_faves:200", getting_count=1):
    # 検索条件の設定
    # min_favesはいいねの件数が最低200件以上のツイートのみを取得する.変更可能
    # *****に検索キーワードを入力する
    # search_word = '***** min_faves:200'

    # 検索条件を元にツイートを抽出
    return tweepy.Cursor(
        api.search_tweets, q=search_word, tweet_mode="extended", result_type="mixed", lang="ja"
    ).items(getting_count)


"""
概　要：ツイート情報をCSV出力
引　数：tweets:ツイートリスト
返り値：なし
"""


def output_csv(tweets):
    # 取得したツイートを一つずつ取り出して必要な情報をtweet_dataに格納する
    tw_data = []

    for tweet in tweets:
        # ツイート時刻とユーザのアカウント作成時刻を日本時刻にする
        tweet_time = change_time_JST(tweet.created_at)
        create_account_time = change_time_JST(tweet.user.created_at)
        # tweet_dataの配列に取得したい情報を入れていく
        tw_data.append(
            [
                tweet.id,
                tweet_time,
                tweet.full_text,
                tweet.favorite_count,
                tweet.retweet_count,
                tweet.user.id,
                tweet.user.screen_name,
                tweet.user.name,
                tweet.user.description,
                tweet.user.friends_count,
                tweet.user.followers_count,
                create_account_time,
                tweet.user.following,
                tweet.user.profile_image_url,
                tweet.user.profile_background_image_url,
                tweet.user.url,
            ]
        )

    # tw_dataのリストをpandasのDataFrameに変換して、CSVファイルを出力する
    pandas.DataFrame(tw_data, columns=LABELS).to_csv(FILE_NAME, encoding="utf-8-sig", index=False)


"""
概　要：本処理
引　数：なし
返り値：なし
"""


def start(event, context):
    # スプレッドシート読み込み&Googleドライブ準備
    sheet1, sheet2 = init_google_tools()
    print("Google Tools Authorized")

    max_row = len(list(filter(None, sheet1.col_values(SheetIndex.MESSAGE.value))))
    target_row = (
        SheetIndex.START_ROW.value
        if TWITTER_ORDER == 1
        else random.randint(SheetIndex.START_ROW.value, max_row)
    )
    message = sheet1.cell(target_row, SheetIndex.MESSAGE.value).value
    image_pass = sheet1.cell(target_row, SheetIndex.IMAGE.value).value

    # スプレッドシートからツイート情報を取得
    # name_list = get_name_list(sheet1)
    print("Tweet Info Get")

    # Twitter認証
    twitter_api = twitter_oauth()
    print("Twitter Authorized")

    # ランダム時間待機
    print("Random Sleep")
    time.sleep(random.randint(1, 600))

    # ツイートを投稿
    twitter_api.update_status(message)
    # # 画像付きツイート
    # twitter_api.update_with_media(status = "hello tweepy with media", filename = 'hoge.jpg')
    print("Twitter Update")

    # 1回限りのメッセージの場合、別シートに移動する
    if sheet1.cell(target_row, SheetIndex.IMAGE.value).value == 'Yes':
        add_row = len(list(filter(None, sheet2.col_values(SheetIndex.MESSAGE.value)))) + 1
        sheet2.update_cell(add_row, SheetIndex.MESSAGE.value, message)
        sheet2.update_cell(add_row, SheetIndex.IMAGE.value, image_pass)
        sheet1.delete_row(target_row)

    print("COMPLETE !")

    return ""


def test():
    # スプレッドシート読み込み&Googleドライブ準備
    sheet1, sheet2 = init_google_tools()
    print("Google Tools Authorized")

    max_row = len(list(filter(None, sheet1.col_values(SheetIndex.MESSAGE.value))))
    print(f"max row: {max_row}")
    target_row = (
        SheetIndex.START_ROW.value
        if TWITTER_ORDER == 1
        else random.randint(SheetIndex.START_ROW.value, max_row)
    )
    print(f"target row: {target_row}")
    message = sheet1.cell(target_row, SheetIndex.MESSAGE.value).value
    print(f"message: {message}")
    image_pass = sheet1.cell(target_row, SheetIndex.IMAGE.value).value
    print(f"image: {image_pass}")

    # # スプレッドシートからツイート情報を取得
    # # name_list = get_name_list(sheet1)
    # print("Tweet Info Get")

    # Twitter認証
    twitter_api = twitter_oauth()
    print("Twitter Authorized")

    # ランダム時間待機
    time.sleep(random.randint(1, 600))

    # # ツイートを投稿
    twitter_api.update_status(message)
    # # 画像付きツイート
    # twitter_api.update_with_media(status = "hello tweepy with media", filename = 'hoge.jpg')
    # print("Twitter Update")

    add_row = len(list(filter(None, sheet2.col_values(SheetIndex.MESSAGE.value)))) + 1
    sheet2.update_cell(add_row, SheetIndex.MESSAGE.value, message)
    sheet2.update_cell(add_row, SheetIndex.IMAGE.value, image_pass)
    sheet1.delete_row(target_row)

    # print("COMPLETE !")

    # return ''
