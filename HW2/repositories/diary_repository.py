from datetime import date, timedelta
from sqlalchemy import select, update
from database import get_session
from models import DailyLog, WaterLog, FoodLog, WorkoutLog
from dto import DailyProgressDTO, HistoricalDataDTO

class DiaryRepository:
    @staticmethod
    async def get_or_create_daily_log_with_session(session, user_id, log_date):
        result = await session.execute(
            select(DailyLog).where(
                DailyLog.user_id == user_id,
                DailyLog.log_date == log_date
            )
        )
        daily_log = result.scalar_one_or_none()

        if not daily_log:
            daily_log = DailyLog(
                user_id=user_id,
                log_date=log_date,
                logged_water=0,
                logged_calories=0,
                burned_calories=0
            )
            session.add(daily_log)
            await session.flush()

        return DailyProgressDTO(
            logged_water=daily_log.logged_water,
            logged_calories=daily_log.logged_calories,
            burned_calories=daily_log.burned_calories
        )

    @staticmethod
    async def get_or_create_daily_log(user_id, log_date):
        async with get_session() as session:
            async with session.begin():
                return await DiaryRepository.get_or_create_daily_log_with_session(
                    session, user_id, log_date
                )

    @staticmethod
    async def log_water(user_id, amount):
        async with get_session() as session:
            async with session.begin():
                water_log = WaterLog(user_id=user_id, amount=amount)
                session.add(water_log)

                today = date.today()
                await DiaryRepository.get_or_create_daily_log_with_session(
                    session, user_id, today
                )

                await session.execute(
                    update(DailyLog)
                    .where(DailyLog.user_id == user_id, DailyLog.log_date == today)
                    .values(logged_water=DailyLog.logged_water + amount)
                )

    @staticmethod
    async def log_food(user_id, product_name, grams, calories,
                      protein=None, carbs=None, fat=None):
        async with get_session() as session:
            async with session.begin():
                food_log = FoodLog(
                    user_id=user_id,
                    product_name=product_name,
                    grams=grams,
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fat=fat
                )
                session.add(food_log)

                today = date.today()
                await DiaryRepository.get_or_create_daily_log_with_session(
                    session, user_id, today
                )

                await session.execute(
                    update(DailyLog)
                    .where(DailyLog.user_id == user_id, DailyLog.log_date == today)
                    .values(logged_calories=DailyLog.logged_calories + int(calories))
                )

    @staticmethod
    async def log_workout(user_id, workout_type, duration_minutes, calories_burned):
        async with get_session() as session:
            async with session.begin():
                workout_log = WorkoutLog(
                    user_id=user_id,
                    workout_type=workout_type,
                    duration_minutes=duration_minutes,
                    calories_burned=calories_burned
                )
                session.add(workout_log)

                today = date.today()
                await DiaryRepository.get_or_create_daily_log_with_session(
                    session, user_id, today
                )

                await session.execute(
                    update(DailyLog)
                    .where(DailyLog.user_id == user_id, DailyLog.log_date == today)
                    .values(burned_calories=DailyLog.burned_calories + calories_burned)
                )

    @staticmethod
    async def get_progress(user_id, log_date):
        return await DiaryRepository.get_or_create_daily_log(user_id, log_date)

    @staticmethod
    async def get_historical_data(user_id, days=7):
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

        async with get_session() as session:
            result = await session.execute(
                select(DailyLog).where(
                    DailyLog.user_id == user_id,
                    DailyLog.log_date >= start_date,
                    DailyLog.log_date <= end_date
                ).order_by(DailyLog.log_date)
            )
            logs = result.scalars().all()

            row_dict = {log.log_date: log for log in logs}

            result = []
            current_date = start_date

            while current_date <= end_date:
                if current_date in row_dict:
                    log_entry = row_dict[current_date]
                    result.append(HistoricalDataDTO(
                        log_date=log_entry.log_date,
                        logged_water=log_entry.logged_water,
                        logged_calories=log_entry.logged_calories,
                        burned_calories=log_entry.burned_calories
                    ))
                else:
                    result.append(HistoricalDataDTO(
                        log_date=current_date,
                        logged_water=0,
                        logged_calories=0,
                        burned_calories=0
                    ))
                current_date += timedelta(days=1)

            return result
