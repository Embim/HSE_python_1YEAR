from config import (
    WATER_BASE_RATE,
    WATER_PER_ACTIVITY_30MIN,
    WATER_HOT_WEATHER_BONUS,
    HOT_WEATHER_THRESHOLD,
    WORKOUT_CALORIE_RATES
)

def calculate_water_norm(weight, activity_minutes, temperature):
    base_water = weight * WATER_BASE_RATE
    activity_bonus = (activity_minutes / 30) * WATER_PER_ACTIVITY_30MIN
    weather_bonus = 0
    if temperature > HOT_WEATHER_THRESHOLD:
        weather_bonus = WATER_HOT_WEATHER_BONUS
    total = base_water + activity_bonus + weather_bonus
    return int(total)

def calculate_calorie_norm(weight, height, age, gender, activity_minutes, custom_goal=None):
    if custom_goal:
        return custom_goal

    bmr = 10 * weight + 6.25 * height - 5 * age

    if gender.lower() == 'male':
        bmr += 5
    else:
        bmr -= 161

    if activity_minutes < 30:
        multiplier = 1.2
    elif activity_minutes < 60:
        multiplier = 1.375
    elif activity_minutes < 90:
        multiplier = 1.55
    else:
        multiplier = 1.725

    total_calories = bmr * multiplier
    return int(total_calories)

def calculate_workout_calories(workout_type, duration_minutes, user_weight):
    base_rate = WORKOUT_CALORIE_RATES.get(
        workout_type.lower(),
        WORKOUT_CALORIE_RATES['default']
    )

    calories = (base_rate * duration_minutes * user_weight) / 70

    return int(calories)
