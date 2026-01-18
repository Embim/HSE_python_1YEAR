from sqlalchemy import Column, BigInteger, String, Float, Integer, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    activity_minutes = Column(Integer, nullable=False)
    city = Column(String(100), nullable=False)
    custom_calorie_goal = Column(Integer)
    water_goal = Column(Integer, nullable=False)
    calorie_goal = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female')", name='check_gender'),
    )

class DailyLog(Base):
    __tablename__ = 'daily_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    log_date = Column(Date, nullable=False)
    logged_water = Column(Integer, default=0)
    logged_calories = Column(Integer, default=0)
    burned_calories = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

class WaterLog(Base):
    __tablename__ = 'water_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    amount = Column(Integer, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)

class FoodLog(Base):
    __tablename__ = 'food_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product_name = Column(String(255), nullable=False)
    grams = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    logged_at = Column(DateTime, default=datetime.utcnow)

class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    workout_type = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    calories_burned = Column(Integer, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
