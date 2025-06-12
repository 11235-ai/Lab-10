import json
import time
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer
import os
import sys
import webbrowser

# ---------------- Speech ----------------
class Speech:
    def __init__(self, lang='en'):
        self.tts = pyttsx3.init()
        self.set_voice(lang)

    def set_voice(self, lang_code):
        voices = self.tts.getProperty('voices')
        for voice in voices:
            if lang_code in ''.join(voice.languages).lower():
                self.tts.setProperty('voice', voice.id)
                return
        # fallback to default voice

    def speak(self, text):
        print(f"Assistant: {text}")
        self.tts.say(text)
        self.tts.runAndWait()

# ---------------- Recognizer ----------------
class Recognizer:
    def __init__(self, model_path, rate=16000, buffer=8000):
        if not os.path.exists(model_path):
            model_path = os.path.join(os.getcwd(), model_path)
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, rate)
        self._init_stream(rate, buffer)

    def _init_stream(self, rate, buffer):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            input=True,
            frames_per_buffer=buffer,
        )

    def listen(self):
        try:
            while True:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        yield text.lower()
        except KeyboardInterrupt:
            return

# ---------------- Dictionary API ----------------
class DictionaryAPI:
    BASE_URL = 'https://api.dictionaryapi.dev/api/v2/entries/en/'

    def __init__(self):
        self.entry = None

    def find_word(self, word):
        try:
            res = requests.get(f"{self.BASE_URL}{word}")
            res.raise_for_status()
            data = res.json()
            self.entry = data[0]
            return True, None
        except requests.RequestException as e:
            return False, str(e)
        except (IndexError, ValueError):
            return False, 'No entry found.'

    def save(self, folder='dictionary_entries'):
        if not self.entry:
            return False, 'No word selected.'
        os.makedirs(folder, exist_ok=True)
        word = self.entry.get('word', 'entry')
        path = os.path.join(folder, f"{word}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.entry, f, ensure_ascii=False, indent=2)
        return True, path

    def meaning(self):
        if not self.entry:
            return None, 'No word selected.'
        definitions = []
        for m in self.entry.get('meanings', []):
            part = m.get('partOfSpeech', '')
            for d in m.get('definitions', []):
                definitions.append(f"({part}) {d.get('definition')}")
        return definitions, None

    def example(self):
        if not self.entry:
            return None, 'No word selected.'
        for m in self.entry.get('meanings', []):
            for d in m.get('definitions', []):
                ex = d.get('example')
                if ex:
                    return ex, None
        return None, 'No example found.'

    def link(self):
        if not self.entry:
            return None, 'No word selected.'
        word = self.entry.get('word')
        url = f"{self.BASE_URL}{word}"
        return url, None

# ---------------- Main ----------------
# Commands in English and Russian
COMMANDS = {
    'save': 'save', 'сохранить': 'save',
    'meaning': 'meaning', 'значение': 'meaning',
    'example': 'example', 'пример': 'example',
    'link': 'link', 'ссылка': 'link',
    'exit': 'exit', 'выход': 'exit', 'quit': 'exit'
}

if __name__ == '__main__':
    MODEL_PATH = sys.argv[1] if len(sys.argv) > 1 else 'vosk-model-small-ru-0.22'
    speech = Speech(lang='en')
    recognizer = Recognizer(MODEL_PATH)
    dictionary = DictionaryAPI()

    # Initial prompts in English
    speech.speak("Dictionary assistant activated. Say 'find <word>' or 'найти <word>'.")
    speech.speak("Then use commands: save/сохранить, meaning/значение, example/пример, link/ссылка, exit/выход.")
    time.sleep(0.5)

    for text in recognizer.listen():
        print(f"Heard: {text}")

        if text.startswith('find '):
            word = text.replace('find ', '').strip()
        elif text.startswith('найти '):
            word = text.replace('найти ', '').strip()
        else:
            word = None

        if word:
            ok, err = dictionary.find_word(word)
            speech.speak(f"Word '{word}' found." if ok else f"Error: {err}")
            continue

        cmd = text.strip()
        action = COMMANDS.get(cmd)
        if action == 'exit':
            speech.speak('Goodbye!')
            break
        if not action:
            speech.speak("Unknown command. Use save/сохранить, meaning/значение, example/пример, link/ссылка, or exit/выход.")
            continue

        if action == 'save':
            ok, res = dictionary.save()
            speech.speak(f"Saved to {res}" if ok else res)

        elif action == 'meaning':
            defs, err = dictionary.meaning()
            if defs:
                for d in defs:
                    speech.speak(d)
            else:
                speech.speak(err)

        elif action == 'example':
            ex, err = dictionary.example()
            speech.speak(ex if ex else err)

        elif action == 'link':
            url, err = dictionary.link()
            if url:
                webbrowser.open(url)
                speech.speak(f"Opened link: {url}")
            else:
                speech.speak(err)
