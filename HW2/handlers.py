from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import ProfileSetup, FoodLogging, WorkoutLogging
from services import UserService, DiaryService
from formatters import MessageFormatter
import charts
import recommendation_engine

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(MessageFormatter.start_message())

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(MessageFormatter.help_message())

@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileSetup.weight)

@router.message(ProfileSetup.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if weight <= 0:
            await message.reply("Введите корректный вес")
            return

        await state.update_data(weight=weight)
        await message.reply("Введите ваш рост")
        await state.set_state(ProfileSetup.height)
    except ValueError:
        await message.reply("Пожалуйста, введите число")

@router.message(ProfileSetup.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        if height <= 0:
            await message.reply("Введите корректный рост")
            return

        await state.update_data(height=height)
        await message.reply("Введите ваш возраст:")
        await state.set_state(ProfileSetup.age)
    except ValueError:
        await message.reply("Пожалуйста, введите число:")

@router.message(ProfileSetup.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age <= 0 or age > 120:
            await message.reply("Введите корректный возраст")
            return

        await state.update_data(age=age)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Мужской", callback_data="gender_male")],
            [InlineKeyboardButton(text="Женский", callback_data="gender_female")]
        ])
        await message.reply("Выберите ваш пол:", reply_markup=keyboard)
        await state.set_state(ProfileSetup.gender)
    except ValueError:
        await message.reply("Пожалуйста, введите число:")

@router.callback_query(F.data.startswith("gender_"), ProfileSetup.gender)
async def process_gender(callback, state: FSMContext):
    gender = "male" if callback.data == "gender_male" else "female"
    await state.update_data(gender=gender)

    await callback.message.answer("Сколько минут активности у вас в день?")
    await state.set_state(ProfileSetup.activity_minutes)
    await callback.answer()

@router.message(ProfileSetup.activity_minutes)
async def process_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
        if activity < 0:
            await message.reply("Введите корректное значение")
            return

        await state.update_data(activity_minutes=activity)
        await message.reply("В каком городе вы находитесь? На английском")
        await state.set_state(ProfileSetup.city)
    except ValueError:
        await message.reply("Пожалуйста, введите число:")

@router.message(ProfileSetup.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рассчитать автоматически",
                            callback_data="calorie_auto")],
        [InlineKeyboardButton(text="Ввести свою цель",
                            callback_data="calorie_custom")]
    ])

    await message.reply(
        "Хотите указать свою цель по калориям или рассчитать автоматически?",
        reply_markup=keyboard
    )
    await state.set_state(ProfileSetup.custom_calorie_goal)

@router.callback_query(F.data == "calorie_auto", ProfileSetup.custom_calorie_goal)
async def process_auto_calories(callback, state: FSMContext):
    await finalize_profile(callback, state, None)
    await callback.answer()

@router.callback_query(F.data == "calorie_custom", ProfileSetup.custom_calorie_goal)
async def process_custom_calories_prompt(callback, state: FSMContext):
    await callback.message.answer("Введите вашу цель по калориям (ккал/день)")
    await callback.answer()

@router.message(ProfileSetup.custom_calorie_goal)
async def process_custom_calories_value(message: Message, state: FSMContext):
    try:
        custom_goal = int(message.text)
        if custom_goal < 400:
            await message.reply("Введите корректное значение:")
            return

        await finalize_profile(message, state, custom_goal)
    except ValueError:
        await message.reply("Пожалуйста, введите число")

async def finalize_profile(event, state: FSMContext, custom_goal):
    data = await state.get_data()
    user_id = event.from_user.id
    username = event.from_user.username

    result = await UserService.create_profile(
        user_id=user_id,
        username=username,
        weight=data['weight'],
        height=data['height'],
        age=data['age'],
        gender=data['gender'],
        activity_minutes=data['activity_minutes'],
        city=data['city'],
        custom_calorie_goal=custom_goal
    )

    response_text = MessageFormatter.profile_created(
        data['city'],
        result['temperature'],
        result['water_goal'],
        result['calorie_goal']
    )

    if hasattr(event, 'message'):
        await event.message.answer(response_text)
    else:
        await event.reply(response_text)

    await state.clear()

@router.message(Command("log_water"))
async def cmd_log_water(message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("Использование: /log_water <количество мл>")
            return

        amount = int(parts[1])
        if amount <= 0 or amount > 5000:
            await message.reply("Введите корректное количество")
            return

        user_id = message.from_user.id

        user = await UserService.get_user(user_id)
        if not user:
            await message.reply(MessageFormatter.no_profile())
            return

        result = await DiaryService.log_water(user_id, amount)

        response = MessageFormatter.water_logged(
            result['amount'],
            result['logged_water'],
            result['water_goal'],
            result['remaining'],
            result['goal_reached']
        )
        await message.reply(response)
    except ValueError:
        await message.reply("Пожалуйста, введите число")

@router.message(Command("log_food"))
async def cmd_log_food(message: Message, state: FSMContext):
    user = await UserService.get_user(message.from_user.id)
    if not user:
        await message.reply(MessageFormatter.no_profile())
        return

    await message.reply("Введите название продукта")
    await state.set_state(FoodLogging.product_name)

@router.message(FoodLogging.product_name)
async def process_food_name(message: Message, state: FSMContext):
    product_name = message.text.strip()

    food_info = await DiaryService.search_food(product_name)

    if not food_info:
        await message.reply(MessageFormatter.food_not_found(product_name))
        await state.clear()
        return

    await state.update_data(
        original_name=product_name,
        product_name=food_info['name'],
        calories_per_100g=food_info['calories_per_100g'],
        protein_per_100g=food_info.get('protein_per_100g', 0),
        carbs_per_100g=food_info.get('carbs_per_100g', 0),
        fat_per_100g=food_info.get('fat_per_100g', 0)
    )

    response = MessageFormatter.food_nutrition(
        food_info['name'],
        food_info['calories_per_100g']
    )
    await message.reply(response)
    await state.set_state(FoodLogging.grams)

@router.message(FoodLogging.grams)
async def process_food_grams(message: Message, state: FSMContext):
    try:
        grams = float(message.text)
        if grams <= 0 or grams > 10000:
            await message.reply("Введите корректное количество (1-10000 г):")
            return

        data = await state.get_data()
        user_id = message.from_user.id

        calories = (data['calories_per_100g'] * grams) / 100
        protein = (data['protein_per_100g'] * grams) / 100
        carbs = (data['carbs_per_100g'] * grams) / 100
        fat = (data['fat_per_100g'] * grams) / 100

        result = await DiaryService.log_food(
            user_id=user_id,
            product_name=data['product_name'],
            grams=grams,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat
        )

        response = MessageFormatter.food_logged(
            data['original_name'],
            grams,
            calories,
            protein,
            carbs,
            fat,
            result['net_calories'],
            result['calorie_goal'],
            result['remaining'],
            result['over_limit']
        )
        await message.reply(response)

        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите число:")

@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message, state: FSMContext):
    user = await UserService.get_user(message.from_user.id)
    if not user:
        await message.reply(MessageFormatter.no_profile())
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бег", callback_data="workout_бег")],
        [InlineKeyboardButton(text="Ходьба", callback_data="workout_ходьба")],
        [InlineKeyboardButton(text="Плавание", callback_data="workout_плавание")],
        [InlineKeyboardButton(text="Велосипед", callback_data="workout_велосипед")],
        [InlineKeyboardButton(text="Йога", callback_data="workout_йога")],
        [InlineKeyboardButton(text="Силовая", callback_data="workout_силовая")]
    ])

    await message.reply("Выберите тип тренировки:", reply_markup=keyboard)
    await state.set_state(WorkoutLogging.workout_type)

@router.callback_query(F.data.startswith("workout_"), WorkoutLogging.workout_type)
async def process_workout_type(callback, state: FSMContext):
    workout_type = callback.data.replace("workout_", "")
    await state.update_data(workout_type=workout_type)

    await callback.message.answer("Сколько минут длилась тренировка?")
    await state.set_state(WorkoutLogging.duration)
    await callback.answer()

@router.message(WorkoutLogging.duration)
async def process_workout_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        if duration <= 0:
            await message.reply("Введите корректное время")
            return

        data = await state.get_data()
        user_id = message.from_user.id

        result = await DiaryService.log_workout(
            user_id, data['workout_type'], duration
        )

        response = MessageFormatter.workout_logged(
            result['workout_type'],
            result['duration'],
            result['calories_burned'],
            result['extra_water'],
            result['net_calories'],
            result['calorie_goal']
        )
        await message.reply(response)

        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите число:")

@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    user_id = message.from_user.id
    user = await UserService.get_user(user_id)

    if not user:
        await message.reply(MessageFormatter.no_profile())
        return

    progress_data = await DiaryService.get_progress(user_id)
    response = MessageFormatter.progress_report(progress_data)
    await message.reply(response)

@router.message(Command("graphs"))
async def cmd_graphs(message: Message):
    user = await UserService.get_user(message.from_user.id)
    if not user:
        await message.reply(MessageFormatter.no_profile())
        return

    await message.answer(MessageFormatter.generating_graphs())

    graph_image = await charts.generate_progress_graph(
        message.from_user.id,
        days=7
    )

    if graph_image:
        photo = BufferedInputFile(graph_image.getvalue(), filename="progress.png")
        await message.answer_photo(photo, caption=MessageFormatter.graph_caption())
    else:
        await message.reply(MessageFormatter.insufficient_data())

@router.message(Command("recommend"))
async def cmd_recommend(message: Message):
    user = await UserService.get_user(message.from_user.id)
    if not user:
        await message.reply(MessageFormatter.no_profile())
        return

    recommendations = await recommendation_engine.get_recommendations(message.from_user.id)
    formatted = recommendation_engine.format_recommendations(recommendations)

    await message.reply(MessageFormatter.recommendations_header() + formatted)

def setup_handlers(dp):
    dp.include_router(router)
