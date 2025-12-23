from flask import Flask, request, redirect, session
import json, os, time

app = Flask(__name__)
app.secret_key = "mini-x-secret"

DATA_FILE = "posts.json"

def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

posts = load_posts()

@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        text = request.form["text"]
        if text.strip():
            posts.insert(0, {
                "id": str(time.time()),
                "user": session["user"],
                "text": text,
                "likes": 0,
                "comments": []
            })
            save_posts(posts)
        return redirect("/")

    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Mini X - 초간단 SNS</title>
<meta name="description" content="닉네임만 입력하면 바로 사용하는 초간단 SNS Mini X">
<meta name="keywords" content="Mini X, SNS, 트위터, 미니 트위터, Flask SNS">
<meta name="robots" content="index, follow">
<style>
body {font-family: Arial;background:#000;color:#fff;margin:0}
.header {padding:15px;font-size:22px;font-weight:bold;border-bottom:1px solid #333}
.container {max-width:600px;margin:auto;padding:10px}
.post {border-bottom:1px solid #333;padding:10px}
.user {font-weight:bold}
button {background:#1d9bf0;color:white;border:none;padding:5px 10px;border-radius:20px;cursor:pointer}
.like {background:none;color:#1d9bf0}
.delete {background:none;color:red}
.comment {background:none;color:#aaa}
input {width:100%;padding:10px;border-radius:20px;border:none;margin-bottom:6px}
.comment-box {margin-left:15px;margin-top:5px;color:#ccc}
</style>
</head>
<body>
<div class="header">Mini X</div>
<div class="container">
    <a href="/grok" style="color:white;display:block;padding:8px 0;">🤖 Grok</a>

<form method="post">
<input name="text" maxlength="280" placeholder="무슨 일이 일어나고 있나요?" required>
<button>게시</button>
</form>
<hr>
"""
    for p in posts:
        html += f"""
<div class="post">
<div class="user">{p['user']}</div>
<div>{p['text']}</div>

<form action="/like/{p['id']}" method="post" style="display:inline">
<button class="like">❤️ {p['likes']}</button>
</form>

<form action="/comment/{p['id']}" method="post" style="display:inline">
<input name="comment" placeholder="댓글 쓰기" required>
<button class="comment">💬</button>
</form>
"""
        if p["user"] == session["user"]:
            html += f"""
<form action="/delete/{p['id']}" method="post" style="display:inline">
<button class="delete">🗑️</button>
</form>
"""
        for c in p["comments"]:
            html += f"""
<div class="comment-box">
<b>{c['user']}</b>: {c['text']}
</div>
"""
        html += "</div>"

    html += "</div></body></html>"
    return html

@app.route("/like/<pid>", methods=["POST"])
def like(pid):
    for p in posts:
        if p["id"] == pid:
            p["likes"] += 1
            break
    save_posts(posts)
    return redirect("/")

@app.route("/comment/<pid>", methods=["POST"])
def comment(pid):
    text = request.form["comment"]
    for p in posts:
        if p["id"] == pid:
            p["comments"].append({"user": session["user"], "text": text})
            break
    save_posts(posts)
    return redirect("/")

@app.route("/delete/<pid>", methods=["POST"])
def delete(pid):
    global posts
    posts = [p for p in posts if p["id"] != pid]
    save_posts(posts)
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["name"]
        return redirect("/")
    return '''
    <h2>Mini X 로그인</h2>
    <form method="post">
        <input name="name" placeholder="닉네임" required>
        <button>입장</button>
    </form>
    '''

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/grok", methods=["GET", "POST"])
def grok():
    answer = ""
    if request.method == "POST":
        q = request.form["q"]
        answer = f"🤖 Grok: '{q}'에 대해 생각해보면… 꽤 흥미로운 질문이네."
    return f"""
    <h2>🤖 Grok</h2>
    <form method="post">
        <input name="q" placeholder="Grok에게 물어보세요" required>
        <button>질문</button>
    </form>
    <p>{answer}</p>
    <a href="/">← 홈</a>
    """

@app.route("/health")
def health():
    return "OK", 200

# ---- 검색엔진용 추가 ----
@app.route("/robots.txt")
def robots():
    return """User-agent: *
Allow: /
""", 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap():
    urls = ["/", "/login", "/grok"]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url>\n    <loc>https://mini-x-0rn4.onrender.com{u}</loc>\n  </url>\n"
    xml += '</urlset>'
    return xml, 200, {"Content-Type": "application/xml"}

