# Fight Club [![Build Status](https://travis-ci.org/kzkn/fc.png)](https://travis-ci.org/kzkn/fc) #

Fight Club という福岡で活動するテニスサークルのホームページを制作するプロジェクトです。

## 動作環境 ##

python 2.7 で動作します。他のバージョンではおそらく動きません。動くようにしてもらうのは大歓迎です。

また、Linux 以外のプラットフォームにおける動作実績もありません。Windows や Mac な方々は、動作環境を構築するのに苦戦を強いられるかもしれません。ごめんなさい。

## 環境構築 ##

 1. [Python](http://www.python.org) をインストール
 2. [virtualenv](http://pypi.python.org/pypi/virtualenv) をインストール
 3. 以下、コマンドラインにて:

        $ git clone リポジトリ
        $ cd fc
        $ virtualenv .env
        $ . .env/bin/activate
        $ pip install -r requirements.txt
        $ python gensecret.py  # 1回やればOK
        $ python run.py

## コード書きたい方は ##

[本リポジトリ](https://github.com/kzkn/fc/) を fork して、そのリポジトリ上で あれこれ試すのがいいかと思います。開発が一段落したら、Pull-Request ください。メインラインにマージします。
