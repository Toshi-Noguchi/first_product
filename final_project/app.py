import os
from flask import Flask, render_template, redirect, request, g, session, url_for
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from functools import wraps

#アプリの作成
app = Flask(__name__, static_folder='./images')
app.config['SECRET_KEY'] = os.urandom(24)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)




#データベース操作の準備
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("diary.db")
        g.db.row_factory = sqlite3.Row

    return g.db

#ログインの確認
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        else:
            return func(*args, **kwargs)
        
    return wrapper

#ホーム
@app.route("/")
@login_required
def home():
        username = session["username"]
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM diaries WHERE username = ?", (username,))
        diaries = cur.fetchall()
        con.close()

        return render_template("home.html", diaries=diaries, username=username)

#投稿
@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    errors ={}

    if request.method == "POST":
        #フォームからデータ回収
        date = request.form.get("date")
        study_time = request.form.get("studytime")
        review = request.form.get("review")
        can = request.form.get("can")
        will = request.form.get("will")


        #バリデーション
        if not date:
            errors["field"] = "date"
            errors["message"] = "日付を入力してください"
        elif not study_time:
            errors["field"] = "studytime"
            errors["message"] = "学習時間を入力してください"
        elif not review:
            errors["field"] = "review"
            errors["message"] = "本日の振り返りを入力してください"
        elif not can:
            errors["field"] = "can"
            errors["message"] = "できるようになったことを入力してください"
        elif not will:
            errors["field"] = "will"
            errors["message"] = "明日達成することを入力してください"
        else:
            username = session["username"]
            #データベースに登録
            con = get_db()
            cur = con.cursor()
            cur.execute('INSERT INTO diaries(username, date, studytime, review, can, will) VALUES(?, ?, ?, ?, ?, ?)', (username, date, study_time, review, can, will))
            con.commit()
            con.close()
            return redirect("/")
        
        return render_template("post.html", errors=errors, error_message="入力内容に誤りがあります", username=session["username"])

    else:
        return render_template("post.html", username=session["username"])

#ログイン
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        errors = {}

        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            errors["field"] = "username"
            errors["error_message"] = "ユーザーネームを入力してください"
            return render_template("login.html", errors=errors, error_message="入力内容に誤りがあります")
        elif not password:
            errors["field"] = "password"
            errors["error_message"] = "パスワードを入力してください"
            return render_template("login.html", errors=errors, error_message="入力内容に誤りがあります")

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        rows =  cur.fetchall()
        con.close()

        if len(rows) == 0:
            errors["field"] = "username"
            errors["message"] = "ユーザーネームが見つかりません"
        elif not check_password_hash(rows[0]["hash"], password):
            errors["field"] = password
            errors["message"] = "パスワードが間違っています"
        else:
            session["username"] = username
            return redirect("/")
        
        return render_template("login.html", errors=errors, error_message="入力内容に誤りがあります")

    else:
        return render_template("login.html")

#サインアップ
@app.route("/register", methods=["GET", "POST"])
def register():
    errors ={}
    #セッションのクリア
    session.clear()

    if request.method == "POST":
        username = request.form.get('username')
        password =request.form.get("password")
        confirmation = request.form.get("confirmation")

        con = get_db()
        cur = con.cursor()
        cur.execute('SELECT * FROM diaries WHERE username = ?', (username,))
        rows = cur.fetchall()

        if not username:
            errors["field"] = "username"
            errors["error_message"] = "ユーザーネームを入力してください"
        elif not password:
            errors["field"] = "password"
            errors["error_message"] = "パスワードを入力してください"
        elif not confirmation:
            errors["field"] = "confirmation"
            errors["error_message"] = "再度、パスワードを入力してください"
        elif len(rows) != 0:
            errors["field"] = "username"
            errors["error_message"] = "そのユーザーネームは使用できません"
        elif password != confirmation:
            errors["field"] = "confirmation"
            errors["error_message"] = "パスワードが一致しません"
        else:
            hash=generate_password_hash(password)
            cur.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hash))
            con.commit()
            con.close()
            session["username"] = username

            return redirect("/")

        return render_template("register.html", errors=errors, error_message="入力内容に誤りがあります")

    else:
        return render_template("register.html")

#ログアウト
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#マイページ
@app.route("/mypage", methods=["GET", "POST"])
def mypage():
    if request.method == "POST":
        username = request.form.get("username")
        target = request.form.get("target")
        tr_study = request.form.get("trstudy")

        con = get_db()
        cur = con.cursor()
        cur.execute("UPDATE users SET username = ?, target = ?, trStudy = ? WHERE username = ?", (username, target, tr_study, session["username"]))
        con.commit()
        con.close()
        session["username"] = username

        return redirect("/mypage")

    else:
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (session["username"],))
        rows = cur.fetchall()
        target = rows[0]["target"]
        tar_study = rows[0]["trStudy"]

        cur.execute("SELECT SUM(studytime) FROM diaries WHERE username = ?", (session["username"],))
        rows2 = cur.fetchall()
        sum_study = rows2[0]["SUM(studytime)"]

        return render_template("mypage.html", username=session["username"], target=target, tar_study=tar_study, sum_study=sum_study)

if __name__ == "__main__":
    app.run()



