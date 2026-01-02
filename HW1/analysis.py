import pandas as pd
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

def load_data(file_path):
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def calculate_rolling_stats(df, window=30):
    df = df.copy()
    df = df.sort_values('timestamp')
    df['rolling_mean'] = df['temperature'].rolling(window, center=True).mean()
    df['rolling_std'] = df['temperature'].rolling(window, center=True).std()
    return df


def calculate_seasonal_stats(df):
    seasonal_stats = df.groupby('season')['temperature'].agg([
        'mean', 'std', 'min', 'max', 'count'
    ]).reset_index()
    seasonal_stats.columns = ['season', 'mean', 'std', 'min', 'max', 'count']
    return seasonal_stats


def detect_anomalies(df, seasonal_stats):
    df = df.copy()

    season_bounds = {}
    for _, row in seasonal_stats.iterrows():
        season = row['season']
        mean = row['mean']
        std = row['std']
        season_bounds[season] = {
            'lower': mean - 2 * std,
            'upper': mean + 2 * std,
            'mean': mean,
            'std': std
        }

    def check_anomaly(row):
        bounds = season_bounds.get(row['season'])
        if bounds is None:
            return False
        return row['temperature'] < bounds['lower'] or row['temperature'] > bounds['upper']

    df['is_anomaly'] = df.apply(check_anomaly, axis=1)

    df['season_lower'] = df['season'].map(lambda s: season_bounds[s]['lower'])
    df['season_upper'] = df['season'].map(lambda s: season_bounds[s]['upper'])
    df['season_mean'] = df['season'].map(lambda s: season_bounds[s]['mean'])

    return df


def calculate_trend(df):
    df = df.sort_values('timestamp')

    x = (df['timestamp'] - df['timestamp'].min()).dt.days.values
    y = df['temperature'].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    return slope, intercept, r_value


def calculate_yearly_stats(df):
    df = df.copy()
    df['year'] = df['timestamp'].dt.year

    yearly_stats = df.groupby('year')['temperature'].agg([
        'mean', 'std', 'min', 'max'
    ]).reset_index()

    return yearly_stats


def analyze_city(city_data):
    city_name = city_data['city'].iloc[0]

    city_data = calculate_rolling_stats(city_data)

    seasonal_stats = calculate_seasonal_stats(city_data)

    city_data = detect_anomalies(city_data, seasonal_stats)

    slope, intercept, r_value = calculate_trend(city_data)

    yearly_stats = calculate_yearly_stats(city_data)

    anomaly_count = city_data['is_anomaly'].sum()
    anomaly_percent = (anomaly_count / len(city_data)) * 100
    
    return {
        'city': city_name,
        'data': city_data,
        'seasonal_stats': seasonal_stats,
        'yearly_stats': yearly_stats,
        'trend_slope': slope,
        'trend_slope_yearly': slope * 365,
        'trend_intercept': intercept,
        'trend_r_value': r_value,
        'anomaly_count': anomaly_count,
        'anomaly_percent': anomaly_percent
    }


def _analyze_city_wrapper(args):
    city_name, city_data = args
    return analyze_city(city_data)


def analyze_sequential(df):
    start_time = time.time()

    results = {}
    cities = df['city'].unique()

    for city in cities:
        city_data = df[df['city'] == city].copy()
        results[city] = analyze_city(city_data)

    execution_time = time.time() - start_time
    return results, execution_time


def analyze_parallel(df, max_workers=None):
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    start_time = time.time()

    cities = df['city'].unique()
    city_data_list = [(city, df[df['city'] == city].copy()) for city in cities]

    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = list(executor.map(_analyze_city_wrapper, city_data_list))

    for result in futures:
        results[result['city']] = result

    execution_time = time.time() - start_time
    return results, execution_time


def benchmark_analysis(df, runs=3):
    sequential_times = []
    parallel_times = []

    for _ in range(runs):
        _, seq_time = analyze_sequential(df)
        sequential_times.append(seq_time)

        _, par_time = analyze_parallel(df)
        parallel_times.append(par_time)

    avg_sequential = np.mean(sequential_times)
    avg_parallel = np.mean(parallel_times)
    speedup = avg_sequential / avg_parallel if avg_parallel > 0 else 0

    return {
        'sequential_times': sequential_times,
        'parallel_times': parallel_times,
        'avg_sequential': avg_sequential,
        'avg_parallel': avg_parallel,
        'speedup': speedup,
        'num_cities': len(df['city'].unique()),
        'num_workers': multiprocessing.cpu_count()
    }


def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'


def check_temperature_anomaly(current_temp, seasonal_stats, season):
    season_data = seasonal_stats[seasonal_stats['season'] == season]

    if season_data.empty:
        return 'unknown', 0, 0

    mean = season_data['mean'].values[0]
    std = season_data['std'].values[0]

    lower_bound = mean - 2 * std
    upper_bound = mean + 2 * std

    if current_temp < lower_bound:
        status = 'cold_anomaly'
    elif current_temp > upper_bound:
        status = 'hot_anomaly'
    else:
        status = 'normal'

    return status, lower_bound, upper_bound


def get_descriptive_stats(df):
    stats_df = df.groupby('season')['temperature'].describe()
    stats_df = stats_df.round(2)
    return stats_df


def predict_temperature(city_data, days_ahead=365):
    city_data = city_data.sort_values('timestamp').copy()

    city_data['days'] = (city_data['timestamp'] - city_data['timestamp'].min()).dt.days

    X = city_data[['days']].values
    y = city_data['temperature'].values

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)

    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)

    last_day = city_data['days'].max()
    future_days = np.arange(last_day + 1, last_day + days_ahead + 1).reshape(-1, 1)
    future_pred = model.predict(future_days)

    last_date = city_data['timestamp'].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days_ahead)

    return {
        'model': model,
        'predictions': y_pred,
        'future_predictions': future_pred,
        'future_dates': future_dates,
        'rmse': rmse,
        'r2': r2,
        'slope': model.coef_[0],
        'intercept': model.intercept_
    }


def calculate_city_correlations(df):
    pivot_df = df.pivot_table(
        values='temperature',
        index='timestamp',
        columns='city',
        aggfunc='mean',
        observed=True
    )

    corr = pivot_df.corr()

    return corr


def cluster_cities_by_temperature(df):
    city_stats = df.groupby('city')['temperature'].agg(['mean', 'std']).reset_index()

    cities = city_stats['city'].tolist()
    means = city_stats['mean'].tolist()
    stds = city_stats['std'].tolist()

    return {
        'cities': cities,
        'mean_temps': means,
        'std_temps': stds,
        'stats': city_stats
    }


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'temperature_data.csv')

    if os.path.exists(data_path):
        print("Загрузка данных...")
        df = load_data(data_path)
        print(f"Загружено {len(df)} записей для {df['city'].nunique()} городов")

        print("\nЗапуск бенчмарка...")
        benchmark = benchmark_analysis(df, runs=3)

        print(f"\nРезультаты бенчмарка:")
        print(f"  Последовательный: {benchmark['avg_sequential']} сек")
        print(f"  Параллельный: {benchmark['avg_parallel']} сек")
        print(f"  Ускорение: {benchmark['speedup']}x")
        print(f"  Число ядер: {benchmark['num_workers']}")
    else:
        print(f"Файл не найден: {data_path}")
