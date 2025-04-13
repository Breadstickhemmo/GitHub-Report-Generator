# GitHub Report Generator

Приложение для анализа качества кода GitHub репозиториев.

## Структура проекта
- **client/**: React-фронтенд
- **server/**: Flask-бэкенд

## Подготовка
- Создайте свой токен GitHub
- В папке server создайте файл `.env`
- В созданном файле вставьте свой токен GitHub `GITHUB_TOKEN=Ваш_токен`

## Запуск
1. Установите зависимости:
```bash
   cd client && npm install
   cd ../server && pip install -r requirements.txt
```

2. Запустите сервер:
```bash
    cd server && flask run
```

3. Запустите фронтенд:
```bash
    cd client && npm start
```