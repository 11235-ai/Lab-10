import json
import time
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer
import random
from PIL import Image
from io import BytesIO
import os
import sys

class Speech:
    def __init__(self, lang='ru'):
        self.tts = pyttsx3.init()
        self.lang = lang
        self.set_voice(self.lang)

    def set_voice(self, lang_code):
        """
        Set TTS voice based on language code (e.g., 'ru', 'en').
        """
        voices = self.tts.getProperty('voices')
        for voice in voices:
            if lang_code in ''.join(voice.languages).lower():
                self.tts.setProperty('voice', voice.id)
                return
        # fallback to default

    def speak(self, text):
        self.tts.say(text)
        self.tts.runAndWait()

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
                        yield text
        except KeyboardInterrupt:
            return

class RickAndMortyAPI:
    BASE_URL = 'https://rickandmortyapi.com/api'

    def __init__(self):
        self.character = None

    def _fetch(self, endpoint):
        try:
            res = requests.get(f"{self.BASE_URL}/{endpoint}")
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {'error': str(e)}

    def random_character(self):
        # fetch count
        info = self._fetch('character')
        total = info.get('info', {}).get('count', 826)
        char_id = random.randint(1, total)
        data = self._fetch(f'character/{char_id}')
        if 'error' in data:
            return None, data['error']
        self.character = data
        return data['name'], None

    def save_image(self, folder='images'):
        if not self.character:
            return None, 'Character not selected.'
        os.makedirs(folder, exist_ok=True)
        url = self.character['image']
        data = requests.get(url).content
        safe_name = ''.join(c for c in self.character['name'] if c.isalnum() or c in (' ', '_')).strip()
        path = os.path.join(folder, f"{safe_name}.jpg")
        with open(path, 'wb') as f:
            f.write(data)
        return path, None

    def first_episode(self):
        if not self.character:
            return None, 'Character not selected.'
        url = self.character['episode'][0]
        ep = self._fetch_from_url(url)
        return ep.get('name'), None

    def show_image(self):
        if not self.character:
            return None, 'Character not selected.'
        url = self.character['image']
        img = Image.open(BytesIO(requests.get(url).content))
        img.show()
        return 'Image displayed.', None

    def image_resolution(self):
        if not self.character:
            return None, 'Character not selected.'
        url = self.character['image']
        img = Image.open(BytesIO(requests.get(url).content))
        w, h = img.size
        return f"{w}x{h}", None

    def origin(self):
        if not self.character:
            return None, 'Character not selected.'
        return self.character['origin']['name'], None

    def location(self):
        if not self.character:
            return None, 'Character not selected.'
        return self.character['location']['name'], None

    def episodes_list(self):
        if not self.character:
            return None, 'Character not selected.'
        eps = []
        for url in self.character['episode']:
            data = self._fetch_from_url(url)
            eps.append(data.get('name'))
        return eps, None

    def _fetch_from_url(self, url):
        try:
            r = requests.get(url)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return {}

COMMANDS = {
    'случайный': 'random',
    'сохранить': 'save',
    'эпизод': 'first_ep',
    'показать': 'show_img',
    'разрешение': 'resolution',
    'происхождение': 'origin',
    'локация': 'location',
    'список эпизодов': 'list_eps',
    'выход': 'exit'
}

if __name__ == '__main__':
    MODEL_PATH = sys.argv[1] if len(sys.argv) > 1 else 'vosk-model-small-ru-0.22'
    speech = Speech(lang='ru')
    recognizer = Recognizer(MODEL_PATH)
    api = RickAndMortyAPI()

    speech.speak("Голосовой ассистент Рик и Морти активирован.")
    speech.speak("Команды: " + ", ".join(COMMANDS.keys()))
    time.sleep(0.5)

    for text in recognizer.listen():
        print(f"Распознано: {text}")
        cmd = text.lower()
        if 'выход' in cmd or 'прощаюсь' in cmd:
            speech.speak('До скорых встреч!')
            break

        if 'случайный' in cmd:
            name, err = api.random_character()
            speech.speak(name if not err else err)

        elif 'сохранить' in cmd:
            path, err = api.save_image()
            speech.speak(f'Сохранено: {path}' if not err else err)

        elif 'эпизод' in cmd:
            ep, err = api.first_episode()
            speech.speak(ep if not err else err)

        elif 'список эпизодов' in cmd:
            eps, err = api.episodes_list()
            speech.speak(', '.join(eps) if not err else err)

        elif 'показать' in cmd:
            msg, err = api.show_image()
            speech.speak(msg if not err else err)

        elif 'разрешение' in cmd:
            res, err = api.image_resolution()
            speech.speak(f"Разрешение: {res}" if not err else err)

        elif 'происхождение' in cmd:
            origin, err = api.origin()
            speech.speak(origin if not err else err)

        elif 'локация' in cmd:
            loc, err = api.location()
            speech.speak(loc if not err else err)

        else:
            speech.speak("Команда не распознана. Попробуйте снова.")
