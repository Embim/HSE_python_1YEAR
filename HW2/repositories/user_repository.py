from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from database import get_session
from models import User
from dto import UserDTO

class UserRepository:
    @staticmethod
    async def create_or_update(user_id, username, weight, height, age, gender,
                               activity_minutes, city, water_goal, calorie_goal,
                               custom_calorie_goal=None):
        async with get_session() as session:
            async with session.begin():
                stmt = insert(User).values(
                    user_id=user_id,
                    username=username,
                    weight=weight,
                    height=height,
                    age=age,
                    gender=gender,
                    activity_minutes=activity_minutes,
                    city=city,
                    water_goal=water_goal,
                    calorie_goal=calorie_goal,
                    custom_calorie_goal=custom_calorie_goal
                )

                stmt = stmt.on_conflict_do_update(
                    index_elements=['user_id'],
                    set_=dict(
                        username=username,
                        weight=weight,
                        height=height,
                        age=age,
                        gender=gender,
                        activity_minutes=activity_minutes,
                        city=city,
                        water_goal=water_goal,
                        calorie_goal=calorie_goal,
                        custom_calorie_goal=custom_calorie_goal
                    )
                )

                await session.execute(stmt)

    @staticmethod
    async def get_by_id(user_id) -> UserDTO:
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                return UserDTO(
                    user_id=user.user_id,
                    username=user.username,
                    weight=user.weight,
                    height=user.height,
                    age=user.age,
                    gender=user.gender,
                    activity_minutes=user.activity_minutes,
                    city=user.city,
                    water_goal=user.water_goal,
                    calorie_goal=user.calorie_goal,
                    custom_calorie_goal=user.custom_calorie_goal
                )
            return None
