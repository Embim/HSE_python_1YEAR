from datetime import date
import API
import calculations
from repositories import DiaryRepository, UserRepository
from dto import DailyProgressDTO
from logger import log

class DiaryService:
    @staticmethod
    async def log_water(user_id, amount):
        await DiaryRepository.log_water(user_id, amount)

        user = await UserRepository.get_by_id(user_id)
        progress = await DiaryRepository.get_progress(user_id, date.today())

        remaining = max(0, user.water_goal - progress.logged_water)

        return {
            'amount': amount,
            'logged_water': progress.logged_water,
            'water_goal': user.water_goal,
            'remaining': remaining,
            'goal_reached': remaining == 0
        }

    @staticmethod
    async def log_food(user_id, product_name, grams, calories, protein, carbs, fat):
        await DiaryRepository.log_food(
            user_id, product_name, grams, calories, protein, carbs, fat
        )

        user = await UserRepository.get_by_id(user_id)
        progress = await DiaryRepository.get_progress(user_id, date.today())

        net_calories = progress.logged_calories - progress.burned_calories
        remaining = user.calorie_goal - net_calories

        return {
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fat': fat,
            'net_calories': net_calories,
            'calorie_goal': user.calorie_goal,
            'remaining': remaining,
            'over_limit': remaining < 0
        }

    @staticmethod
    async def log_workout(user_id, workout_type, duration_minutes):
        user = await UserRepository.get_by_id(user_id)

        calories_burned = calculations.calculate_workout_calories(
            workout_type, duration_minutes, user.weight
        )

        extra_water = int((duration_minutes / 30) * 200)

        await DiaryRepository.log_workout(
            user_id, workout_type, duration_minutes, calories_burned
        )

        progress = await DiaryRepository.get_progress(user_id, date.today())
        net_calories = progress.logged_calories - progress.burned_calories

        return {
            'workout_type': workout_type,
            'duration': duration_minutes,
            'calories_burned': calories_burned,
            'extra_water': extra_water,
            'net_calories': net_calories,
            'calorie_goal': user.calorie_goal
        }

    @staticmethod
    async def get_progress(user_id):
        user = await UserRepository.get_by_id(user_id)
        progress = await DiaryRepository.get_progress(user_id, date.today())

        water_logged = progress.logged_water
        water_goal = user.water_goal
        water_remaining = max(0, water_goal - water_logged)
        water_percent = min(100, int((water_logged / water_goal) * 100))

        calories_consumed = progress.logged_calories
        calories_burned = progress.burned_calories
        net_calories = calories_consumed - calories_burned
        calorie_goal = user.calorie_goal
        calorie_remaining = calorie_goal - net_calories
        calorie_percent = min(100, int((net_calories / calorie_goal) * 100))

        return {
            'water_logged': water_logged,
            'water_goal': water_goal,
            'water_remaining': water_remaining,
            'water_percent': water_percent,
            'calories_consumed': calories_consumed,
            'calories_burned': calories_burned,
            'net_calories': net_calories,
            'calorie_goal': calorie_goal,
            'calorie_remaining': calorie_remaining,
            'calorie_percent': calorie_percent
        }

    @staticmethod
    async def search_food(product_name):
        food_info = await API.search_food_nutrition(product_name)

        if not food_info:
            log.warning(f"Продукт не найден {product_name}")
            return None

        return food_info

    @staticmethod
    async def get_historical_data(user_id, days=7):
        return await DiaryRepository.get_historical_data(user_id, days)
