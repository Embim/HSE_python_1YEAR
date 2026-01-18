import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлена!")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

WATER_BASE_RATE = 30

WATER_PER_ACTIVITY_30MIN = 500

WATER_HOT_WEATHER_BONUS = 750

HOT_WEATHER_THRESHOLD = 25

WORKOUT_CALORIE_RATES = {
    "бег": 10.0,
    "ходьба": 4.0,
    "плавание": 8.0,
    "велосипед": 7.0,
    "йога": 3.0,
    "силовая": 6.0,
    "default": 5.0
}

RECOMMENDATION_THRESHOLDS = {
    "calorie_deficit_very_low": 200,
    "calorie_deficit_low": 500,
    "calorie_deficit_high": 800,
    "calorie_surplus_small": 300,
    "calorie_surplus_moderate": 600,
    "water_deficit_threshold": 500
}

LOW_CALORIE_FOODS = [
    {"name": "Огурец", "calories": 15, "benefit": "95% вода, отлично для гидратации"},
    {"name": "Помидор", "calories": 18, "benefit": "Богат ликопином и витамином C"},
    {"name": "Салат", "calories": 14, "benefit": "Клетчатка и минимум калорий"},
    {"name": "Брокколи", "calories": 34, "benefit": "Высокое содержание витамина C и клетчатки"},
    {"name": "Морковь", "calories": 41, "benefit": "Витамин A для зрения"},
    {"name": "Яблоко", "calories": 52, "benefit": "Пектин и натуральные сахара"},
]

WORKOUT_RECOMMENDATIONS = {
    "light": [
        {"name": "Прогулка", "duration": 30, "benefit": "Легкая активность для восстановления"},
        {"name": "Растяжка", "duration": 20, "benefit": "Улучшает гибкость и кровообращение"},
    ],
    "moderate": [
        {"name": "Плавание", "duration": 30, "benefit": "Вода – это колыбель разумной жизни. Я просто возвращаюсь к истокам бытия… получаю от этого несказанное удовольствие... Все болезни – от бескультурья"},
        {"name": "Йога", "duration": 40, "benefit": "Баланс тела и разума"},
        {"name": "Велосипед", "duration": 45, "benefit": "Кардио и укрепление ног"},
    ],
    "intense": [
        {"name": "Интервальный бег", "duration": 25, "benefit": "Максимальное сжигание калорий"},
        {"name": "Силовая тренировка", "duration": 45, "benefit": "Набор мышечной массы"},
        {"name": "Кроссфит", "duration": 30, "benefit": "Комплексная высокоинтенсивная тренировка"},
    ]
}

WATER_TIPS = [
    "Поставьте бутылку воды на видное место",
    "Пейте воду перед каждым приемом пищи",
    "Установите напоминание каждый час"
]
