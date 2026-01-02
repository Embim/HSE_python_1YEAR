import requests
import aiohttp
import asyncio
import time

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherAPIError(Exception):
    pass

class InvalidAPIKeyError(WeatherAPIError):
    pass

def get_current_weather_sync(city, api_key):
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        if response.status_code == 401:
            raise InvalidAPIKeyError(
                "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
            )

        if response.status_code != 200:
            error_msg = data.get('message', 'Unknown error')
            raise WeatherAPIError(f"API Error: {error_msg}")

        return {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed'],
            'clouds': data['clouds']['all'],
            'cod': data['cod']
        }

    except requests.RequestException as e:
        raise WeatherAPIError(f"Network error: {str(e)}")


def get_weather_multiple_cities_sync(cities, api_key):
    start_time = time.time()
    results = []

    for city in cities:
        try:
            weather = get_current_weather_sync(city, api_key)
            results.append(weather)
        except WeatherAPIError as e:
            results.append({'city': city, 'error': str(e)})

    execution_time = time.time() - start_time
    return results, execution_time

async def get_current_weather_async(city, api_key, session=None):
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        async with session.get(BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
            data = await response.json()

            if response.status == 401:
                raise InvalidAPIKeyError(
                    "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
                )

            if response.status != 200:
                error_msg = data.get('message', 'Unknown error')
                raise WeatherAPIError(f"API Error: {error_msg}")

            return {
                'city': data['name'],
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'cod': data['cod']
            }

    except aiohttp.ClientError as e:
        raise WeatherAPIError(f"Network error: {str(e)}")
    finally:
        if close_session:
            await session.close()


async def get_weather_multiple_cities_async(cities, api_key):
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [
            get_current_weather_async(city, api_key, session)
            for city in cities
        ]

        results = []
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for city, response in zip(cities, responses):
            if isinstance(response, Exception):
                results.append({'city': city, 'error': str(response)})
            else:
                results.append(response)

    execution_time = time.time() - start_time
    return results, execution_time

def run_async_weather(cities, api_key):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(get_weather_multiple_cities_async(cities, api_key))

def benchmark_api_methods(cities, api_key, runs=3):
    sync_times = []
    async_times = []

    for _ in range(runs):
        _, sync_time = get_weather_multiple_cities_sync(cities, api_key)
        sync_times.append(sync_time)

        time.sleep(0.5)

        _, async_time = run_async_weather(cities, api_key)
        async_times.append(async_time)

        time.sleep(0.5)

    avg_sync = sum(sync_times) / len(sync_times)
    avg_async = sum(async_times) / len(async_times)
    speedup = avg_sync / avg_async if avg_async > 0 else 0

    return {
        'sync_times': sync_times,
        'async_times': async_times,
        'avg_sync': avg_sync,
        'avg_async': avg_async,
        'speedup': speedup,
        'num_cities': len(cities),
        'conclusion': _get_conclusion(speedup, len(cities))
    }


def _get_conclusion(speedup, num_cities):
    if num_cities == 1:
        return (
            "Для одного города разница минимальна. "
            "Синхронный метод проще в использовании."
        )
    elif speedup > 1.5:
        return (
            f"Асинхронный метод быстрее в {speedup} раз. "
            f"Для {num_cities} городов рекомендуется использовать асинхронный подход."
        )
    else:
        return (
            "Разница в производительности незначительна. "
            "Выбор метода зависит от архитектуры приложения."
        )


def validate_api_key(api_key):
    if not api_key or len(api_key) < 10:
        return False, "API ключ слишком короткий"

    try:
        get_current_weather_sync("London", api_key)
        return True, "API ключ валиден"
    except InvalidAPIKeyError:
        return False, "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
    except WeatherAPIError as e:
        return False, f"Ошибка проверки ключа: {str(e)}"

if __name__ == "__main__":
    print("Модуль weather_api.py загружен успешно.")
    print("\nДоступные функции:")
    print("  - get_current_weather_sync(city, api_key)")
    print("  - get_current_weather_async(city, api_key)")
    print("  - get_weather_multiple_cities_sync(cities, api_key)")
    print("  - get_weather_multiple_cities_async(cities, api_key)")
    print("  - benchmark_api_methods(cities, api_key)")
    print("  - validate_api_key(api_key)")
