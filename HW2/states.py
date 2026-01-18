from aiogram.fsm.state import State, StatesGroup

class ProfileSetup(StatesGroup):
    weight = State()
    height = State()
    age = State()
    gender = State()
    activity_minutes = State()
    city = State()
    custom_calorie_goal = State()

class FoodLogging(StatesGroup):
    product_name = State()
    grams = State()

class WorkoutLogging(StatesGroup):
    workout_type = State()
    duration = State()
