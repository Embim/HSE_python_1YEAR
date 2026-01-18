import aiohttp
import json
from config import OPENWEATHER_API_KEY, OPENROUTER_API_KEY
from logger import log

API_TIMEOUT = 10
MAX_RETRIES = 2

async def get_temperature(city):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'
    }

    for attempt in range(MAX_RETRIES):
        try:
            timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        temp = data['main']['temp']
                        return temp
                    else:
                        log.warning(f"API погоды вернул статус {response.status} для города {city}")
                        return None
        except aiohttp.ClientError as e:
            log.error(f"Сетевая ошибка при запросе погоды (попытка {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt == MAX_RETRIES - 1:
                return None
        except Exception as e:
            log.error(f"Неожиданная ошибка при запросе погоды: {e}")
            return None

async def search_food_nutrition(food_name):
    if not OPENROUTER_API_KEY:
        log.warning("OpenRouter API ключ не настроен")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json'
    }

    prompt = f"""Provide nutritional information for: {food_name}

Return ONLY a JSON object with this exact format (no additional text):
{{"calories": <number>, "protein": <number>, "carbs": <number>, "fat": <number>}}

All values are per 100g. Use average values for this food item."""

    payload = {
        'model': 'nvidia/nemotron-3-nano-30b-a3b:free', # взял больше потому что маленькая модель давала странные ответы
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content'].strip()

                    content = content.replace('```json', '').replace('```', '').strip()

                    nutrition_data = json.loads(content)

                    return {
                        'name': food_name,
                        'calories_per_100g': float(nutrition_data.get('calories', 0)),
                        'protein_per_100g': float(nutrition_data.get('protein', 0)),
                        'carbs_per_100g': float(nutrition_data.get('carbs', 0)),
                        'fat_per_100g': float(nutrition_data.get('fat', 0))
                    }
                else:
                    log.warning(f"OpenRouter API вернул статус {response.status}")
                    return None
    except json.JSONDecodeError as e:
        log.error(f"Ошибка парсинга JSON {e}")
        return None
    except aiohttp.ClientError as e:
        log.error(f"Сетевая ошибка при поиске продукта {e}")
        return None
    except Exception as e:
        log.error(f"Неожиданная ошибка при поиске продукта {e}")
        return None
    
#Архаика, пытался переводить названия продуктов, но потом отказался от этой идеи, потому что openfoodfacts криво работает )
# async def translate_text(text, target_lang='en'):
#     if not OPENROUTER_API_KEY:
#         log.warning("OpenRouter API ключ не настроен")
#         return text

#     url = "https://openrouter.ai/api/v1/chat/completions"
#     headers = {
#         'Authorization': f'Bearer {OPENROUTER_API_KEY}',
#         'Content-Type': 'application/json'
#     }
#     prompt = f"Translate this food name to English, return only the translated word: {text}"
#     payload = {
#         'model': 'nvidia/nemotron-nano-9b-v2:free',
#         'messages': [
#             {
#                 'role': 'user',
#                 'content': prompt
#             }
#         ]
#     }

#     try:
#         timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
#         async with aiohttp.ClientSession(timeout=timeout) as session:
#             async with session.post(url, headers=headers, json=payload) as response:
#                 if response.status == 200:
#                     data = await response.json()
#                     translated = data['choices'][0]['message']['content'].strip()
#                     return translated
#                 else:
#                     log.warning(f"API перевода вернул статус {response.status}")
#                     return text
#     except aiohttp.ClientError as e:
#         log.error(f"Сетевая ошибка при переводе: {e}")
#         return text
#     except Exception as e:
#         log.error(f"Неожиданная ошибка при переводе: {e}")
#         return text
# Функция может пригодиться для определения, нужно ли переводить текст, магия кодировки символов
# def is_cyrillic(text):
#     return any('\u0400' <= char <= '\u04FF' for char in text)
