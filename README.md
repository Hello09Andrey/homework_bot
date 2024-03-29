# Бот-ассистент.

## Описание:
Telegram-бот, который будет обращаться к API сервиса Практикум.Домашка и узнаёт статус домашней работы: взята ли забота в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

## Бот:
- раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

## Технологии:
- python 3.7
- python-dotenv 0.19.0
- python-telegram-bot 13.7
- requests 2.26.0

## Установка:
1. Клонировать репозиторий и перейти в него:
```
git clone git@github.com:Hello09Andrey/homework_bot.git
```
```
cd homework_bot/
```
2. Созайте виртуальное окружение и активируйте его:
* Windows:
```
python -m venv venv
```
```
source venv/Scripts/activate
```
3. Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
4. Создайте чат-бота в Телеграм
5. Создайте в директории файл .env:
```
touch .env
```
6. Опишите в нем необходимые токены в следующем формате:
```
PRAKTIKUM_TOKEN = <ваш Яндекс.Практикум Homework API token>, 
TELEGRAM_TOKEN = <ваш телеграм бот token>, 
TELEGRAM_CHAT_ID = <ваш телеграм чат id>
```
7. Запустите проект:
```
python homework.py
```

## Автор:
- Белоусов Андрей