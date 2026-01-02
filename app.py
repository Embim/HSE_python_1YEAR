import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

from analysis import (
    load_data, analyze_city, analyze_sequential, analyze_parallel,
    benchmark_analysis, get_current_season, check_temperature_anomaly,
    get_descriptive_stats, calculate_seasonal_stats, predict_temperature,
    calculate_city_correlations, cluster_cities_by_temperature
)
from weather_api import (
    get_current_weather_sync, validate_api_key,
    InvalidAPIKeyError, WeatherAPIError,
    get_weather_multiple_cities_sync, run_async_weather, benchmark_api_methods
)

st.set_page_config(
    page_title="Temperature Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Анализ температурных данных")

with st.sidebar:
    st.header("Навигация")
    page = st.radio("Выберите страницу", ["Анализ данных", "API Погода"])

    st.header("Загрузка данных")

    uploaded_file = st.file_uploader(
        "Загрузите CSV файл с историческими данными",
        type="csv",
        help="Формат: city, timestamp, temperature, season"
    )

    default_file_path = os.path.join(os.path.dirname(__file__), 'temperature_data.csv')
    use_default = st.checkbox(
        "Использовать файл по умолчанию",
        value=os.path.exists(default_file_path) and uploaded_file is None
    )

    st.header("OpenWeatherMap API")

    api_key = st.text_input(
        "API ключ",
        type="password",
        help="Получите бесплатный ключ на openweathermap.org"
    )

    if api_key:
        if st.button("Проверить ключ"):
            with st.spinner("Проверка..."):
                is_valid, message = validate_api_key(api_key)
                if is_valid:
                    st.success(message)
                else:
                    st.error(message)

def load_cached_data(file_content=None, file_path=None):
    if file_content is not None:
        return pd.read_csv(file_content)
    elif file_path and os.path.exists(file_path):
        return load_data(file_path)
    return None

df = None
if uploaded_file is not None:
    df = load_cached_data(file_content=uploaded_file)
    assert df is not None
    df['timestamp'] = pd.to_datetime(df['timestamp'])
elif use_default and os.path.exists(default_file_path):
    df = load_cached_data(file_path=default_file_path)

if df is None:
    st.warning("Пж, загрузите CSV файл.")
    st.stop()

assert df is not None
cities = sorted(df['city'].unique().tolist())

if page == "Анализ данных":
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_city = st.selectbox(
            "Выберите город",
            cities,
            index=0
        )

    city_data = df[df['city'] == selected_city].copy()

    with st.spinner(f"Анализ данных для {selected_city}..."):
        analysis_result = analyze_city(city_data)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Описательная статистика",
        "Временной ряд",
        "Сезонные профили",
        "Тренды",
        "ML и Корреляции",
        "Бенчмарки"
    ])

    with tab1:
        st.header(f"Описательная статистика: {selected_city}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Статистика по сезонам")
            seasonal_stats = analysis_result['seasonal_stats']
            seasonal_stats_display = seasonal_stats.copy()
            seasonal_stats_display.columns = ['Сезон', 'Среднее', 'Ст. откл.', 'Мин', 'Макс', 'Кол-во']
            seasonal_stats_display = seasonal_stats_display.round(2)
            st.dataframe(seasonal_stats_display, width='stretch')

            st.subheader("Общая статистика")
            overall_stats = city_data['temperature'].describe().round(2)
            st.dataframe(overall_stats)

        with col2:
            st.subheader("Распределение температур")
            fig_hist = px.histogram(
                city_data,
                x='temperature',
                color='season',
                title="Распределение температур"
            )
            st.plotly_chart(fig_hist, width='stretch')

        st.subheader("Аномалии")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего аномалий", int(analysis_result['anomaly_count']))
        with col2:
            st.metric("Процент аномалий", f"{analysis_result['anomaly_percent']}%")
        with col3:
            st.metric("Всего наблюдений", len(city_data))

    with tab2:
        st.header(f"Временной ряд температур: {selected_city}")

        data = analysis_result['data']

        fig_ts = go.Figure()

        fig_ts.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data['temperature'],
            mode='lines',
            name='Температура'
        ))

        fig_ts.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data['rolling_mean'],
            mode='lines',
            name='Среднее'
        ))

        anomalies = data[data['is_anomaly'] == True]
        fig_ts.add_trace(go.Scatter(
            x=anomalies['timestamp'],
            y=anomalies['temperature'],
            mode='markers',
            name='Аномалии',
            marker=dict(color='red')
        ))

        fig_ts.update_layout(
            title="Температура по времени",
            xaxis_title="Дата",
            yaxis_title="Температура (C)"
        )

        st.plotly_chart(fig_ts, width='stretch')

        if st.checkbox("Показать таблицу аномалий"):
            st.subheader(f"Список аномалий ({len(anomalies)} записей)")
            anomalies_display = anomalies[['timestamp', 'temperature', 'season', 'season_mean', 'season_lower', 'season_upper']].copy()
            anomalies_display.columns = ['Дата', 'Температура', 'Сезон', 'Сезонное среднее', 'Нижняя граница', 'Верхняя граница']
            anomalies_display = anomalies_display.round(2)
            st.dataframe(anomalies_display, width='stretch')

    with tab3:
        st.header(f"Сезонные профили: {selected_city}")

        col1, col2 = st.columns(2)

        with col1:
            fig_box = px.box(
                city_data,
                x='season',
                y='temperature',
                title="Температура по сезонам"
            )
            st.plotly_chart(fig_box, width='stretch')

        with col2:
            fig_violin = px.violin(
                city_data,
                x='season',
                y='temperature',
                box=True,
                title="Распределение по сезонам"
            )
            st.plotly_chart(fig_violin, width='stretch')

        st.subheader("Средние температуры")

        seasonal_stats = analysis_result['seasonal_stats']

        fig_bounds = go.Figure()
        fig_bounds.add_trace(go.Bar(
            x=seasonal_stats['season'],
            y=seasonal_stats['mean'],
            name='Средняя температура',
            error_y=dict(
                type='data',
                array=seasonal_stats['std'] * 2
            )
        ))

        fig_bounds.update_layout(title="Средняя температура по сезонам")
        st.plotly_chart(fig_bounds, width='stretch')

        st.subheader("Границы нормы по сезонам")
        bounds_df = seasonal_stats[['season', 'mean', 'std']].copy()
        bounds_df['lower_bound'] = bounds_df['mean'] - 2 * bounds_df['std']
        bounds_df['upper_bound'] = bounds_df['mean'] + 2 * bounds_df['std']
        bounds_df.columns = ['Сезон', 'Среднее', 'Ст. откл.', 'Нижняя граница (-2sigma)', 'Верхняя граница (+2sigma)']
        bounds_df = bounds_df.round(2)
        st.dataframe(bounds_df, width='stretch')

    with tab4:
        st.header(f"Тренды: {selected_city}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Тренд (C/год)", f"{analysis_result['trend_slope_yearly']}")
        with col2:
            trend_direction = "Потепление" if analysis_result['trend_slope_yearly'] > 0 else "Похолодание"
            st.metric("Направление", trend_direction)

        data_with_analysis = analysis_result['data'].copy()
        data_with_analysis['days'] = (data_with_analysis['timestamp'] - data_with_analysis['timestamp'].min()).dt.days
        data_with_analysis['trend'] = (
            analysis_result['trend_intercept'] +
            analysis_result['trend_slope'] * data_with_analysis['days']
        )

        fig_trend = go.Figure()

        fig_trend.add_trace(go.Scatter(
            x=data_with_analysis['timestamp'],
            y=data_with_analysis['temperature'],
            mode='lines',
            name='Температура'
        ))

        fig_trend.add_trace(go.Scatter(
            x=data_with_analysis['timestamp'],
            y=data_with_analysis['trend'],
            mode='lines',
            name='Тренд',
            line=dict(color='red', dash='dash')
        ))

        fig_trend.update_layout(title="Температура и тренд")
        st.plotly_chart(fig_trend, width='stretch')

        st.subheader("По годам")

        yearly_stats = analysis_result['yearly_stats']

        fig_yearly = px.bar(
            yearly_stats,
            x='year',
            y='mean',
            title="Средняя температура по годам"
        )

        st.plotly_chart(fig_yearly, width='stretch')

    with tab5:
        st.header(f"ML и Корреляции")

        st.subheader("Прогноз температуры")

        ml_result = predict_temperature(city_data, days_ahead=365)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("RMSE", f"{ml_result['rmse']}C")
        with col2:
            st.metric("R2", f"{ml_result['r2']}")

        city_data_sorted = city_data.sort_values('timestamp').copy()
        city_data_sorted['prediction'] = ml_result['predictions']

        fig_ml = go.Figure()

        fig_ml.add_trace(go.Scatter(
            x=city_data_sorted['timestamp'],
            y=city_data_sorted['temperature'],
            mode='lines',
            name='Данные'
        ))

        fig_ml.add_trace(go.Scatter(
            x=city_data_sorted['timestamp'],
            y=city_data_sorted['prediction'],
            mode='lines',
            name='Модель'
        ))

        fig_ml.add_trace(go.Scatter(
            x=ml_result['future_dates'],
            y=ml_result['future_predictions'],
            mode='lines',
            name='Прогноз',
            line=dict(dash='dash')
        ))

        fig_ml.update_layout(title="Прогноз температуры")
        st.plotly_chart(fig_ml, width='stretch')

         
        st.subheader("Корреляции")

        corr_matrix = calculate_city_correlations(df)

        fig_corr = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu'
        ))

        fig_corr.update_layout(title="Корреляция между городами")
        st.plotly_chart(fig_corr, width='stretch')

         
        st.subheader("Кластеризация городов")

        cluster_data = cluster_cities_by_temperature(df)

        fig_cluster = go.Figure()
        fig_cluster.add_trace(go.Scatter(
            x=cluster_data['mean_temps'],
            y=cluster_data['std_temps'],
            mode='markers+text',
            text=cluster_data['cities'],
            textposition='top center'
        ))

        fig_cluster.update_layout(
            title="Города по температуре",
            xaxis_title="Средняя T",
            yaxis_title="Ст. откл."
        )

        st.plotly_chart(fig_cluster, width='stretch')

    with tab6:
        st.header("Бэнчамарки: Сравнение методов")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Распараллеливание анализа")

            if st.button("Запустить бенчмарк анализа", key="bench_analysis"):
                with st.spinner("Выполнение бенчмарка (может занять несколько секунд)..."):
                    benchmark = benchmark_analysis(df, runs=3)

                    st.success("Бенчмарк завершён!")

                    st.metric("Последовательный", f"{benchmark['avg_sequential']} сек")
                    st.metric("Параллельный", f"{benchmark['avg_parallel']} сек")
                    st.metric("Ускорение", f"{benchmark['speedup']}x")

                    fig_bench = go.Figure(data=[
                        go.Bar(name='Последовательный', x=['Время выполнения'], y=[benchmark['avg_sequential']]),
                        go.Bar(name='Параллельный', x=['Время выполнения'], y=[benchmark['avg_parallel']])
                    ])
                    fig_bench.update_layout(title="Сравнение времени выполнения")
                    st.plotly_chart(fig_bench, width='stretch')

                    if benchmark['speedup'] > 1.2:
                        st.info(f"Параллельный метод быстрее в {benchmark['speedup']} раза. "
                               f"Рекомендуется для обработки больших объёмов данных.")
                    else:
                        st.info("Разница в производительности незначительна для данного объёма данных.")

        with col2:
            st.subheader("Синхронный vs Асинхронный API")

            if not api_key:
                st.warning("Введите API ключ для запуска эксперимента")
            else:
                test_cities = st.multiselect(
                    "Выберите города для теста",
                    cities,
                    default=cities[:5] if len(cities) >= 5 else cities
                )

                if st.button("Запустить бенчмарк API", key="bench_api") and test_cities:
                    with st.spinner("Выполнение запросов..."):
                        try:
                            api_benchmark = benchmark_api_methods(test_cities, api_key, runs=2)

                            st.success("Бенчмарк API завершён!")

                            st.metric("Синхронный", f"{api_benchmark['avg_sync']} сек")
                            st.metric("Асинхронный", f"{api_benchmark['avg_async']} сек")
                            st.metric("Ускорение", f"{api_benchmark['speedup']}x")

                            fig_api = go.Figure(data=[
                                go.Bar(name='Синхронный', x=['Время выполнения'], y=[api_benchmark['avg_sync']]),
                                go.Bar(name='Асинхронный', x=['Время выполнения'], y=[api_benchmark['avg_async']])
                            ])
                            fig_api.update_layout(title=f"API: Сравнение для {len(test_cities)} городов")
                            st.plotly_chart(fig_api, width='stretch')

                            st.info(api_benchmark['conclusion'])

                        except InvalidAPIKeyError:
                            st.error("Невалидный API ключ!")
                        except Exception as e:
                            st.error(f"Ошибка: {str(e)}")

elif page == "API Погода":
    st.header("Текущая погода")

    selected_city = st.selectbox(
        "Выберите город",
        cities,
        index=0
    )

    city_data = df[df['city'] == selected_city].copy()

    with st.spinner(f"Анализ данных для {selected_city}..."):
        analysis_result = analyze_city(city_data)

    if not api_key:
        st.info("Введите API ключ OpenWeatherMap в боковой панели для получения текущей погоды.")
    else:
        if st.button("Получить текущую погоду", key="get_weather"):
            with st.spinner(f"Получение погоды для {selected_city}..."):
                try:
                    weather = get_current_weather_sync(selected_city, api_key)

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Температура", f"{weather['temperature']}C")
                    with col2:
                        st.metric("Ощущается как", f"{weather['feels_like']}C")
                    with col3:
                        st.metric("Влажность", f"{weather['humidity']}%")
                    with col4:
                        st.metric("Ветер", f"{weather['wind_speed']} м/с")

                    st.write(f"**Описание:** {weather['description'].capitalize()}")

                    st.subheader("Сравнение с историческими данными")

                    current_season = get_current_season()
                    seasonal_stats = analysis_result['seasonal_stats']

                    status, lower, upper = check_temperature_anomaly(
                        weather['temperature'],
                        seasonal_stats,
                        current_season
                    )

                    season_names = {
                        'winter': 'Зима',
                        'spring': 'Весна',
                        'summer': 'Лето',
                        'autumn': 'Осень'
                    }

                    season_data = seasonal_stats[seasonal_stats['season'] == current_season]
                    if not season_data.empty:
                        mean_temp = season_data['mean'].values[0]

                        fig_compare = go.Figure()

                        fig_compare.add_trace(go.Bar(
                            x=['Минимум', 'Нижняя граница', 'Среднее', 'Текущая', 'Верхняя граница', 'Максимум'],
                            y=[season_data['min'].values[0], lower, mean_temp, weather['temperature'], upper, season_data['max'].values[0]]
                        ))

                        fig_compare.update_layout(
                            title=f"Текущая температура vs исторические данные ({season_names[current_season]})"
                        )

                        st.plotly_chart(fig_compare, width='stretch')

                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Текущий сезон:** {season_names.get(current_season, current_season)}")
                            st.write(f"**Историческая норма:** {lower}C - {upper}C")
                        with col2:
                            if status == 'normal':
                                st.success("Температура в пределах нормы")
                            elif status == 'cold_anomaly':
                                st.error(f"Аномально холодно (ниже {lower}C)")
                            elif status == 'hot_anomaly':
                                st.error(f"Аномально тепло (выше {upper}C)")
                            else:
                                st.warning("Не удалось определить статус")


                except InvalidAPIKeyError:
                    st.error("Невалидный API ключ. Проверьте правильность ключа.")
                except WeatherAPIError as e:
                    st.error(f"Ошибка API: {str(e)}")
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
