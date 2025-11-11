# Gunicorn Configuration

Gunicorn - это WSGI HTTP сервер для Python приложений.

## Файлы

- `gunicorn.conf.py` - Production конфигурация (порт 8000)
- `gunicorn-dev.conf.py` - Development конфигурация (порт 8001)

## Основные параметры

### Production (gunicorn.conf.py)

```python
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1  # Автоматически
worker_class = "uvicorn.workers.UvicornWorker"  # Для FastAPI
timeout = 120
keepalive = 5
loglevel = "info"
```

**Расчёт workers:**
- 2 CPU → 5 workers
- 4 CPU → 9 workers
- 8 CPU → 17 workers

### Development (gunicorn-dev.conf.py)

```python
bind = "127.0.0.1:8001"
workers = 2  # Фиксировано для dev
loglevel = "debug"  # Больше логов
reload = True  # Авто-перезагрузка при изменении кода
```

## Запуск вручную

### Production

```bash
cd /var/www/construction-prod
source venv/bin/activate
gunicorn --config etc/gunicorn/gunicorn.conf.py main:app
```

### Development

```bash
cd /var/www/construction-dev
source venv/bin/activate
gunicorn --config etc/gunicorn/gunicorn-dev.conf.py main:app
```

## Управление через systemd

```bash
# Запуск
sudo systemctl start construction-prod

# Остановка
sudo systemctl stop construction-prod

# Graceful reload (без потери запросов)
sudo systemctl reload construction-prod

# Или отправь SIGHUP
sudo kill -HUP $(pgrep -f "gunicorn.*construction")
```

## Сигналы

Gunicorn понимает Unix сигналы:

- `HUP` - Graceful reload (перезагрузка без потери запросов)
- `TERM` - Graceful shutdown
- `INT` / `QUIT` - Quick shutdown
- `USR2` - Upgrade gunicorn (zero-downtime)

```bash
# Graceful reload
kill -HUP <master_pid>

# Graceful shutdown
kill -TERM <master_pid>
```

## Мониторинг

### Проверка работающих процессов

```bash
# Все gunicorn процессы
ps aux | grep gunicorn

# Production
ps aux | grep "gunicorn.*8000"

# Development
ps aux | grep "gunicorn.*8001"
```

### Проверка портов

```bash
# Production (8000)
curl http://127.0.0.1:8000/health

# Development (8001)
curl http://127.0.0.1:8001/health
```

### Статистика

```bash
# Количество workers
pgrep -f "gunicorn.*construction" | wc -l

# Memory usage
ps aux | grep gunicorn | awk '{sum+=$6} END {print sum/1024 " MB"}'
```

## Troubleshooting

### Workers падают

```bash
# Проверь логи
tail -f /var/www/construction-prod/logs/gunicorn-error.log

# Возможные причины:
# - Таймаут слишком маленький
# - Memory leak в приложении
# - Слишком много workers
```

**Решение:** Увеличь timeout или уменьши workers.

### Медленные ответы

```bash
# Проверь количество workers
ps aux | grep gunicorn | wc -l

# Проверь load average
uptime
```

**Решение:** Увеличь количество workers в `gunicorn.conf.py`.

### Memory leak

```bash
# Проверь потребление памяти
ps aux | grep gunicorn | awk '{print $6, $11}'
```

**Решение:** Используй `max_requests` для автоматической перезагрузки workers:
```python
max_requests = 1000  # Перезапуск после 1000 запросов
```

## Оптимизация

### Для высоконагруженных сайтов

```python
# Больше workers
workers = multiprocessing.cpu_count() * 4

# Больше соединений на worker
worker_connections = 2000

# Увеличь backlog
backlog = 4096

# Keepalive
keepalive = 120
```

### Для экономии памяти

```python
# Меньше workers
workers = 2

# Перезапуск workers чаще
max_requests = 500
max_requests_jitter = 100
```

## Testing

### Load testing

```bash
# Установи ApacheBench
sudo apt install apache2-utils

# Тест (1000 запросов, 10 одновременно)
ab -n 1000 -c 10 http://127.0.0.1:8000/

# С keepalive
ab -n 1000 -c 10 -k http://127.0.0.1:8000/
```

### Stress test

```bash
# Установи wrk
sudo apt install wrk

# 30 секунд теста, 12 потоков, 400 соединений
wrk -t12 -c400 -d30s http://127.0.0.1:8000/
```

## Логирование

### Форматы логов

**Access log format:**
```
%(h)s - Remote address
%(l)s - '-'
%(u)s - User name
%(t)s - Date/time
%(r)s - Request line
%(s)s - Status code
%(b)s - Response size
%(f)s - Referer
%(a)s - User agent
```

**Пример:**
```
127.0.0.1 - - [11/Nov/2025:14:30:45 +0000] "GET /health HTTP/1.1" 200 15 "-" "curl/7.68.0"
```

### Ротация логов

Если используешь file logging в gunicorn.conf.py:

```bash
# Установи logrotate
sudo apt install logrotate

# Создай конфиг
sudo nano /etc/logrotate.d/construction
```

Содержимое:
```
/var/www/construction-prod/logs/gunicorn-*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload construction-prod > /dev/null 2>&1 || true
    endscript
}
```

## Полезные ссылки

- [Gunicorn Settings](https://docs.gunicorn.org/en/stable/settings.html)
- [Gunicorn Design](https://docs.gunicorn.org/en/stable/design.html)
- [FastAPI with Gunicorn](https://fastapi.tiangolo.com/deployment/server-workers/)
