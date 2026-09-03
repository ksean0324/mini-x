from flask import Flask, request, redirect, session, url_for, send_from_directory
import os
import time
import json
import re
import ast
import html
import operator
from datetime import datetime
import werkzeug.utils  # 파일 업로드 안전 처리용

app = Flask(__name__)
app.secret_key = "mini-x-secret"

DATA_FILE = "posts.json"


import re

bad_words = [
    "씨발", "시발", "ㅅㅂ", "ㅆㅂ", "시바", "씨바",
    "병신", "ㅂㅅ",
    "미친", "ㅈㄴ", "존나",
    "개새끼", "개세끼", "ㄱㅅㄲ",
    "좆", "ㅈㄹ", "지랄",
    "tlqkf", "ㅌㄹㅋㅍ"
]

def has_bad_word(text):
    cleaned = text.lower()
    cleaned = re.sub(r'[^가-힣ㄱ-ㅎㅏ-ㅣa-z0-9]', '', cleaned)

    chosung_map = {
        "ㅅㅂ": "시발",
        "ㅆㅂ": "씨발",
        "ㅂㅅ": "병신",
        "ㄱㅅㄲ": "개새끼",
        "ㅈㄴ": "존나",
        "ㅈㄹ": "지랄",
        "ㅌㄹㅋㅍ": "틀딱"
    }

    for c in chosung_map:
        if c in cleaned:
            return True

    for word in bad_words:
        if word in cleaned:
            return True

    return False



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
        text = request.form.get("text", "")
        file = request.files.get("file")  # 업로드 파일

        # 🔥 욕설 검사
        if has_bad_word(text):
            return """
            <script>
            alert("욕설은 사용할 수 없습니다.");
            history.back();
            </script>
            """

        filename = ""
        if file and file.filename:
            filename = f"{int(time.time())}_{werkzeug.utils.secure_filename(file.filename)}"
            file_path = os.path.join("static", "uploads", filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

        if text.strip() or filename:
            posts.insert(0, {
                "id": str(time.time()),
                "user": session["user"],
                "text": text,
                "image": filename,  # 이미지 파일명 저장
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
img {max-width:100%;margin-top:5px;border-radius:10px}
</style>
</head>
<body>
<div class="header">Mini X</div>
<div class="container">
<a href="/grok" style="color:white;display:block;padding:8px 0;">🤖 Grok</a>

<form method="post" enctype="multipart/form-data">
<input name="text" maxlength="280" placeholder="무슨 일이 일어나고 있나요?">
<input type="file" name="file" accept="image/*">
<button>게시</button>
</form>
<hr>
"""

    for p in posts:
        html += f"""
<div class="post">
<div class="user">{p['user']}</div>
<div>{p['text']}</div>
"""
        if p.get("image"):
            html += f'<img src="/static/uploads/{p["image"]}">'

        html += f"""
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["name"]
        return redirect("/")
    return """
    <h2>Mini X 로그인</h2>
    <form method="post">
        <input name="name" placeholder="닉네임" required>
        <button>입장</button>
    </form>
    """


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

CALC_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    """숫자와 기본 연산자만 허용하는 안전한 계산기."""
    if len(expression) > 80:
        raise ValueError("계산식이 너무 길어요")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in CALC_OPERATORS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("지수가 너무 커요")
            result = CALC_OPERATORS[type(node.op)](left, right)
            if abs(result) > 1_000_000_000_000:
                raise ValueError("결과가 너무 커요")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in CALC_OPERATORS:
            return CALC_OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("지원하지 않는 계산식이에요")

    return evaluate(ast.parse(expression, mode="eval"))


def grok_answer(question):
    q = question.strip()
    q_lower = q.lower()
    now = datetime.now()

    # '계산해줘 12*(3+4)'처럼 말해도 계산식을 찾아낸다.
    expression = re.sub(r"(계산해줘|계산해|계산|얼마야|은|는|이|가|\?|=)", "", q_lower).strip()
    if expression and re.fullmatch(r"[\d\s.()+\-*/%]+", expression):
        try:
            result = safe_calculate(expression)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"계산 결과는 {result}입니다."
        except ZeroDivisionError:
            return "0으로 나눌 수는 없어요. 다른 계산식을 입력해 주세요."
        except (ValueError, SyntaxError):
            return "계산식을 이해하지 못했어요. 예: (12 + 3) * 4"

    if any(word in q_lower for word in ("안녕", "반가워", "hello", "hi")):
        user = session.get("user", "친구")
        return f"안녕하세요, {user}님! 질문이나 계산, Mini X 사용법을 물어보세요."
    if "몇 시" in q_lower or "몇시" in q_lower or "현재 시간" in q_lower:
        return f"지금은 {now.strftime('%Y년 %m월 %d일 %H시 %M분')}입니다."
    if any(word in q_lower for word in ("오늘 날짜", "무슨 요일", "며칠")):
        weekdays = "월화수목금토일"
        return f"오늘은 {now.strftime('%Y년 %m월 %d일')} {weekdays[now.weekday()]}요일입니다."
    if "날씨" in q_lower:
        return "실시간 날씨 정보에는 아직 연결되어 있지 않아요. 지역을 알려줘도 지금은 정확한 날씨를 확인할 수 없습니다."
    if "누구" in q_lower and ("너" in q_lower or "grok" in q_lower):
        return "저는 Mini X 안에서 계산과 간단한 질문에 답하는 Grok 도우미예요."
    if any(word in q_lower for word in ("사용법", "뭘 할 수", "기능", "도움말")):
        return "계산, 날짜와 시간 확인, Mini X 사용법 안내를 할 수 있어요. 홈에서는 글과 사진을 올리고 좋아요와 댓글도 남길 수 있습니다."
    if "게시" in q_lower or "글 올" in q_lower:
        return "홈 화면 입력칸에 내용을 쓰고 ‘게시’를 누르세요. 사진도 함께 선택할 수 있어요."
    if "댓글" in q_lower:
        return "게시물 아래 댓글 입력칸에 내용을 작성한 뒤 말풍선 버튼을 누르면 됩니다."
    if "좋아요" in q_lower:
        return "게시물 아래 하트 버튼을 누르면 좋아요가 추가됩니다."
    if any(word in q_lower for word in ("고마워", "감사")):
        return "천만에요! 또 궁금한 게 있으면 물어보세요."

    # 키워드를 바탕으로 완전히 무관한 고정 답변 대신 다음 질문을 안내한다.
    keywords = [word for word in re.findall(r"[가-힣a-zA-Z0-9]+", q) if len(word) > 1]
    topic = keywords[0] if keywords else "그 내용"
    return f"‘{topic}’에 관한 질문은 아직 정확히 답하기 어려워요. 계산식, 날짜·시간 또는 Mini X 사용법처럼 조금 더 구체적으로 물어봐 주세요."


@app.route("/grok", methods=["GET", "POST"])
def grok():
    answer = ""
    question = ""
    if request.method == "POST":
        question = request.form.get("q", "")[:500]
        answer = grok_answer(question)

    return f"""
    <meta charset="UTF-8">
    <h2>🤖 Grok</h2>
    <form method="post">
        <input name="q" maxlength="500" value="{html.escape(question)}" placeholder="계산, 날짜, Mini X 사용법을 물어보세요" required>
        <button>질문</button>
    </form>
    <p>{html.escape(answer)}</p>
    <a href="/">← 홈</a>
    """

@app.route("/health")
def health():
    return "OK", 200

# ---- 검색엔진용 추가 ----
@app.route("/robots.txt")
def robots():
    return """User-agent: *
Allow: /""", 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap():
    urls = ["/", "/login", "/grok"]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url>\n    <loc>https://mini-x-0rn4.onrender.com{u}</loc>\n  </url>\n"
    xml += '</urlset>'
    return xml, 200, {"Content-Type": "application/xml"}

@app.route("/delete/<pid>", methods=["POST"])
def delete_post(pid):
    global posts
    for i, p in enumerate(posts):
        if p["id"] == pid and p["user"] == session.get("user"):
            # 이미지 파일 있으면 삭제
            if p.get("image"):
                try:
                    os.remove(os.path.join("static", "uploads", p["image"]))
                except FileNotFoundError:
                    pass
            # 게시물 삭제
            posts.pop(i)
            save_posts(posts)
            break
    return redirect("/")

# ---- 알림 기능 ----
notifications = {}  # { "username": ["알림1", "알림2", ...] }

def add_notification(user, text):
    if user not in notifications:
        notifications[user] = []
    notifications[user].insert(0, text)  # 최신 순으로 추가

@app.route("/notifications")
def show_notifications():
    if "user" not in session:
        return redirect("/login")
    user = session["user"]
    user_notifications = notifications.get(user, [])
    html = "<h2>🔔 알림</h2><ul>"
    for n in user_notifications:
        html += f"<li>{n}</li>"
    html += "</ul><a href='/'>← 홈</a>"
    # 확인 후 알림 제거
    notifications[user] = []
    return html

# 기존 like와 comment 처리 시 알림 추가
@app.route("/like/<pid>", methods=["POST"])
def like(pid):
    for p in posts:
        if p["id"] == pid:
            p["likes"] += 1
            if p["user"] != session["user"]:
                add_notification(p["user"], f"{session['user']}님이 당신의 글을 좋아합니다 ❤️")
            break
    save_posts(posts)
    return redirect("/")

@app.route("/comment/<pid>", methods=["POST"])
def comment(pid):
    text = request.form["comment"]

    # 🔥 댓글 욕설 검사
    if has_bad_word(text):
        return """
        <script>
        alert("욕설이 포함된 댓글은 작성할 수 없습니다.");
        history.back();
        </script>
        """

    for p in posts:
        if p["id"] == pid:
            p["comments"].append({
                "user": session["user"],
                "text": text
            })

            if p["user"] != session["user"]:
                add_notification(
                    p["user"],
                    f"{session['user']}님이 당신의 글에 댓글을 남겼습니다: {text}"
                )
            break

    save_posts(posts)
    return redirect("/")






@app.route("/status/<int:code>")
def status_test(code):
    messages = {
        200: "✅ 200 OK - 정상 처리됨",
        202: "🕒 202 Accepted - 접수만 됨",
        400: "❌ 400 Bad Request - 잘못된 요청",
        401: "🔐 401 Unauthorized - 인증 필요",
        403: "🚫 403 Forbidden - 접근 금지",
        404: "❓ 404 Not Found - 없음",
        418: "☕ 418 I'm a teapot - 서버 삐짐",
        500: "💥 500 Internal Server Error - 서버 터짐",
        503: "🛠️ 503 Service Unavailable - 점검 중"
    }

    msg = messages.get(code, "🤔 알 수 없는 상태코드 실험")
    return msg, code


