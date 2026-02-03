from flask import Flask, render_template, request, jsonify
import sqlite3
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
load_dotenv()


app = Flask(__name__)
DB_FILE = "vocab.db"
generated_words_cache = {}
KNOWN_WORDS_FILE = 'known_words.json'

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 
genai.configure(api_key=GOOGLE_API_KEY)

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

@app.route('/api/get_random_words')
def get_random_words():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM words WHERE status='new' ORDER BY RANDOM() LIMIT 3")
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

@app.route('/api/mark_known', methods=['POST'])
def mark_known():
    data = request.json
    word = data.get('word')
    if not word:
        return jsonify({"error": "No word provided"}), 400
    
    try:
        conn = get_db_connection()
        conn.execute("UPDATE words SET status='learned' WHERE word=?", (word,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mark_known', methods=['POST'])
def mark_known_simple():
    data = request.json
    word = data.get('word')
    if not word:
        return jsonify({"status": "error", "message": "No word provided"}), 400
    
    try:
        known_list = []
        if os.path.exists(KNOWN_WORDS_FILE):
            with open(KNOWN_WORDS_FILE, 'r') as f:
                try:
                    known_list = json.load(f)
                except json.JSONDecodeError:
                    known_list = []
        
        if word not in known_list:
            known_list.append(word)
            
        with open(KNOWN_WORDS_FILE, 'w') as f:
            json.dump(known_list, f)
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        prompt = f"""
        Act as "CodeVocab", a friendly, slightly futuristic English tutor.
        Analyze the following English sentence: "{text}"
        
        Return ONLY a raw JSON response (no markdown formatting) with these valid fields:
        1. "score": (0-100 integer based on grammar/context)
        2. "corrected": (The corrected sentence if needed, or same if perfect)
        3. "explanation": (Turkish explanation, simple and clear. encapsulate in HTML tags like <b> for emphasis if needed)
        4. "motivation": (Encouraging tone, in Turkish)
        
        Example JSON:
        {{
            "score": 85,
            "corrected": "I am going to school.",
            "explanation": "<b>'Go'</b> fiili şimdiki zamanda <b>'going'</b> olarak kullanılır.",
            "motivation": "Harikasın, devam et! 🚀"
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

if __name__ == '__main__':
    app.run(debug=True, port=5002, host='0.0.0.0')
