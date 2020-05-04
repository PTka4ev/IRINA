# Импорт необходимых библиотек
import sys
from random import choice
from config import CONFIG_SET
import speech_recognition as sr
import pyttsx3
import time
import re
from bs4 import BeautifulSoup
import requests
import datetime
import os
import json
import apiai
from PyQt5 import QtWidgets, QtGui, QtCore
import threading

# Инициализация приложения
app = QtWidgets.QApplication([])
irina = pyttsx3.init()
voices = irina.getProperty('voices')
# Выбор голоса системы, если ругается
# Укажите 0 или 1
irina.setProperty('voice', voices[3].id)


# Функция для воспроизведения речи
def speak(what):
    irina.say(what)
    irina.runAndWait()
    irina.stop()


# Флаг для работы цикла
flag = True


# Обработка комманд
def commands(message, tb, i_label):
    # Погода, можно настроить свой город
    # В конце ссылки просто поменять на нужный
    if re.findall('погода|погоде|на улице|погодка', message):
        tb.setText('О погоде в Астрахани')
        weather = requests.get('https://yandex.ru/pogoda/astrahan')
        bs = BeautifulSoup(weather.text, 'html.parser')
        speak(bs.find('div', 'header-title header-title_in-fact').h1.text)
        speak('Температура' + bs.find('div', 'temp fact__temp fact__temp_size_s').find('span', 'temp__value').text + 'градусов')
        speak('Ощущается как' + bs.find('div', 'term term_orient_h fact__feels-like').find('span', 'temp__value').text)
        speak(bs.find('div', 'link__condition day-anchor i-bem').text)
        speak('Скорость ветра' + bs.find('span', 'wind-speed').text + 'метров в секунду')
        return True
    # Системное время
    elif re.findall('время|времени|часы|часов', message):
        tb.setText(f"Время {datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')}")
        speak(datetime.datetime.strftime(datetime.datetime.now(), '%H %M'))
        return True
    # Завершение программы
    elif re.findall('пока|до свидания|отключись|стоп', message):
        answer = choice(['Всего доброго!', 'Пока!', 'До связи!'])
        tb.setText(answer)
        speak(answer)
        app.exit()
        return False
    # Подключаемся к DialogFlow от Google
    else:
        # Вводим свой токен
        request = apiai.ApiAI(CONFIG_SET['token']).text_request()
        request.lang = 'ru'
        request.session_id = 'IrinaAiBot'
        request.query = message
        response = json.loads(request.getresponse().read().decode('utf-8'))
        resp = response['result']['fulfillment']['speech']

        if resp:
            # Обработка мема "Люк, я твой отец"
            if resp.startswith('Нееее'):
                i_label.setPixmap(QtGui.QPixmap('img/dad.png'))
            # Обработка мема "Тоби, пи*да"
            elif resp.startswith('Тоби '):
                i_label.setPixmap(QtGui.QPixmap('img/term.png'))
            tb.setText(resp)
            speak(resp)
            return True
        else:
            # Если ничего не вернулось
            tb.setText('Я не совсем поняла!')
            speak('Я не совсем поняла!')
            return True


r = sr.Recognizer()
m = sr.Microphone()
# Интерфейс
win = QtWidgets.QWidget()
win.setFixedSize(600, 500)
win.setWindowTitle('IRINA 0.4')
v_layout = QtWidgets.QVBoxLayout()
tb = QtWidgets.QLabel()
tb.setWordWrap(True)
tb.setAlignment(QtCore.Qt.AlignCenter)
font = tb.font()
font.setPixelSize(18)
tb.setFont(font)
tb.setFixedHeight(80)
b_exit = QtWidgets.QPushButton('Отключить')
b_exit.clicked.connect(app.exit)
pixmap = QtGui.QPixmap('img/main.png')
img_label = QtWidgets.QLabel()
img_label.setPixmap(pixmap)
v_layout.addWidget(img_label)
v_layout.addWidget(tb)
v_layout.addWidget(b_exit)
win.setLayout(v_layout)
win.show()


def irina_run(flag, tb, i_label):
    while flag:
        # Слушаем микрофон
        with m as source:
            tb.setText('Говорите, я слушаю')
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
            try:
                # Переводим в текст
                text = r.recognize_google(audio, language='ru_RU').lower()
                # Отдаем обработчику комманд
                flag = commands(text, tb, i_label)
            except sr.UnknownValueError:
                # Если не разобрали
                tb.setText('Я вас не слышу, повторите!')
                speak('Я вас не слышу, повторите!')
            time.sleep(0.1)
            i_label.setPixmap(QtGui.QPixmap('img/main.png'))


# Запускаем в другом потоке
x = threading.Thread(target=irina_run, args=(flag, tb, img_label), daemon=True)
x.start()
app.exec()
