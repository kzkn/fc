# このプロジェクトは？ #

Fight Club という福岡で活動するテニスサークルのホームページを
制作するプロジェクトです。

# 動作環境 #

python 2.6 系、または 2.7 系での動作確認は取れています。他の
バージョンではおそらく動きません。動くようにしてもらうのは大
歓迎です。

また、Linux 以外のプラットフォームにおける動作実績もありませ
ん。Windows や Mac な方々は、動作環境を構築するのに苦戦を強い
られるかもしれません。ごめんなさい。

## 環境構築 ##

 1. [Python](http://www.python.org) をインストール
 2. [virtualenv](http://pypi.python.org/pypi/virtualenv) をインストール
 3. 以下、コマンドラインにて:

        $ git clone リポジトリ fc
        $ virtualenv env
        $ . env/bin/activate
        $ pip install -r fc/libs.txt
        $ cd fc
        $ python gensecret.py  # 1回やればOK
        $ python run.py

## コード書きたい方は ##

[本リポジトリ](https://github.com/kzkn/fc/) を fork して、その
リポジトリ上で あれこれ試すのがいいかと思います。開発が一段落したら、
Pull-Request ください。メインラインにマージします。
