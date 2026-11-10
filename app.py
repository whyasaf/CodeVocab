import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from collections import OrderedDict, deque
from functools import wraps

from dotenv import load_dotenv
from urllib.parse import urlencode, urlparse

from flask import Flask, Response, jsonify, make_response, redirect, render_template, request

load_dotenv()

from ai import AIUnavailable, active_providers, complete_json  # noqa: E402
from prompts import (  # noqa: E402
    ANALYZER_SYSTEM_PROMPT,
    TOPIC_QUIZ_USER_TEMPLATE,
    TOPIC_SYSTEM_PROMPT,
    TOPIC_USER_TEMPLATE,
    WORD_SYSTEM_PROMPT,
    WORD_USER_TEMPLATE,
)

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "vocab.db")

MAX_TEXT_LEN = 500
MAX_HISTORY = 8          # sohbette modele gönderilen önceki mesaj sayısı
MAX_KNOWN_WORDS = 3000
SKIP_MOST_COMMON = 150   # "the", "would" gibi en temel kelimeleri havuzdan çıkar
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'\- ]{0,39}$")
MAX_TOPIC_LEN = 80
SITE_URL = os.getenv("SITE_URL", "https://codevocab.whyasaf.com").rstrip("/")

# Kötüye kullanıma karşı IP başına AI isteği sınırı (pencere saniyesi, izin verilen istek)
RATE_LIMITS = ((60, 15), (3600, 200))


# ───────────── Statik dosya sürümleme ─────────────
# url_for('static', ...) adreslerine dosya içeriğinin kısa özetini ekler (?v=ab12cd34).
# Dosya değişince adres de değişir; tarayıcı eski CSS/JS'i asla kullanmaz.
_hash_cache = {}


def _static_hash(filename):
    path = os.path.join(app.static_folder, filename)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    cached = _hash_cache.get(filename)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, "rb") as f:
        digest = hashlib.md5(f.read()).hexdigest()[:8]
    _hash_cache[filename] = (mtime, digest)
    return digest


@app.url_defaults
def _version_static(endpoint, values):
    if endpoint == "static" and "filename" in values and "v" not in values:
        digest = _static_hash(values["filename"])
        if digest:
            values["v"] = digest


@app.after_request
def _cache_headers(resp):
    # Sürümlü statik dosyalar bir yıl önbellekte kalabilir; adres değişince yenisi iner.
    if request.path.startswith("/static/") and request.args.get("v") and resp.status_code == 200:
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


@app.context_processor
def _site_context():
    return {"site_url": SITE_URL}


# ───────────── İstek sınırı ─────────────
_hits = {}
_hits_lock = threading.Lock()


def _client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return (fwd.split(",")[0].strip() or request.headers.get("X-Real-IP") or request.remote_addr or "?")


def rate_limited(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        now = time.time()
        longest = max(w for w, _ in RATE_LIMITS)
        with _hits_lock:
            if len(_hits) > 5000:  # bellek koruması: eski kayıtları at
                for k in [k for k, q in _hits.items() if not q or now - q[-1] > longest]:
                    del _hits[k]
            q = _hits.setdefault(_client_ip(), deque())
            while q and now - q[0] > longest:
                q.popleft()
            for window, limit in RATE_LIMITS:
                if sum(1 for t in q if now - t <= window) >= limit:
                    msg = (
                        "Biraz hızlı gidiyorsun. Bir dakika bekleyip tekrar dene."
                        if window <= 60
                        else "Bu saatlik istek sınırına ulaştın. Biraz ara verip sonra devam edebilirsin."
                    )
                    resp = jsonify({"error": msg})
                    resp.status_code = 429
                    resp.headers["Retry-After"] = str(window if window > 60 else 60)
                    return resp
            q.append(now)
        return view(*args, **kwargs)

    return wrapper


class LRUCache(OrderedDict):
    def __init__(self, maxsize=500):
        super().__init__()
        self.maxsize = maxsize

    def get(self, key):
        if key in self:
            self.move_to_end(key)
            return self[key]
        return None

    def put(self, key, value):
        self[key] = value
        self.move_to_end(key)
        if len(self) > self.maxsize:
            self.popitem(last=False)


word_cache = LRUCache()
topic_cache = LRUCache(maxsize=200)


def get_db_connection():
    # Vercel'de dosya sistemi salt okunur; sadece okuma yapıyoruz
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def ai_error_response(e: AIUnavailable):
    if e.rate_limited:
        return jsonify({"error": "Tüm ücretsiz AI kotaları şu an dolu. Bir dakika sonra tekrar dene."}), 429
    print(f"[ai] all providers failed: {e}")
    if not active_providers():
        return jsonify({"error": "Sunucuda AI anahtarı tanımlı değil (.env dosyasını kontrol et)."}), 503
    return jsonify({"error": "AI şu an yanıt veremiyor. Biraz sonra tekrar dene."}), 503


# ───────────────────────── Pages ─────────────────────────

APP_COOKIE = "cv_app"  # uygulamayı en az bir kez açanları işaretler


@app.route("/")
def home():
    # Eski bağlantılar (/?mode=vocab vb.) doğrudan uygulamaya gider.
    if request.args.get("mode"):
        return redirect("/app?" + urlencode({"mode": request.args["mode"]}))
    # Daha önce uygulamayı açmış biri siteye dışarıdan girerse tanıtımı atla.
    # Site içinden (logo/nav) gelen her zaman tanıtım sayfasını görür.
    ref = urlparse(request.referrer or "")
    if request.cookies.get(APP_COOKIE) and ref.netloc != request.host:
        return redirect("/app")
    return render_template("home.html")


@app.route("/app")
def chat_app():
    resp = make_response(render_template("index.html"))
    resp.set_cookie(APP_COOKIE, "1", max_age=60 * 60 * 24 * 365, samesite="Lax")
    return resp


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /app\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    pages = [("/", "1.0"), ("/guide", "0.8"), ("/about", "0.6"), ("/privacy", "0.3"), ("/terms", "0.3")]
    urls = "".join(f"<url><loc>{SITE_URL}{p}</loc><priority>{pr}</priority></url>" for p, pr in pages)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(xml, mimetype="application/xml")


# ───────────────────────── API ─────────────────────────

@app.route("/api/health")
def health():
    return jsonify({"ok": True, "providers": [p.name for p in active_providers()]})


@app.route("/api/get_random_words", methods=["POST"])
def get_random_words():
    data = request.get_json(silent=True) or {}
    known = data.get("known_words", [])
    if not isinstance(known, list):
        known = []
    known = [w for w in known if isinstance(w, str)][:MAX_KNOWN_WORDS]
    count = max(1, min(int(data.get("count", 5) or 5), 10))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if known:
            # Büyük listelerde "NOT IN (?,?,...)" SQLite değişken sınırını aşabilir,
            # bu yüzden bilinen kelimeleri tek bir JSON parametresiyle gönderiyoruz.
            cur.execute(
                "SELECT word FROM words WHERE id > ? AND word NOT IN (SELECT value FROM json_each(?)) "
                "ORDER BY RANDOM() LIMIT ?",
                (SKIP_MOST_COMMON, json.dumps(known), count),
            )
        else:
            cur.execute(
                "SELECT word FROM words WHERE id > ? ORDER BY RANDOM() LIMIT ?", (SKIP_MOST_COMMON, count)
            )
        words = [row["word"] for row in cur.fetchall()]
        conn.close()
        return jsonify(words)
    except sqlite3.Error as e:
        print(f"[db] {e}")
        return jsonify({"error": "Kelime listesi okunamadı."}), 500


@app.route("/api/word_details")
@rate_limited
def word_details():
    word = (request.args.get("word") or "").strip().lower()
    if not word or not WORD_RE.match(word):
        return jsonify({"error": "Geçerli bir İngilizce kelime gir."}), 400

    cached = word_cache.get(word)
    if cached:
        return jsonify(cached)

    try:
        data, provider = complete_json(
            WORD_SYSTEM_PROMPT,
            [{"role": "user", "content": WORD_USER_TEMPLATE.format(word=word)}],
            temperature=0.3,
            max_tokens=1500,
            required_keys=("meaning_tr", "sentences"),
        )
    except AIUnavailable as e:
        return ai_error_response(e)

    sentences = data.get("sentences") if isinstance(data.get("sentences"), dict) else {}
    result = {
        "word": str(data.get("word") or word),
        "phonetic": str(data.get("phonetic") or ""),
        "part_of_speech": str(data.get("part_of_speech") or ""),
        "meaning_tr": str(data.get("meaning_tr") or ""),
        "sentences": {lvl: str(sentences.get(lvl) or "") for lvl in ("A1", "B1", "C1")},
        "tip": str(data.get("tip") or ""),
        "provider": provider,
    }
    word_cache.put(word, result)
    return jsonify(result)


def _clean_history(raw):
    """İstemciden gelen sohbet geçmişini modele gönderilebilir hale getirir."""
    history = []
    if not isinstance(raw, list):
        return history
    for msg in raw[-MAX_HISTORY:]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        history.append({"role": role, "content": content[:1500]})
    return history


@app.route("/api/analyze", methods=["POST"])
@rate_limited
def analyze():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()

    if not text:
        return jsonify({"error": "Boş mesaj gönderilemez."}), 400
    if len(text) > MAX_TEXT_LEN:
        return jsonify({"error": f"Mesaj çok uzun (en fazla {MAX_TEXT_LEN} karakter)."}), 400

    messages = _clean_history(data.get("history"))
    messages.append({"role": "user", "content": text})

    try:
        result, provider = complete_json(
            ANALYZER_SYSTEM_PROMPT, messages, temperature=0.3, max_tokens=1500
        )
    except AIUnavailable as e:
        return ai_error_response(e)

    kind = result.get("type")
    if kind == "reply" or ("text" in result and "score" not in result):
        reply = str(result.get("text") or "").strip()
        if not reply:
            return jsonify({"error": "Model boş yanıt döndürdü."}), 502
        return jsonify({"status": "success", "type": "reply", "data": {"text": reply}, "provider": provider})

    missing = {"score", "corrected_sentence", "explanation"} - result.keys()
    if missing:
        return jsonify({"error": "Model eksik yanıt döndürdü, tekrar dene."}), 502
    try:
        score = max(0, min(100, int(float(result["score"]))))
    except (TypeError, ValueError):
        return jsonify({"error": "Model geçersiz puan döndürdü, tekrar dene."}), 502

    payload = {
        "score": score,
        "corrected_sentence": str(result.get("corrected_sentence") or ""),
        "explanation": str(result.get("explanation") or ""),
        "motivation": str(result.get("motivation") or ""),
    }
    return jsonify({"status": "success", "type": "analysis", "data": payload, "provider": provider})


# ───────────────────────── Konu çalış ─────────────────────────

def _s(value, limit=600):
    """Model çıktısındaki bir alanı güvenli, kısaltılmış string'e çevir."""
    return str(value or "").strip()[:limit]


def _clean_quiz(raw):
    """Quiz sorularını doğrula; bozuk soruları at. En az 3 geçerli soru yoksa None."""
    questions = []
    for q in raw if isinstance(raw, list) else []:
        if not isinstance(q, dict):
            continue
        kind = q.get("type")
        text = _s(q.get("q"), 300)
        answer = _s(q.get("answer"), 120)
        if not text or not answer:
            continue
        # Her soru tam olarak bir boşluk içermeli (iki boşluklu sorular arayüzde bozuk görünür)
        if kind == "fill" and text.count("___") != 1:
            continue
        if kind == "choice" and text.count("___") > 1:
            continue
        item = {"type": kind, "q": text, "answer": answer, "explain": _s(q.get("explain"), 400)}
        if kind == "choice":
            options = [_s(o, 120) for o in q.get("options", []) if _s(o)]
            options = list(dict.fromkeys(options))  # tekrarları at
            if answer not in options:
                # Model cevabı seçeneklerde birebir yazmamışsa büyük/küçük harf duyarsız eşle
                match = next((o for o in options if o.lower() == answer.lower()), None)
                if not match:
                    continue
                item["answer"] = match
            if not 2 <= len(options) <= 5:
                continue
            item["options"] = options
        elif kind == "fill":
            accept = q.get("accept") if isinstance(q.get("accept"), list) else []
            item["accept"] = [_s(a, 120).lower() for a in accept if _s(a)][:10]
        else:
            continue
        questions.append(item)
    return questions[:6] if len(questions) >= 3 else None


def _clean_lesson(data):
    uses = []
    for u in data.get("uses") or []:
        if isinstance(u, dict) and _s(u.get("text")):
            uses.append({k: _s(u.get(k), 400) for k in ("title", "text", "en", "tr")})
    traps = []
    for t in data.get("traps") or []:
        if isinstance(t, dict) and _s(t.get("wrong")) and _s(t.get("right")):
            traps.append({k: _s(t.get(k), 300) for k in ("wrong", "right", "why")})
    compare = data.get("compare")
    if isinstance(compare, dict) and _s(compare.get("with")) and _s(compare.get("text")):
        compare = {k: _s(compare.get(k), 400) for k in ("with", "text", "a", "b")}
    else:
        compare = None
    return {
        "topic": _s(data.get("topic"), 80),
        "topic_tr": _s(data.get("topic_tr"), 80),
        "level": _s(data.get("level"), 12),
        "summary": _s(data.get("summary"), 800),
        "formula": [_s(f, 120) for f in (data.get("formula") or []) if _s(f)][:5],
        "uses": uses[:5],
        "turkish_link": _s(data.get("turkish_link"), 800),
        "traps": traps[:4],
        "signal_words": [_s(w, 40) for w in (data.get("signal_words") or []) if _s(w)][:10],
        "compare": compare,
        "tip": _s(data.get("tip"), 400),
    }


def _read_topic():
    data = request.get_json(silent=True) or {}
    topic = " ".join(str(data.get("topic", "")).split())
    if not topic:
        return None, (jsonify({"error": "Bir konu yaz (ör. present perfect)."}), 400)
    if len(topic) > MAX_TOPIC_LEN:
        return None, (jsonify({"error": f"Konu adı çok uzun (en fazla {MAX_TOPIC_LEN} karakter)."}), 400)
    return topic, None


@app.route("/api/topic", methods=["POST"])
@rate_limited
def topic_lesson():
    topic, err = _read_topic()
    if err:
        return err

    key = topic.lower()
    cached = topic_cache.get(key)
    if cached:
        return jsonify(cached)

    try:
        data, provider = complete_json(
            TOPIC_SYSTEM_PROMPT,
            [{"role": "user", "content": TOPIC_USER_TEMPLATE.format(topic=topic)}],
            temperature=0.4,
            max_tokens=3500,  # ölçüm: ders+quiz ≈ 2000 token; Groq ücretsiz katman 8k token/dk
        )
    except AIUnavailable as e:
        return ai_error_response(e)

    if data.get("type") == "invalid":
        msg = _s(data.get("message")) or "Bu bir İngilizce konusu gibi görünmüyor. Ör: present perfect, articles, conditionals."
        return jsonify({"error": msg}), 422

    lesson = _clean_lesson(data)
    quiz = _clean_quiz(data.get("quiz"))
    if not lesson["topic"] or not lesson["summary"] or not lesson["uses"] or not quiz:
        return jsonify({"error": "Ders tam oluşturulamadı, tekrar dene."}), 502

    result = {"lesson": lesson, "quiz": quiz, "provider": provider}
    topic_cache.put(key, result)
    # Normalize edilmiş adla da önbelleğe al (ör. "present perfekt" → "Present Perfect")
    topic_cache.put(lesson["topic"].lower(), result)
    return jsonify(result)


@app.route("/api/topic_quiz", methods=["POST"])
@rate_limited
def topic_quiz():
    topic, err = _read_topic()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    previous = [str(q)[:200] for q in (data.get("previous") or []) if isinstance(q, str)][-15:]
    prev_text = "\n".join(f"- {q}" for q in previous) or "- (yok)"

    try:
        result, provider = complete_json(
            TOPIC_SYSTEM_PROMPT,
            [{"role": "user", "content": TOPIC_QUIZ_USER_TEMPLATE.format(topic=topic, previous=prev_text)}],
            temperature=0.8,
            max_tokens=2200,
        )
    except AIUnavailable as e:
        return ai_error_response(e)

    quiz = _clean_quiz(result.get("quiz"))
    if not quiz:
        return jsonify({"error": "Yeni sorular oluşturulamadı, tekrar dene."}), 502
    return jsonify({"topic": topic, "quiz": quiz, "provider": provider})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5050)))
