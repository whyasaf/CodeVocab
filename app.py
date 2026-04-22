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

GROQ_MODEL = "llama-3.1-8b-instant"

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
        system_prompt = """
        You are "CodeVocab", an expert Native English Architect and Mentor. 
        Your mission is to evaluate sentences with a focus on communication and natural flow, not minor typos.

        STRICT EVALUATION RULES:
        1. LENIENCY ON MINOR ERRORS: Ignore missing periods (.) at the end or minor capitalization issues (e.g., 'i' vs 'I'). Do NOT lower the score for these.
        2. FOCUS ON CORE: Only penalize for Grammar, Tense, and Word Choice errors.
        3. NO OVERTHINKING: If the user's sentence is already correct and natural, you MUST give 100/100. DO NOT suggest "better" versions or alternative words if the current one is already correct. 
        4. NATURAL FLOW: Only suggest changes if the original is objectively wrong or sounds very robotic/unclear.
        5. COMPLETENESS: Always provide a full, fluent, and perfect English sentence in 'corrected_sentence'.
        
        STRICT EXPLANATION STRUCTURE (IN TURKISH):
        If there are errors, explain these 3 things clearly:
        - Ne yanlış? (What is wrong?)
        - Neden yanlış? (Why is it wrong?)
        - Doğru kural ne? (What is the correct rule?)
        * If multiple errors exist, explain the most important one (Tense or Structure) first. Keep it simple; avoid overly complex jargon.

        IF THE SENTENCE IS ALREADY CORRECT:
        - Do NOT change it unnecessarily.
        - Explain WHY it is correct and valid.

        JSON FORMAT RULES:
        - "score": Integer (0-100).
        - "corrected_sentence": Perfect, natural English sentence.
        - "explanation": Teaching-focused Turkish feedback (using <b> tags for emphasis).
        - "motivation": Max 1 sentence + exactly 1 emoji.

        Return ONLY raw JSON:
        {
            "score": 90,
            "corrected_sentence": "I will fetch the data from the server.",
            "explanation": "Cümlen gayet anlaşılır. Ancak <b>'pull'</b> yerine teknik bağlamda daha doğal olan <b>'fetch'</b> kelimesini tercih etmelisin. İngilizcede veri çekme işlemleri için bu ifade daha yaygındır.",
            "motivation": "Harika bir ilerleme kaydediyorsun! 🚀"
        }
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f'Evaluate this sentence and return JSON: "{text}"'
                }
            ],
            model=GROQ_MODEL,
            response_format={"type": "json_object"},
            temperature=0.5
        )
        
        response_text = chat_completion.choices[0].message.content
        result = json.loads(response_text)
        
        return jsonify({
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        print(f"ANALYZE HATASI: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)