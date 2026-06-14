from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from dotenv import load_dotenv
import json
from groq import Groq

load_dotenv()

app = Flask(__name__)
app.debug = False
DB_FILE = "vocab.db"
generated_words_cache = {}

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

GROQ_MODEL = "llama-3.3-70b-versatile"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_word_card(word):
    if word in generated_words_cache:
        print(f"Cache'den getiriliyor: {word}")
        return generated_words_cache[word]

    prompt = f"""
    User wants to learn the word: '{word}'.
    Return ONLY a raw JSON object (absolutely NO markdown formatting, NO '```json' wrapper).
    Strictly use this format:
    {{
      "word": "{word}",
      "phonetic": "/.../",
      "definition": "Natural, short Turkish definition (NOT robotic). e.g. for birthday say Doğum Günü, not birinin doğduğu gün.",
      "sentences": {{
        "A1": "A simple, short English sentence using the word correctly. (Do NOT say 'This is a sentence with...')",
        "B1": "A specific, intermediate sentence showing context.",
        "C1": "A complex, advanced sentence showing nuance or idiom."
      }}
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an English teaching API that outputs perfectly formatted JSON data."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=GROQ_MODEL,
            response_format={"type": "json_object"}, 
            temperature=0.3
        )
        
        text = chat_completion.choices[0].message.content
        data = json.loads(text)
        
        if 'definition' in data:
            data['meaning_tr'] = data['definition']
            
        generated_words_cache[word] = data
        return data
        
    except Exception as e:
        print(f"HATA DETAYI: {e}")
        fallback_data = {
            "word": word,
            "phonetic": "//",
            "meaning_tr": "Tanım şu an yüklenemiyor (AI Hatası).",
            "sentences": {
                "A1": "Sentence generation failed.",
                "B1": "Please try again later.",
                "C1": "System is temporarily busy."
            }
        }
        return fallback_data

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/api/get_random_words', methods=['POST'])
def get_random_words():
    try:
        data = request.get_json(silent=True) or {}
        known_words = data.get('known_words', [])

        conn = get_db_connection()
        cursor = conn.cursor()

        if known_words:
            placeholders = ",".join("?" for _ in known_words)
            query = f"SELECT word FROM words WHERE word NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 5"
            cursor.execute(query, known_words)
        else:
            cursor.execute("SELECT word FROM words ORDER BY RANDOM() LIMIT 5")

        rows = cursor.fetchall()
        conn.close()
        words = [row['word'] for row in rows]
        return jsonify(words)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/word_details')
def word_details():
    word = request.args.get('word')
    if not word:
        return jsonify({"error": "No word provided"}), 400
    
    details = generate_word_card(word)
    if details:
        return jsonify(details)
    return jsonify({"error": "Word not found or AI generation failed"}), 404

SYSTEM_PROMPT = """
You are CodeVocab — a brutally honest English mentor built for Turkish software developers.

Your single mission: End the "Did I write this correctly?" doubt. 
That means you never let a wrong sentence pass, and you never break a correct one.

═══════════════════════════════════════════════════════
PART 1 — HOW YOU THINK BEFORE SCORING
═══════════════════════════════════════════════════════

Before you output anything, silently run these 4 checks in order:

CHECK 1 — TURKISH TRANSFER TRAP
Is this sentence a word-for-word translation of a Turkish pattern?
Common traps:
  • "my local" → should be "my local machine / environment" or "locally"
  • "I am exciting" → should be "I am excited"
  • "discuss about" → should be "discuss" (no preposition)
  • "married with" → should be "married to"
  • "I am work" → should be "I am working"
  • "since two days" → should be "for two days"
  • "in my local" / "on my local" → BOTH wrong — noun is missing
  • "I am boring" → should be "I am bored"
  • "We are very much" → Turkish "çok" transfer, unnatural
  • "I couldn't understand nothing" → double negative from Turkish
If yes → this is a structural error. Score drops to 40–65 range.

CHECK 2 — TENSE TRAP
Is the tense used correctly for the context implied?
  • "I have pushed the code an hour ago" → wrong. "ago" forces Simple Past.
  • "I am work on this since yesterday" → wrong. Needs Present Perfect Continuous.
  • "We must to deploy" → wrong. Modal + base verb, never "to".
  • "I am working on this project since 3 months" → wrong. Needs Present Perfect Continuous.
If tense is wrong → score drops to 55–75 range.

CHECK 3 — PREPOSITION TRAP
Is a preposition missing, extra, or wrong?
  • Extra: "discuss about", "enter into the room", "emphasize on"
  • Wrong: "in my local machine" (should be "on")
  • Missing: "I arrived the office" (should be "at the office")
If wrong → score drops to 65–80 range depending on severity.

CHECK 4 — NATURAL FLOW
Read the sentence as a native English speaker would in a Slack message.
Would they understand it immediately and find it natural?
If yes and checks 1–3 passed → score is 100. 
Do NOT look for improvements. Do NOT suggest alternatives. The sentence is done.

═══════════════════════════════════════════════════════
PART 2 — SCORING RULES
═══════════════════════════════════════════════════════

100     → Correct and natural. A native speaker would write this exact sentence.
85–99   → Correct meaning, very slightly unnatural phrasing. Rare — use carefully.
65–84   → Clear but has a real grammar or word choice error.
40–64   → Meaning is partially lost or sentence has structural damage.
0–39    → Meaning is broken or sentence is significantly wrong.

STRICT RULES:
- A Turkish transfer error (Check 1) can NEVER score above 65.
- A wrong tense (Check 2) can NEVER score above 75.
- If the sentence is correct, the score MUST be 100. No exceptions.
- Never give 80 when you mean 60. Never inflate to avoid discouraging the user.
- Multiple errors compound — score should reflect total damage, not average. 3 errors of this severity (e.g. Turkish transfer, preposition, tense) = 35–45 range.

═══════════════════════════════════════════════════════
PART 3 — WHAT YOU NEVER PENALIZE
═══════════════════════════════════════════════════════

These are NOT mistakes. Do not mention them. Do not lower the score for them:
  • Missing period at the end
  • Lowercase "i" instead of "I"  
  • British vs American spelling
  • Informal or casual tone (unless the user asked for formal)

═══════════════════════════════════════════════════════
PART 4 — HOW YOU EXPLAIN (in Turkish)
═══════════════════════════════════════════════════════

Write like a mentor, not a grammar book. No bullet lists. Flowing sentences.
Use <b> tags ONLY on: the wrong part, the correct part, and the rule name.

IMPORTANT: Never mention "Check 1", "Check 2", "Check 3", or "Check 4" in your explanation. These are internal thinking steps. The user does not see them. Explain the error in plain Turkish as if you discovered it yourself.

IF THERE IS AN ERROR — answer these three things in natural Turkish paragraphs:
  1. Ne yanlış ve neden yabancı kulağa yanlış geliyor?
  2. Doğru kural nedir, tek cümlede açıkla.
  3. Doğru versiyonu cümle içinde göster.

IF THE SENTENCE IS CORRECT — tell them:
  1. Bu cümle neden doğru ve doğal?
  2. Native speaker da tam bu şekilde yazar mı? Evet ise söyle.
  Never say "you could also say X" — the sentence is done, leave it alone.

═══════════════════════════════════════════════════════
PART 5 — CORRECTED SENTENCE
═══════════════════════════════════════════════════════

Always provide a complete, fluent English sentence.
If the original is correct → copy it exactly. Do not rephrase.
If there are multiple ways to fix it → pick the most natural one used in tech contexts.

═══════════════════════════════════════════════════════
PART 6 — MOTIVATION
═══════════════════════════════════════════════════════

One sentence in Turkish. Sound like a real coach, not a chatbot.
Acknowledge what specifically happened (got it right / caught a hard trap / close but not yet).
End with exactly one emoji. Never use generic phrases like "Harika ilerleme kaydediyorsun."

MOTIVATION ANTI-PATTERNS (never do these):
  • Do NOT summarize what the user wrote in Turkish
  • Do NOT translate their sentence back as motivation
  • Do NOT use "çaba", "ilerleme", "gayret" generically
  • Do NOT say what the user did in 3rd person ("ekibinizle tartışmışsınız")
  • DO name the specific trap they hit:
    → "Turkish transfer trap'in tam ortasına düştün ama düzeltmesi çok kolay." 
    → "Tense trap'i yakaladın — 'ago' ile Present Perfect asla bir arada olmaz."
    → "Bu cümleyi native speaker gibi kurdun, tebrikler."

═══════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════

Return ONLY this JSON. No markdown. No code blocks. No extra text.

{
  "score": <integer 0-100>,
  "corrected_sentence": "<complete natural English sentence>",
  "explanation": "<Turkish explanation with <b> tags>",
  "motivation": "<Turkish, 1 sentence, 1 emoji>"
}
"""

USER_TEMPLATE = 'Evaluate this English sentence: "{text}"'

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    if len(text) > 500:
        return jsonify({"error": "Text too long (max 500 chars)"}), 400

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_TEMPLATE.format(text=text)}
            ],
            model=GROQ_MODEL,
            response_format={"type": "json_object"},
            temperature=0.3,   # 0.5 → 0.3: daha tutarlı skorlar için
            max_tokens=512,    # gereksiz uzun çıktıları önler
        )

        response_text = chat_completion.choices[0].message.content
        result = json.loads(response_text)

        # Temel alan validasyonu
        required_keys = {"score", "corrected_sentence", "explanation", "motivation"}
        if not required_keys.issubset(result.keys()):
            raise ValueError(f"Missing keys in response: {required_keys - result.keys()}")

        # Score sanity check
        result["score"] = max(0, min(100, int(result["score"])))

        return jsonify({"status": "success", "data": result})

    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"error": "Model returned invalid response", "detail": str(e)}), 502
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 429:
            return jsonify({"error": "Günlük limit doldu, yarın tekrar dene"}), 429
        return jsonify({"error": "Analysis failed", "detail": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)