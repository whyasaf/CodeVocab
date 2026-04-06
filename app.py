from flask import Flask, render_template, request, jsonify
import sqlite3
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
load_dotenv()


app = Flask(__name__)
app.debug = False
DB_FILE = "vocab.db"
generated_words_cache = {}

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-flash-latest')
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_word_card(word):
    if word in generated_words_cache:
        print(f"Combinando (Fetching from Cache): {word}")
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
        response = model.generate_content(prompt)
        text = response.text
        text = text.replace('```json', '').replace('```', '').strip()
        
        data = json.loads(text)
        
        if 'definition' in data:
            data['meaning_tr'] = data['definition']
            
        generated_words_cache[word] = data
        return data
        
    except Exception as e:
        print(f"HATA DETAYI: {e}")
        if 'response' in locals():
            print(f"CEVAP: {response.text}")
        else:
            print("CEVAP: Cevap yok (API çağrısı başarısız oldu)")
            
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
            query = f"SELECT word FROM words WHERE word NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 3"
            cursor.execute(query, known_words)
        else:
            cursor.execute("SELECT word FROM words ORDER BY RANDOM() LIMIT 3")

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

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        prompt = f"""
        Act as "CodeVocab", a refined, supportive AI English architect. 
        Your goal is to evaluate the sentence: "{text}"
        
        CRITICAL RULES:
        1. BE LENIENT: If the only "errors" are minor capitalization (e.g. 'i' instead of 'I') or missing a final period, do NOT penalize heavily. Highlight it gently but focus on the structural integrity.
        2. MEANING FIRST: If the core message is clear and grammatically sound, give a high score.
        3. TEACHING TONE: Provide clear, encouraging feedback in Turkish.
        
        Return ONLY a raw JSON response (no markdown) with:
        1. "score": (0-100 integer)
        2. "corrected": (The professionally polished version)
        3. "explanation": (A friendly Turkish breakdown of what was good or what could be better. Use HTML <b> or <i> tags for key terms.)
        4. "motivation": (A modern, punchy motivational sentence in Turkish with an emoji.)
        
        Example JSON:
        {{
            "score": 92,
            "corrected": "I like coding in Python.",
            "explanation": "Cümlen gayet net! Sadece <b>'i'</b> yerine büyük <b>'I'</b> kullanman daha profesyonel görünür. Harika bir yapı kurmuşsun.",
            "motivation": "Kod gibi temiz bir cümle! 💻"
        }}
        """
        
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)
        
        return jsonify({
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


