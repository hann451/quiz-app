from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from authlib.integrations.flask_client import OAuth
import sqlite3, os, csv, io, uuid, random, json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.pdfmetrics import stringWidth

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-secret")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

DB = os.path.join(os.path.dirname(__file__), "quiz.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            picture TEXT
        );
        CREATE TABLE IF NOT EXISTS csvfiles (
            id TEXT PRIMARY KEY,
            owner_email TEXT NOT NULL,
            title TEXT NOT NULL,
            is_public INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            number INTEGER,
            group_name TEXT,
            question TEXT,
            answer TEXT
        );
        CREATE TABLE IF NOT EXISTS saved_files (
            user_email TEXT,
            file_id TEXT,
            PRIMARY KEY (user_email, file_id)
        );
    """)
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

# ── ページ ──────────────────────────────────────────
@app.route("/")
def index():
    if "user" not in session:
        return render_template("login.html")
    return render_template("index.html", user=session["user"])

@app.route("/login")
def login():
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    u = token.get("userinfo")
    session["user"] = {"email": u["email"], "name": u.get("name",""), "picture": u.get("picture","")}
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users(email,name,picture) VALUES(?,?,?)",
                 (u["email"], u.get("name",""), u.get("picture","")))
    conn.commit(); conn.close()
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

# ── CSV アップロード ──────────────────────────────────
@app.route("/api/upload", methods=["POST"])
@login_required
def upload_csv():
    f = request.files.get("file")
    title = request.form.get("title", f.filename if f else "無題")
    is_public = 1 if request.form.get("is_public") == "1" else 0
    if not f:
        return jsonify({"error": "ファイルが必要です"}), 400

    content = f.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return jsonify({"error": "CSVが空です"}), 400

    file_id = str(uuid.uuid4())
    email = session["user"]["email"]
    conn = get_db()
    conn.execute("INSERT INTO csvfiles VALUES(?,?,?,?,?)",
                 (file_id, email, title, is_public, datetime.now().isoformat()))
    for row in rows:
        conn.execute("INSERT INTO questions(file_id,number,group_name,question,answer) VALUES(?,?,?,?,?)",
                     (file_id,
                      row.get("問題番号") or row.get("number") or 0,
                      row.get("グループ") or row.get("group") or "",
                      row.get("問題") or row.get("question") or "",
                      row.get("解答") or row.get("answer") or ""))
    conn.execute("INSERT OR IGNORE INTO saved_files VALUES(?,?)", (email, file_id))
    conn.commit(); conn.close()
    return jsonify({"id": file_id, "title": title})

# ── ファイル一覧 ──────────────────────────────────────
@app.route("/api/files")
@login_required
def get_files():
    email = session["user"]["email"]
    conn = get_db()
    rows = conn.execute("""
        SELECT c.id, c.title, c.owner_email, c.is_public, c.created_at
        FROM csvfiles c
        JOIN saved_files s ON c.id = s.file_id
        WHERE s.user_email = ?
    """, (email,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/files/public")
@login_required
def get_public_files():
    conn = get_db()
    rows = conn.execute(
        "SELECT id,title,owner_email,created_at FROM csvfiles WHERE is_public=1"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/files/<file_id>/save", methods=["POST"])
@login_required
def save_file(file_id):
    email = session["user"]["email"]
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO saved_files VALUES(?,?)", (email, file_id))
    conn.commit(); conn.close()
    return jsonify({"ok": True})

@app.route("/api/files/<file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    email = session["user"]["email"]
    conn = get_db()

    # オーナーかどうか確認
    owner = conn.execute(
        "SELECT owner_email FROM csvfiles WHERE id=?", (file_id,)
    ).fetchone()

    if owner and owner["owner_email"] == email:
        # オーナーなら本体ごと削除（全員のsaved_filesからも消える）
        conn.execute("DELETE FROM questions WHERE file_id=?", (file_id,))
        conn.execute("DELETE FROM saved_files WHERE file_id=?", (file_id,))
        conn.execute("DELETE FROM csvfiles WHERE id=?", (file_id,))
    else:
        # 他人のファイルは自分のsaved_filesから外すだけ
        conn.execute(
            "DELETE FROM saved_files WHERE user_email=? AND file_id=?", (email, file_id)
        )

    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ── 問題取得・グループ一覧 ────────────────────────────
@app.route("/api/files/<file_id>/groups")
@login_required
def get_groups(file_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT group_name FROM questions WHERE file_id=? ORDER BY group_name",
        (file_id,)).fetchall()
    conn.close()
    return jsonify([r["group_name"] for r in rows])

@app.route("/api/quiz", methods=["POST"])
@login_required
def get_quiz():
    body = request.get_json()
    file_id = body.get("file_id")
    groups = body.get("groups", [])       # [] = 全グループ
    num_from = body.get("num_from")
    num_to = body.get("num_to")
    count = body.get("count")             # None = 全問

    conn = get_db()
    query = "SELECT * FROM questions WHERE file_id=?"
    params = [file_id]
    if groups:
        placeholders = ",".join("?" * len(groups))
        query += f" AND group_name IN ({placeholders})"
        params += groups
    if num_from:
        query += " AND number >= ?"
        params.append(int(num_from))
    if num_to:
        query += " AND number <= ?"
        params.append(int(num_to))

    rows = conn.execute(query, params).fetchall()
    conn.close()

    questions = [dict(r) for r in rows]
    random.shuffle(questions)
    if count:
        questions = questions[:int(count)]
    return jsonify(questions)

# ── PDF生成 ───────────────────────────────────────────
def wrap_text(text, font_name, font_size, max_width):
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if stringWidth(test, font_name, font_size) > max_width:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def build_pdf(questions, mode, font_size, text_color):
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    color = HexColor(text_color) if text_color.startswith("#") else HexColor("#000000")
    c.setFillColor(color)
    c.setFont("HeiseiKakuGo-W5", font_size)

    margin = 40
    max_width = W - margin * 2  # 約515pt
    line_height = font_size * 1.8
    y = H - 50

    for i, q in enumerate(questions, 1):
        text = f"Q{i}. {q['question']}" if mode == "question" else f"Q{i}. {q['answer']}"

        lines = wrap_text(text, "HeiseiKakuGo-W5", font_size, max_width)

        for line in lines:
            if y < 50:
                c.showPage()
                c.setFillColor(color)
                c.setFont("HeiseiKakuGo-W5", font_size)
                y = H - 50
            c.drawString(margin, y, line)
            y -= line_height

        y -= line_height * 0.3

    c.save()
    buf.seek(0)
    return buf

@app.route("/api/pdf", methods=["POST"])
@login_required
def generate_pdf():
    body = request.get_json()
    questions = body.get("questions", [])
    mode = body.get("mode", "question")       # "question" or "answer"
    font_size = float(body.get("font_size", 10.5))
    text_color = body.get("text_color", "#000000")

    buf = build_pdf(questions, mode, font_size, text_color)
    filename = "questions.pdf" if mode == "question" else "answers.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")