from datetime import date

class MessageFormatter:
    @staticmethod
    def start_message():
        return (
            "Добро пожаловать в Health Tracker Bot!\n\n"
            "Ваш персональный помощник для отслеживания здоровья\n\n"

            "Основные команды:\n"
            "/set_profile - Создать/обновить профиль\n"
            "/log_water <мл> - Записать воду (пример: /log_water 500)\n"
            "/log_food - Записать прием пищи\n"
            "/log_workout - Записать тренировку\n"
            "/check_progress - Прогресс за сегодня\n"
            "/graphs - Графики за 7 дней\n"
            "/recommend - Персональные рекомендации\n"
            "/help - Подробная инструкция\n\n"

            "Начните с команды /set_profile"
        )

    @staticmethod
    def help_message():
        return (
            "Помощь по использованию Health Tracker Bot\n\n"

            "Начало работы:\n"
            "1. /set_profile - Создать профиль\n"
            "   Укажите: вес, рост, возраст, пол, активность, город\n"
            "   Бот рассчитает нормы воды и калорий\n\n"

            "Ежедневный трекинг:\n"
            "2. /log_water <мл> - Записать воду\n"
            "   Пример: /log_water 500\n\n"

            "3. /log_food - Записать прием пищи\n"
            "   Шаги:\n"
            "   - Введите название продукта (на русском или английском)\n"
            "   - Укажите количество грамм\n"
            "   - Бот автоматически рассчитает БЖУ через AI\n\n"

            "4. /log_workout - Записать тренировку\n"
            "   Шаги:\n"
            "   - Выберите тип тренировки\n"
            "   - Укажите длительность в минутах\n"
            "   - Бот рассчитает сожженные калории\n\n"

            "Отслеживание прогресса:\n"
            "5. /check_progress - Текущий прогресс за день\n"
            "   Показывает: воду, калории, баланс БЖУ\n\n"

            "6. /graphs - Графики за последние 7 дней\n"
            "   Визуализация динамики воды и калорий\n\n"

            "7. /recommend - Персональные рекомендации\n"
        )

    @staticmethod
    def profile_created(city, temperature, water_goal, calorie_goal):
        return (
            f"Профиль сохранен!\n\n"
            f"Ваши нормы:\n"
            f"Вода: {water_goal} мл/день\n"
            f"Калории: {calorie_goal} ккал/день\n"
            f"Температура в {city}: {temperature}C\n\n"
            f"Используйте /log_water, /log_food, /log_workout для трекинга!"
        )

    @staticmethod
    def water_logged(amount, logged_water, water_goal, remaining, goal_reached):
        status = "Цель достигнута!" if goal_reached else "Осталось: {} мл".format(remaining)
        return (
            f"Записано: {amount} мл\n"
            f"Прогресс: {logged_water}/{water_goal} мл\n"
            f"{status}"
        )

    @staticmethod
    def food_logged(original_name, grams, calories, protein, carbs, fat,
                   net_calories, calorie_goal, remaining, over_limit):
        status = "Превышение!" if over_limit else "Осталось: {} ккал".format(remaining)
        return (
            f"Записано: {original_name} ({grams} г)\n"
            f"Калории: {calories:.1f} ккал\n"
            f"Белки: {protein:.1f} г | Углеводы: {carbs:.1f} г | Жиры: {fat:.1f} г\n\n"
            f"Всего за день: {net_calories}/{calorie_goal} ккал\n"
            f"{status}"
        )

    @staticmethod
    def food_nutrition(name, calories_per_100g):
        return (
            f"{name}\n"
            f"{calories_per_100g:.1f} ккал на 100 г\n\n"
            f"Сколько грамм вы съели?"
        )

    @staticmethod
    def workout_logged(workout_type, duration, calories_burned, extra_water,
                      net_calories, calorie_goal):
        return (
            f"Тренировка записана!\n"
            f"Тип: {workout_type}\n"
            f"Время: {duration} мин\n"
            f"Сожжено: {calories_burned} ккал\n"
            f"Выпейте дополнительно: {extra_water} мл воды\n\n"
            f"Баланс калорий: {net_calories}/{calorie_goal} ккал"
        )

    @staticmethod
    def progress_report(progress_data):
        water_bar = "#" * (progress_data['water_percent'] // 10) + " " * (10 - progress_data['water_percent'] // 10)
        calorie_bar = "#" * (progress_data['calorie_percent'] // 10) + " " * (10 - progress_data['calorie_percent'] // 10)

        water_status = "Цель достигнута!" if progress_data['water_remaining'] == 0 else "Осталось: {} мл".format(progress_data['water_remaining'])

        if progress_data['calorie_remaining'] < 0:
            calorie_status = "Превышение на {} ккал!".format(abs(progress_data['calorie_remaining']))
        else:
            calorie_status = "Осталось: {} ккал".format(progress_data['calorie_remaining'])

        return (
            f"Прогресс за {date.today().strftime('%d.%m.%Y')}\n\n"
            f"Вода:\n"
            f"[{water_bar}] {progress_data['water_percent']}%\n"
            f"Выпито: {progress_data['water_logged']} мл из {progress_data['water_goal']} мл\n"
            f"{water_status}\n\n"
            f"Калории:\n"
            f"[{calorie_bar}] {progress_data['calorie_percent']}%\n"
            f"Потреблено: {progress_data['calories_consumed']} ккал\n"
            f"Сожжено: {progress_data['calories_burned']} ккал\n"
            f"Баланс: {progress_data['net_calories']} ккал из {progress_data['calorie_goal']} ккал\n"
            f"{calorie_status}"
        )

    @staticmethod
    def no_profile():
        return "Сначала настройте профиль: /set_profile"

    @staticmethod
    def food_not_found(product_name):
        return (
            f"Продукт '{product_name}' не найден.\n"
            f"Попробуйте другое название или /log_food заново"
        )

    @staticmethod
    def insufficient_data():
        return "Недостаточно данных для построения графиков"

    @staticmethod
    def graph_caption():
        return "Ваш прогресс за последние 7 дней"

    @staticmethod
    def generating_graphs():
        return "Генерируем графики, пожалуйста, подождите"

    @staticmethod
    def recommendations_header():
        return "Персональные рекомендации:\n\n"
