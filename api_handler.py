import requests
import json
from deep_translator import GoogleTranslator

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"

def get_word_details(word):
    url = API_URL.format(word)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        entry = data[0]

        
        phonetic_text = entry.get('phonetic', '')
        if not phonetic_text:
             for p in entry.get('phonetics', []):
                if 'text' in p and p['text']:
                    phonetic_text = p['text']
                    break

        
        audio_url = ''
        for p in entry.get('phonetics', []):
            if 'audio' in p and p['audio']:
                audio_url = p['audio']
                break 

       
        definition_text = "Definition not found."
        word_type = "Unknown"
        example_text = None

        if 'meanings' in entry and entry['meanings']:
            first_meaning = entry['meanings'][0]
            word_type = first_meaning.get('partOfSpeech', 'Unknown')
            
            if 'definitions' in first_meaning and first_meaning['definitions']:
                first_def = first_meaning['definitions'][0]
                definition_text = first_def.get('definition', definition_text)
                example_text = first_def.get('example')

        
        try:
            translator = GoogleTranslator(source='en', target='tr')
            meaning_tr = translator.translate(definition_text)
        except Exception as e:
            print(f"Translation Error: {e}")
            meaning_tr = "Çeviri yapılamadı."

       
        sentences = {
            'A1': f"This is a simple sentence with {word}.",
            'B1': example_text if example_text else f"The word {word} is used here.",
            'C1': f"In a more complex context, {word} implies deeper nuances."
        }

        return {
            'word': word,
            'phonetic': phonetic_text,
            'audio': audio_url,
            'type': word_type,
            'definition': definition_text,
            'meaning_tr': meaning_tr,
            'sentences': sentences
        }

    except requests.exceptions.RequestException as e:
        print(f"Error for word '{word}': {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

if __name__ == "__main__":
    test_word = "resilient"
    print(f"Fetching details for '{test_word}'...")
    details = get_word_details(test_word)
    
    if details:
        print("\nDetails Found:")
        print(json.dumps(details, indent=4, ensure_ascii=False))
    else:
        print("\nCould not fetch details.")
