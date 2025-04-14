from flask import Flask
from flask_cors import CORS
from config import Config
from routes import register_routes
from logging_config import setup_logging

# Инициализация приложения
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})
setup_logging()

# Регистрация маршрутов
register_routes(app)

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)