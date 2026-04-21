import requests
from bs4 import BeautifulSoup
import os
import json
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request

# --- 1. Firebase 初始化 ---
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = None # 或者處理沒有配置的情況

if cred and not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

# --- 2. 首頁與基本路由 ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    now_str = now.strftime("%Y年%m月%d日")
    return render_template("today.html", datetime=now_str)

@app.route("/about")
def about():
    return render_template("mis2a.html")

# --- 3. 爬蟲功能 (spider1 & movie1) ---
@app.route("/spider1")
def spider1():
    url = "https://2026-rust.vercel.app/"
    try:
        Data = requests.get(url, verify=False, timeout=10)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        title = sp.select_one("h1") 
        paragraphs = sp.select("p")
        
        R = "<h1>爬蟲測試結果</h1>"
        if title: R += f"<h3>網頁主標題是：{title.text}</h3>"
        for p in paragraphs:
            R += f"· {p.text}<br>"
        return R
    except Exception as e:
        return f"爬蟲發生錯誤：{e}"

@app.route("/movie1")
def movie1():
    import requests
    from bs4 import BeautifulSoup
    
    url = "https://www.atmovies.com.tw/movie/next/"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        Data = requests.get(url, headers=headers, timeout=15)
        Data.encoding = "utf-8"
        
        sp = BeautifulSoup(Data.text, "html.parser")
        
        # ⭐ 正確 selector（對應你貼的HTML）
        movies = sp.select(".filmListAllX li")
        
        R = "<h2>🎬 即將上映電影</h2><hr>"
        
        for m in movies:
            a = m.select_one(".filmtitle a")
            
            if a:
                name = a.text.strip()
                link = "https://www.atmovies.com.tw" + a.get("href")
                
                R += f"<b>電影名稱：</b>{name}<br>"
                R += f"<b>電影連結：</b><a href='{link}' target='_blank'>點我查看</a><br><br>"
        
        return R

    except Exception as e:
        return f"發生錯誤：{e}"
            

    except Exception as e:
        return f"連線發生錯誤：{e}"
# --- 4. Firebase 資料讀取與查詢 ---
@app.route("/read")
def read():
    db = firestore.client()
    Temp = "<h3>資料讀取結果：</h3>"
    collection_ref = db.collection("靜宜資管2026a")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"
    return Temp

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    keyword = ""
    if request.method == "POST":
        keyword = request.form.get("keyword")
        docs = db.collection("靜宜資管2026a").get()
        for doc in docs:
            user = doc.to_dict()
            if keyword in user.get("name", ""):
                results.append({"name": user["name"], "lab": user["lab"]})
    return render_template("search.html", results=results, keyword=keyword)

# --- 5. 互動功能 (welcome, account, math, cup) ---
@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name=x, dep=y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}"
    return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x, y = int(request.form["x"]), int(request.form["y"])
        opt = request.form["opt"]
        if opt == "/" and y == 0: return "除數不能為0"
        r = {"+": x+y, "-": x-y, "*": x*y, "/": x/y}.get(opt, "未知運算")
        return f"您輸入的是：{x}{opt}{y}={r}<br><a href=/>返回首頁</a>"
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
        x, y = int(request.form.get("x")), int(request.form.get("y"))
        opt = request.form.get("opt")
        if opt == "∧": result = x ** y
        elif opt == "√": result = x ** (1/y) if y != 0 else "數學上不存在0次方根"
    return render_template("math2.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)