from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class UserDTO:
    user_id: int
    username: Optional[str]
    weight: float
    height: float
    age: int
    gender: str
    activity_minutes: int
    city: str
    water_goal: int
    calorie_goal: int
    custom_calorie_goal: Optional[int] = None

@dataclass
class DailyProgressDTO:
    logged_water: int
    logged_calories: int
    burned_calories: int

@dataclass
class HistoricalDataDTO:
    log_date: date
    logged_water: int
    logged_calories: int
    burned_calories: int

@dataclass
class FoodNutritionDTO:
    name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float

@dataclass
class RecommendationDTO:
    foods: list
    workouts: list
    water_tips: list
    food_message: str = ""
    workout_message: str = ""
