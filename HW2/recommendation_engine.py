from datetime import date
from repositories import UserRepository, DiaryRepository
from config import (
    RECOMMENDATION_THRESHOLDS,
    LOW_CALORIE_FOODS,
    WORKOUT_RECOMMENDATIONS,
    WATER_TIPS
)

def _get_food_recommendations(calorie_deficit):
    threshold_very_low = RECOMMENDATION_THRESHOLDS["calorie_deficit_very_low"]
    threshold_low = RECOMMENDATION_THRESHOLDS["calorie_deficit_low"]

    if calorie_deficit < 0:
        return {
            "foods": [f for f in LOW_CALORIE_FOODS if f["calories"] < 25],
            "message": "Превышение калорий! Рекомендуем овощи:"
        }
    elif calorie_deficit < threshold_very_low:
        return {
            "foods": LOW_CALORIE_FOODS[:4],
            "message": "Близки к норме! Низкокалорийные продукты:"
        }
    elif calorie_deficit < threshold_low:
        return {
            "foods": LOW_CALORIE_FOODS[:5],
            "message": "Умеренный дефицит. Здоровые продукты:"
        }
    else:
        return {
            "foods": LOW_CALORIE_FOODS,
            "message": "Большой дефицит. Полезные перекусы:"
        }

def _get_workout_recommendations(calorie_deficit):
    threshold_high = RECOMMENDATION_THRESHOLDS["calorie_deficit_high"]
    threshold_surplus_small = RECOMMENDATION_THRESHOLDS["calorie_surplus_small"]
    threshold_surplus_moderate = RECOMMENDATION_THRESHOLDS["calorie_surplus_moderate"]

    if calorie_deficit < 0:
        surplus_amount = abs(calorie_deficit)
        if surplus_amount > threshold_surplus_moderate:
            return {
                "workouts": WORKOUT_RECOMMENDATIONS["intense"],
                "workout_message": "Значительное превышение. Интенсивная тренировка:"
            }
        elif surplus_amount > threshold_surplus_small:
            return {
                "workouts": WORKOUT_RECOMMENDATIONS["moderate"],
                "workout_message": "Умеренное превышение. Активная тренировка:"
            }
        else:
            return {
                "workouts": WORKOUT_RECOMMENDATIONS["light"],
                "workout_message": "Небольшое превышение. Легкая активность:"
            }
    elif calorie_deficit > threshold_high:
        return {
            "workouts": WORKOUT_RECOMMENDATIONS["light"],
            "workout_message": "Большой дефицит. Восстановительная активность:"
        }
    else:
        return {
            "workouts": WORKOUT_RECOMMENDATIONS["moderate"],
            "workout_message": "Норма. Поддерживающая тренировка:"
        }

def _get_water_tips(water_deficit):
    threshold = RECOMMENDATION_THRESHOLDS["water_deficit_threshold"]

    if water_deficit > threshold:
        return WATER_TIPS
    return []

async def get_recommendations(user_id):
    user = await UserRepository.get_by_id(user_id)
    progress = await DiaryRepository.get_progress(user_id, date.today())

    net_calories = progress.logged_calories - progress.burned_calories
    calorie_deficit = user.calorie_goal - net_calories
    water_deficit = user.water_goal - progress.logged_water

    recommendations = {
        "foods": [],
        "workouts": [],
        "water_tips": []
    }

    food_rec = _get_food_recommendations(calorie_deficit)
    recommendations.update(food_rec)

    workout_rec = _get_workout_recommendations(calorie_deficit)
    recommendations.update(workout_rec)

    recommendations["water_tips"] = _get_water_tips(water_deficit)

    return recommendations

def format_recommendations(recommendations):
    message_parts = []

    if "message" in recommendations:
        message_parts.append(f"{recommendations['message']}")
        for food in recommendations["foods"]:
            message_parts.append(
                f"  - {food['name']} - {food['calories']} ккал/100г\n"
                f"    {food['benefit']}"
            )

    message_parts.append("")

    if "workout_message" in recommendations:
        message_parts.append(f"{recommendations['workout_message']}")
        for workout in recommendations["workouts"]:
            message_parts.append(
                f"  - {workout['name']} ({workout['duration']} мин)\n"
                f"    {workout['benefit']}"
            )

    if recommendations.get("water_tips"):
        message_parts.append("")
        message_parts.append("Советы по питью воды:")
        for tip in recommendations["water_tips"]:
            message_parts.append(f"  - {tip}")

    return "\n".join(message_parts)
