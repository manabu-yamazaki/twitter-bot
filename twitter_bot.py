import os
import random

# import re
import time
# from datetime import datetime, timezone
from enum import Enum

import boto3
import gspread

# import pandas
# import pytz
import tweepy
from oauth2client.service_account import ServiceAccountCredentials

from user_settings import (
    FAVORITE_TIME,
    SLEEP_MAX_TIME_LIKE,
    SLEEP_MAX_TIME_TWEET,
    SPREADSHEET_NAME,
    TWEET_MIN_FAVES,
    TWITTER_ORDER,
)

AWS_IMAGE_BUCKET = "myzk"
TEMP_IMAGE_PASS = "/tmp/temp.png"

# # CSVファイル名
# FILE_NAME = "tw_data.csv"
# スプレッドシートインデックス
class SheetIndex(Enum):
    START_ROW = 2
    MESSAGE = 1
    IMAGE = 2
    ONETIME = 3
    SEARCH_WORD = 1


# # 取り出したデータをpandasのDataFrameに変換
# # CSVファイルに出力するときの列の名前を定義
# LABELS = [
#     "ツイートID",
#     "ツイート時刻",
#     "ツイート本文",
#     "いいね数",
#     "リツイート数",
#     "ID",
#     "ユーザー名",
#     "アカウント名",
#     "自己紹介文",
#     "フォロー数",
#     "フォロワー数",
#     "アカウント作成日時",
#     "自分のフォロー状況",
#     "アイコン画像URL",
#     "ヘッダー画像URL",
#     "WEBサイト",
# ]


# """
# 概　要：UTCをJSTに変換する
# 引　数：u_time:日付
# 返り値：日本時間
# """


# def change_time_JST(u_time):
#     # イギリスのtimezoneを設定するために再定義する
#     utc_time = datetime(
#         u_time.year,
#         u_time.month,
#         u_time.day,
#         u_time.hour,
#         u_time.minute,
#         u_time.second,
#         tzinfo=timezone.utc,
#     )
#     # タイムゾーンを日本時刻に変換
#     jst_time = utc_time.astimezone(pytz.timezone("Asia/Tokyo"))
#     # 文字列で返す
#     return jst_time.strftime("%Y-%m-%d_%H:%M:%S")


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
        client.open(SPREADSHEET_NAME).worksheet("ツイートリスト"),
        client.open(SPREADSHEET_NAME).worksheet("ツイート済"),
        client.open(SPREADSHEET_NAME).worksheet("検索ワード"),
    )


"""
概　要：Twitter認証
引　数：なし
返り値：TwitterAPIインスタンス
"""


def twitter_oauth():
    # Twitterの認証
    auth = tweepy.OAuthHandler(os.environ["TWITTER_API_KEY"], os.environ["TWITTER_API_KEY_SECRET"])
    auth.set_access_token(
        os.environ["TWITTER_ACCESS_TOKEN"], os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )

    # ”wait_on_rate_limit = True” 利用制限にひっかかた時に必要時間待機する
    return tweepy.API(auth, wait_on_rate_limit=True)


"""
概　要：複数ツイート取得
twitter_api:TwitterAPIインスタンス, search_word:検索条件の設定, getting_count:取得件数
返り値：ツイートリスト
"""


def get_tweets(twitter_api, search_word="***** min_faves:200", getting_count=1):
    # 検索条件の設定
    # min_favesはいいねの件数が最低200件以上のツイートのみを取得する.変更可能
    # *****に検索キーワードを入力する
    # search_word = '***** min_faves:200'

    # 検索条件を元にツイートを抽出
    return tweepy.Cursor(
        twitter_api.search_tweets,
        q=search_word,
        tweet_mode="extended",
        result_type="mixed",
        lang="ja",
    ).items(getting_count)


"""
概　要：スプレッドシートの検索ワードを基にツイートを検索し、いいね&フォローする
引　数：api:TwitterAPIインスタンス, search_word:検索条件の設定
返り値：なし
"""


def search_tweets_and_method(twitter_api, search_word):
    for tweet in get_tweets(
        twitter_api, f"{search_word} min_faves:{TWEET_MIN_FAVES}", FAVORITE_TIME,
    ):
        # 未いいねの場合はいいねする
        if twitter_api.get_status(tweet.id).favorited:
            time.sleep(random.randint(1, SLEEP_MAX_TIME_LIKE))
            twitter_api.create_favorite(tweet.id)
        # 未フォローの場合はフォローする
        if tweet.user._json["screen_name"] not in twitter_api.friends:
            twitter_api.create_friendship(tweet.user._json["screen_name"])
            print(f'{tweet.user._json["screen_name"]} followed')


# """
# 概　要：ツイート情報をCSV出力
# 引　数：tweets:ツイートリスト
# 返り値：なし
# """


# def output_csv(tweets):
#     # 取得したツイートを一つずつ取り出して必要な情報をtweet_dataに格納する
#     tw_data = []

#     for tweet in tweets:
#         # ツイート時刻とユーザのアカウント作成時刻を日本時刻にする
#         tweet_time = change_time_JST(tweet.created_at)
#         create_account_time = change_time_JST(tweet.user.created_at)
#         # tweet_dataの配列に取得したい情報を入れていく
#         tw_data.append(
#             [
#                 tweet.id,
#                 tweet_time,
#                 tweet.full_text,
#                 tweet.favorite_count,
#                 tweet.retweet_count,
#                 tweet.user.id,
#                 tweet.user.screen_name,
#                 tweet.user.name,
#                 tweet.user.description,
#                 tweet.user.friends_count,
#                 tweet.user.followers_count,
#                 create_account_time,
#                 tweet.user.following,
#                 tweet.user.profile_image_url,
#                 tweet.user.profile_background_image_url,
#                 tweet.user.url,
#             ]
#         )

#     # tw_dataのリストをpandasのDataFrameに変換して、CSVファイルを出力する
#     pandas.DataFrame(tw_data, columns=LABELS).to_csv(FILE_NAME, encoding="utf-8-sig", index=False)

"""
概　要：スプレッドシートから1回分のツイート情報を取得する
引　数：sheet:ツイート情報が記載されているシート
返り値：target_row: 対称行番号, message:メッセージ, image_pass:AWS S3バケットのイメージパス
"""


def get_tweet_info(sheet):
    max_row = len(list(filter(None, sheet.col_values(SheetIndex.MESSAGE.value))))
    target_row = (
        SheetIndex.START_ROW.value
        if TWITTER_ORDER == 1
        else random.randint(SheetIndex.START_ROW.value, max_row)
    )
    message = sheet.cell(target_row, SheetIndex.MESSAGE.value).value
    image_pass = sheet.cell(target_row, SheetIndex.IMAGE.value).value

    # 画像がある場合は作業用にダウンロードする
    if image_pass != None:
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(AWS_IMAGE_BUCKET)
        bucket.download_file("image/" + image_pass, TEMP_IMAGE_PASS)
        print("Tweet Image Get")

    return target_row, message, image_pass


"""
概　要：本処理
引　数：なし
返り値：なし
"""


def start(event, context):

    # スプレッドシート読み込み&Googleドライブ準備
    tweets_sheet, tweeted_sheet, search_word_sheet = init_google_tools()
    print("Google Tools Authorized")

    # スプレッドシートから1回分のツイート情報を取得
    target_row, message, image_pass = get_tweet_info(tweets_sheet)
    print("Tweet Info Get")

    # Twitter認証
    twitter_api = twitter_oauth()
    print("Twitter Authorized")

    # ランダム時間待機
    print("Random Sleep")
    time.sleep(random.randint(1, SLEEP_MAX_TIME_LIKE))

    if image_pass != None:
        # 画像付きツイート
        twitter_api.update_status_with_media(message, TEMP_IMAGE_PASS)
    else:
        # ツイートを投稿
        twitter_api.update_status(message)
    print("Twitter Update")

    # 1回限りのメッセージの場合、別シートに移動する
    if tweets_sheet.cell(target_row, SheetIndex.IMAGE.value).value == "Yes":
        add_row = len(list(filter(None, tweeted_sheet.col_values(SheetIndex.MESSAGE.value)))) + 1
        tweeted_sheet.update_cell(add_row, SheetIndex.MESSAGE.value, message)
        tweeted_sheet.update_cell(add_row, SheetIndex.IMAGE.value, image_pass)
        tweets_sheet.delete_row(target_row)

    # スプレッドシートの検索ワードを基にツイートを検索し、いいね&フォローする
    for target_row in range(
        SheetIndex.START_ROW.value,
        len(list(filter(None, search_word_sheet.col_values(SheetIndex.MESSAGE.value)))),
    ):
        search_tweets_and_method(
            twitter_api, search_word_sheet.cell(target_row, SheetIndex.SEARCH_WORD.value).value
        )

    print("COMPLETE !")

    return ""


def test():

    # スプレッドシート読み込み&Googleドライブ準備
    tweets_sheet, tweeted_sheet, search_word_sheet = init_google_tools()
    print("Google Tools Authorized")

    # スプレッドシートから1回分のツイート情報を取得
    target_row, message, image_pass = get_tweet_info(tweets_sheet)
    print("Tweet Info Get")

    # Twitter認証
    twitter_api = twitter_oauth()
    print("Twitter Authorized")

    # ランダム時間待機
    print("Random Sleep")
    time.sleep(random.randint(1, SLEEP_MAX_TIME_TWEET))

    if image_pass != None:
        # 画像付きツイート
        twitter_api.update_status_with_media(message, TEMP_IMAGE_PASS)
    else:
        # ツイートを投稿
        twitter_api.update_status(message)
    print("Twitter Update")

    # 1回限りのメッセージの場合、別シートに移動する
    if tweets_sheet.cell(target_row, SheetIndex.IMAGE.value).value == "Yes":
        add_row = len(list(filter(None, tweeted_sheet.col_values(SheetIndex.MESSAGE.value)))) + 1
        tweeted_sheet.update_cell(add_row, SheetIndex.MESSAGE.value, message)
        tweeted_sheet.update_cell(add_row, SheetIndex.IMAGE.value, image_pass)
        tweets_sheet.delete_row(target_row)

    # スプレッドシートの検索ワードを基にツイートを検索し、いいね&フォローする
    for target_row in range(
        SheetIndex.START_ROW.value,
        len(list(filter(None, search_word_sheet.col_values(SheetIndex.MESSAGE.value)))),
    ):
        search_tweets_and_method(
            twitter_api, search_word_sheet.cell(target_row, SheetIndex.SEARCH_WORD.value).value
        )

    print("COMPLETE !")
