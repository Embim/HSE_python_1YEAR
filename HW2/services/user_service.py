import API
import calculations
from repositories import UserRepository
from dto import UserDTO
from logger import log

class UserService:
    @staticmethod
    async def create_profile(user_id, username, weight, height, age, gender,
                           activity_minutes, city, custom_calorie_goal=None):
        temperature = await API.get_temperature(city)
        if temperature is None:
            temperature = 20
            log.warning(f"Нет данных о температуре для {city}, используем 20С по умолчанию")

        water_norm = calculations.calculate_water_norm(
            weight, activity_minutes, temperature
        )

        calorie_norm = calculations.calculate_calorie_norm(
            weight, height, age, gender, activity_minutes, custom_calorie_goal
        )

        await UserRepository.create_or_update(
            user_id=user_id,
            username=username,
            weight=weight,
            height=height,
            age=age,
            gender=gender,
            activity_minutes=activity_minutes,
            city=city,
            water_goal=water_norm,
            calorie_goal=calorie_norm,
            custom_calorie_goal=custom_calorie_goal
        )

        return {
            'water_goal': water_norm,
            'calorie_goal': calorie_norm,
            'temperature': temperature
        }

    @staticmethod
    async def get_user(user_id) -> UserDTO:
        return await UserRepository.get_by_id(user_id)
