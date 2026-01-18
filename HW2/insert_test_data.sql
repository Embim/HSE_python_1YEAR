-- Вставка тестовых данных для графиков (последние 7 дней)

-- Удаляем старые данные если есть
DELETE FROM daily_logs WHERE user_id = num;

-- День 1 (сегодня - 6 дней)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE - INTERVAL '6 days', 2800, 2100, 400, NOW());

-- День 2 (сегодня - 5 дней)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE - INTERVAL '5 days', 3500, 2800, 500, NOW());

-- День 3 (сегодня - 4 дня)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE - INTERVAL '4 days', 4100, 3200, 600, NOW());

-- День 4 (сегодня - 3 дня)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE - INTERVAL '3 days', 3800, 2900, 450, NOW());

-- День 5 (сегодня - 2 дня)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE - INTERVAL '2 days', 4200, 3400, 700, NOW());

-- День 6 (вчера)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE - INTERVAL '1 day', 3900, 3100, 550, NOW());

-- День 7 (сегодня)
INSERT INTO daily_logs (user_id, log_date, logged_water, logged_calories, burned_calories, created_at)
VALUES (num, CURRENT_DATE, 2500, 1800, 300, NOW());

-- Проверка вставленных данных
SELECT log_date, logged_water, logged_calories, burned_calories
FROM daily_logs
WHERE user_id = num
ORDER BY log_date;
