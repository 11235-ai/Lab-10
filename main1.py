import json, time

import pyttsx3, pyaudio, vosk



class Speech:
    def __init__(self):
        self.speaker = 0
        self.tts = pyttsx3.init('sapi5')

    def set_voice(self, speaker):
        self.voices = self.tts.getProperty('voices')
        for count, voice in enumerate(self.voices):
            if count == 0:
                print('0')
                id = voice.id
            if speaker == count:
                id = voice.id
        return id

    def text2voice(self, speaker=0, text='Готов'):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()


class Recognize:
    def __init__(self):
        model = vosk.Model('vosk-model-small-ru-0.22') #vosk-model-small-ru-0.22 /   model_small   / vosk-model-ru-0.10
        #model = r"C:\Users\G I G A B Y T E\Desktop\ITMO\Мехатроника и робототехника\1 Курс\Программирование на Python\Python\Семестр 2\Lab10\Lab-10\vosk-model-ru-0.10"



        self.record = vosk.KaldiRecognizer(model, 16000)
        self.stream()

    def stream(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=16000,
                         input=True,
                         frames_per_buffer=8000)


    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.record.AcceptWaveform(data) and len(data) > 0:
                answer = json.loads(self.record.Result())
                if answer['text']:
                    yield answer['text']


def speak(text):
    speech = Speech()
    speech.text2voice(speaker=1, text=text)


rec = Recognize()
text_gen = rec.listen()
rec.stream.stop_stream()
speak('Starting')
time.sleep(0.5)
rec.stream.start_stream()
for text in text_gen:
    if text == 'закрыть':
        speak('Бывай, ихтиандр')
        quit()
    else:
        print(text)
