# twitter-bot

## twitter_bot.start

定期ランダムツイート

## ユーザー設定

user_settings.py の設定値を変更する。

## ターミナルからの実行

cd `dirname $0` # カレントディレクトリに移動
python -c "from twitter_bot import start; start()"

## ライブラリインストール

### ターミナル実行用

pip install gspread oauth2client -t .
pip install tweepy -t .
pip install pandas -t .
pip install pytz -t .

### AWS Lambda 定期実行用

pip install gspread oauth2client -t python/lib/python3.7/site-packages
pip install tweepy -t python/lib/python3.7/site-packages
pip install pandas -t python/lib/python3.7/site-packages
pip install pytz -t python/lib/python3.7/site-packages

## スプレッドシートを操作するための認証

client_secret.json を作成する
https://www.twilio.com/blog/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python-jp

## Twitter デベロッパーサイトで API 取得

https://developer.twitter.com/en/apps/

## Twitter API サードパーティアプリの承認

https://tools.tsukumijima.net/twittertoken-viewer/

##

| 検索キーワード                 | 説明                                            |
| ------------------------------ | ----------------------------------------------- |
| キーワード -除外するキーワード | -の後に続くキーワードを除外して検索             |
| キーワード min_faves:100       | いいねの数が 100 以上のツイートだけ             |
| キーワード min_retweets:100    | 100 リツイート以上のツイートを検索              |
| from:ユーザーネーム            | 特定のユーザーのツイートを検索                  |
| キーワード 1 OR キーワード 2   | ブログもしくはブロガーのキーワードを検索        |
| “キーワード”                   | ” “で囲われた文字列に完全一致するツイートを検索 |
