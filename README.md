# このプロジェクトは？ #

Fight Club という福岡で活動するテニスサークルのホームページを
制作するプロジェクトです。

# 動作環境 #

python 2.6 系、または 2.7 系での動作確認は取れています。他の
バージョンではおそらく動きません。動くようにしてもらうのは大
歓迎です。

## 環境構築 ##

 1. [Python](http://www.python.org) をインストール
 2. [pip](http://pypi.python.org/pypi/pip) をインストール
 3. [virtualenv](http://pypi.python.org/pypi/virtualenv) をインストール
 4. 以下、コマンドラインにて:

        $ git clone リポジトリ fc
        $ virtualenv env
        $ . env/bin/activate
        $ pip install -r fc/libs.txt
        $ cd fc
        $ python run.py
