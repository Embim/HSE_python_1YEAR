import altair as alt
import pandas as pd
from io import BytesIO
from repositories import UserRepository, DiaryRepository
from logger import log

async def generate_progress_graph(user_id, days=7):
    historical_data = await DiaryRepository.get_historical_data(user_id, days)
    user = await UserRepository.get_by_id(user_id)

    if not historical_data:
        return None

    data_rows = []
    for record in historical_data:
        date_str = record.log_date.strftime('%d.%m')
        net_calories = record.logged_calories - record.burned_calories

        data_rows.append({
            'date': date_str,
            'water_logged': record.logged_water,
            'water_goal': user.water_goal,
            'calories_net': net_calories,
            'calorie_goal': user.calorie_goal
        })

    df = pd.DataFrame(data_rows)

    water_line = alt.Chart(df).mark_line(point=True, color='#2196F3').encode(
        x=alt.X('date:N', title='Дата', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('water_logged:Q', title='Вода (мл)'),
        tooltip=['date', 'water_logged']
    )

    water_goal_line = alt.Chart(df).mark_line(strokeDash=[5, 5], color='#FF9800').encode(
        x='date:N',
        y='water_goal:Q',
        tooltip=['date', 'water_goal']
    )

    water_chart = (water_line + water_goal_line).properties(
        title='Потребление воды',
        width=600,
        height=250
    )

    calorie_line = alt.Chart(df).mark_line(point=True, color='#4CAF50').encode(
        x=alt.X('date:N', title='Дата', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('calories_net:Q', title='Калории (ккал)'),
        tooltip=['date', 'calories_net']
    )

    calorie_goal_line = alt.Chart(df).mark_line(strokeDash=[5, 5], color='#FF9800').encode(
        x='date:N',
        y='calorie_goal:Q',
        tooltip=['date', 'calorie_goal']
    )

    calorie_chart = (calorie_line + calorie_goal_line).properties(
        title='Баланс калорий',
        width=600,
        height=250
    )

    final_chart = alt.vconcat(
        water_chart,
        calorie_chart
    ).properties(
        title='Прогресс за последние дни'
    ).configure_title(
        fontSize=16,
        anchor='start'
    )

    try:
        buf = BytesIO()
        final_chart.save(buf, format='png', scale_factor=2.0)
        buf.seek(0)
        return buf
    except Exception as e:
        log.error(f"Ошибка при генерации графика: {e}")
        return None
