import os
import json
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request

# --- 1. Firebase 初始化 ---
# 優先順序：環境變數 > 實體檔案
firebase_config = os.getenv('FIREBASE_CONFIG')

if firebase_config:
    try:
        # 處理可能的換行符號問題
        cred_dict = json.loads(firebase_config, strict=False)
        cred = credentials.Certificate(cred_dict)
    except Exception as e:
        print(f"環境變數解析失敗: {e}")
        cred = None
elif os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    cred = None

if cred and not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

# --- 2. 路由設定 ---

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now_str = datetime.now().strftime("%Y年%m月%d日")
    return render_template("today.html", datetime=now_str)

@app.route("/about")
def about():
    return render_template("mis2a.html")

# --- 3. 爬蟲功能 ---

@app.route("/spider1")
def spider1():
    url = "https://2026-rust.vercel.app/"
    try:
        data = requests.get(url, verify=False, timeout=10)
        data.encoding = "utf-8"
        sp = BeautifulSoup(data.text, "html.parser")
        title = sp.select_one("h1") 
        paragraphs = sp.select("p")
        
        res = "<h1>爬蟲測試結果</h1>"
        if title: res += f"<h3>網頁主標題是：{title.text}</h3>"
        for p in paragraphs:
            res += f"· {p.text}<br>"
        return res
    except Exception as e:
        return f"爬蟲發生錯誤：{e}"

@app.route("/movie1")
def movie1():
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(url, headers=headers, timeout=15)
        data.encoding = "utf-8"
        sp = BeautifulSoup(data.text, "html.parser")
        movies = sp.select(".filmListAllX li")
        
        res = "<h2>🎬 即將上映電影</h2><hr>"
        for m in movies:
            a = m.select_one(".filmtitle a")
            if a:
                name = a.text.strip()
                link = "https://www.atmovies.com.tw" + a.get("href")
                res += f"<b>電影名稱：</b>{name}<br>"
                res += f"<b>電影連結：</b><a href='{link}' target='_blank'>點我查看</a><br><br>"
        return res
    except Exception as e:
        return f"連線發生錯誤：{e}"

# --- 4. Firebase 資料功能 ---

@app.route("/read")
def read():
    try:
        db = firestore.client()
        res = "<h3>資料讀取結果：</h3>"
        # 請確認集合名稱正確
        docs = db.collection("靜宜資管2026a").order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
        for doc in docs:
            res += str(doc.to_dict()) + "<br>"
        return res
    except Exception as e:
        return f"Firebase 讀取失敗：{e}"

@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    keyword = ""
    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        docs = db.collection("靜宜資管2026a").get()
        for doc in docs:
            user = doc.to_dict()
            if keyword in user.get("name", ""):
                results.append({"name": user["name"], "lab": user["lab"]})
    return render_template("search.html", results=results, keyword=keyword)

# --- 5. 互動功能 ---

@app.route("/welcome", methods=["GET"])
def welcome():
    u = request.values.get("u")
    dep = request.values.get("dep")
    return render_template("welcome.html", name=u, dep=dep)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("pwd")
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}"
    return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x, y = int(request.form["x"]), int(request.form["y"])
            opt = request.form["opt"]
            if opt == "/" and y == 0: return "除數不能為0"
            r = {"+": x+y, "-": x-y, "*": x*y, "/": x/y}.get(opt, "未知運算")
            return f"您輸入的是：{x}{opt}{y}={r}<br><a href=/>返回首頁</a>"
        except:
            return "輸入錯誤，請輸入數字。"
    return render_template("math.html")

@app.route('/cup', methods=["GET"])
def cup():
    action = request.values.get("action")
    result = None
    if action == 'toss':
        x1, x2 = random.randint(0, 1), random.randint(0, 1)
        msg = "聖筊" if x1 != x2 else ("笑筊" if x1 == 0 else "陰筊")
        result = {"cup1": f"/static/{x1}.jpg", "cup2": f"/static/{x2}.jpg", "message": msg}
    return render_template('cup.html', result=result)

@app.route("/math2", methods=["GET", "POST"])
def math2():
    result = None
    if request.method == "POST":
        try:
            x, y = float(request.form.get("x")), float(request.form.get("y"))
            opt = request.form.get("opt")
            if opt == "∧": result = x ** y
            elif opt == "√": result = x ** (1/y) if y != 0 else "錯誤"
        except:
            result = "計算錯誤"
    return render_template("math2.html", result=result)

if __name__ == "__main__":
    app.run()
