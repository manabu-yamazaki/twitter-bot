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

### AWS Lambda 定期実行用

pip install gspread oauth2client -t python/lib/python3.7/site-packages
