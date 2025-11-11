# Systemd Services Configuration

Эта папка содержит systemd сервисы для автоматического запуска Construction приложения.

## Структура

```
etc/systemd/
├── construction-dev.service     # Systemd сервис для dev/staging
├── construction-prod.service    # Systemd сервис для production
└── README.md                    # Эта инструкция

etc/gunicorn/
├── gunicorn.conf.py            # Gunicorn конфиг для production (порт 8000)
├── gunicorn-dev.conf.py        # Gunicorn конфиг для dev (порт 8001)
└── README.md                   # Инструкция по gunicorn
```

## Что такое systemd?

Systemd - это менеджер служб в Linux, который:
- ✅ Автоматически запускает приложение при старте сервера
- ✅ Перезапускает приложение при сбое
- ✅ Управляет логами
- ✅ Контролирует ресурсы

## Установка на сервере

### 1. Установка Gunicorn

```bash
# В виртуальном окружении
source /var/www/construction-prod/venv/bin/activate
pip install gunicorn uvicorn[standard]

# То же для dev
source /var/www/construction-dev/venv/bin/activate
pip install gunicorn uvicorn[standard]
```

### 2. Копирование systemd сервисов

```bash
# Скопировать сервисы в системную папку
sudo cp /var/www/construction-prod/etc/systemd/*.service /etc/systemd/system/

# Проверить файлы
ls -la /etc/systemd/system/construction-*.service
```

### 3. Перезагрузка systemd и запуск сервисов

```bash
# Перезагрузить systemd daemon
sudo systemctl daemon-reload

# Включить автозапуск при загрузке сервера
sudo systemctl enable construction-prod
sudo systemctl enable construction-dev

# Запустить сервисы
sudo systemctl start construction-prod
sudo systemctl start construction-dev

# Проверить статус
sudo systemctl status construction-prod
sudo systemctl status construction-dev
```

## Управление сервисами

### Базовые команды

```bash
# Запуск
sudo systemctl start construction-prod

# Остановка
sudo systemctl stop construction-prod

# Перезапуск
sudo systemctl restart construction-prod

# Перезагрузка конфигурации (без остановки)
sudo systemctl reload construction-prod

# Статус
sudo systemctl status construction-prod

# Включить автозапуск
sudo systemctl enable construction-prod

# Отключить автозапуск
sudo systemctl disable construction-prod
```

### Логи

```bash
# Просмотр логов (последние 50 строк)
sudo journalctl -u construction-prod -n 50

# Следить за логами в реальном времени
sudo journalctl -u construction-prod -f

# Логи за сегодня
sudo journalctl -u construction-prod --since today

# Логи за последний час
sudo journalctl -u construction-prod --since "1 hour ago"

# Логи с ошибками
sudo journalctl -u construction-prod -p err

# Логи из файлов (если настроены в systemd)
tail -f /var/www/construction-prod/logs/gunicorn-access.log
tail -f /var/www/construction-prod/logs/gunicorn-error.log
```

## Конфигурация сервисов

### Production (construction-prod.service)

```ini
[Service]
WorkingDirectory=/var/www/construction-prod
Environment="PATH=/var/www/construction-prod/venv/bin"
EnvironmentFile=/var/www/construction-prod/.env
ExecStart=/var/www/construction-prod/venv/bin/gunicorn \
    --config /var/www/construction-prod/etc/gunicorn/gunicorn.conf.py \
    main:app
```

**Особенности:**
- Порт: 8000
- Workers: CPU * 2 + 1 (автоматически)
- Повышенная безопасность (ProtectSystem, ProtectHome)
- Логи в `/var/www/construction-prod/logs/`

### Development (construction-dev.service)

```ini
[Service]
WorkingDirectory=/var/www/construction-dev
Environment="PATH=/var/www/construction-dev/venv/bin"
EnvironmentFile=/var/www/construction-dev/.env
ExecStart=/var/www/construction-dev/venv/bin/gunicorn \
    --config /var/www/construction-dev/etc/gunicorn/gunicorn-dev.conf.py \
    main:app
```

**Особенности:**
- Порт: 8001
- Workers: 2 (фиксировано для dev)
- Auto-reload при изменении кода
- Verbose logging (debug mode)
- Логи в `/var/www/construction-dev/logs/`

## Troubleshooting

### Сервис не запускается

```bash
# 1. Проверь логи
sudo journalctl -u construction-prod -n 100

# 2. Проверь статус
sudo systemctl status construction-prod

# 3. Проверь конфигурацию
sudo systemd-analyze verify /etc/systemd/system/construction-prod.service

# 4. Проверь права доступа
ls -la /var/www/construction-prod
ls -la /var/www/construction-prod/venv/bin/gunicorn

# 5. Проверь .env файл
cat /var/www/construction-prod/.env
```

### Ошибка "Failed to start"

**Причины:**
- Порт уже занят
- Неправильный путь к venv
- Отсутствует gunicorn
- Ошибка в .env файле
- Нет прав доступа

**Решение:**
```bash
# Проверь занятые порты
sudo netstat -tlnp | grep 8000
sudo netstat -tlnp | grep 8001

# Проверь gunicorn
/var/www/construction-prod/venv/bin/gunicorn --version

# Проверь main.py
cd /var/www/construction-prod
source venv/bin/activate
python -c "from main import app; print('OK')"
```

### Сервис падает после запуска

```bash
# Проверь логи ошибок
sudo journalctl -u construction-prod -n 100 -p err

# Проверь логи приложения
tail -n 100 /var/www/construction-prod/logs/gunicorn-error.log
tail -n 100 /var/www/construction-prod/logs/app.log

# Попробуй запустить вручную
cd /var/www/construction-prod
source venv/bin/activate
gunicorn --config etc/gunicorn/gunicorn.conf.py main:app
```

### Порт занят

```bash
# Найти процесс на порту 8000
sudo lsof -i :8000

# Убить процесс
sudo kill -9 <PID>

# Или остановить старый сервис
sudo systemctl stop construction-prod
```

## Обновление сервисов

### После изменения systemd файла

```bash
# 1. Скопировать обновлённый файл
sudo cp /var/www/construction-prod/etc/systemd/construction-prod.service /etc/systemd/system/

# 2. Перезагрузить systemd
sudo systemctl daemon-reload

# 3. Перезапустить сервис
sudo systemctl restart construction-prod
```

### После деплоя нового кода

```bash
# Способ 1: Restart (с остановкой)
sudo systemctl restart construction-prod

# Способ 2: Reload (без остановки, если поддерживается)
sudo systemctl reload construction-prod

# Способ 3: Gunicorn graceful reload (без потери запросов)
sudo kill -HUP $(cat /run/construction-prod.pid)
```

## Мониторинг

### Проверка работоспособности

```bash
# Статус всех construction сервисов
systemctl list-units "construction-*" --all

# Проверка через curl
curl http://127.0.0.1:8000/health  # production
curl http://127.0.0.1:8001/health  # dev

# Проверка через nginx
curl https://site.com/health
curl https://dev.site.com/health
```

### Автоматический мониторинг

Создай скрипт `/usr/local/bin/check-construction.sh`:

```bash
#!/bin/bash
if ! systemctl is-active --quiet construction-prod; then
    echo "Construction prod is down!" | mail -s "Alert" admin@site.com
    systemctl restart construction-prod
fi
```

Добавь в crontab:
```bash
# Проверка каждые 5 минут
*/5 * * * * /usr/local/bin/check-construction.sh
```

## Безопасность

### Настройки безопасности в systemd

Сервисы используют:

- `NoNewPrivileges=true` - Запрет повышения привилегий
- `PrivateTmp=true` - Изолированная /tmp директория
- `ProtectSystem=strict` - Защита системных файлов (только prod)
- `ProtectHome=true` - Защита домашних директорий (только prod)
- `ReadWritePaths=...` - Разрешённые пути для записи

### Права доступа

```bash
# Сервисы должны работать под пользователем www-data
sudo chown -R www-data:www-data /var/www/construction-prod
sudo chown -R www-data:www-data /var/www/construction-dev

# .env файл только для чтения
chmod 600 /var/www/construction-prod/.env
chmod 600 /var/www/construction-dev/.env
```

## Production Checklist

Перед запуском в production:

- [ ] Gunicorn установлен в venv
- [ ] .env файл настроен с `ENVIRONMENT=production`
- [ ] База данных создана и миграции применены
- [ ] Static файлы собраны
- [ ] Логи директория создана с правами www-data
- [ ] Systemd сервис скопирован в `/etc/systemd/system/`
- [ ] Сервис включен: `systemctl enable construction-prod`
- [ ] Nginx настроен и работает
- [ ] SSL сертификаты установлены
- [ ] Firewall настроен (порты 80, 443 открыты)
- [ ] Мониторинг настроен

## Полезные алиасы

Добавь в `~/.bashrc`:

```bash
# Construction aliases
alias cprod-status='sudo systemctl status construction-prod'
alias cprod-restart='sudo systemctl restart construction-prod'
alias cprod-logs='sudo journalctl -u construction-prod -f'
alias cprod-errors='sudo journalctl -u construction-prod -p err -n 50'

alias cdev-status='sudo systemctl status construction-dev'
alias cdev-restart='sudo systemctl restart construction-dev'
alias cdev-logs='sudo journalctl -u construction-dev -f'
```

Применить:
```bash
source ~/.bashrc
```

Использование:
```bash
cprod-status
cprod-logs
```

## Ссылки

- [Systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
