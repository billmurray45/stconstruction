# Nginx Configuration Guide

Эта папка содержит конфигурацию Nginx для проекта Construction.

## Структура

```
etc/nginx/
├── nginx.conf          # Основная конфигурация для dev и prod
└── README.md           # Эта инструкция
```

## Установка на сервере

### 1. Установка Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# Проверка установки
nginx -v
```

### 2. Копирование конфигурации

```bash
# Скопировать конфигурацию
sudo cp /var/www/construction-prod/etc/nginx/nginx.conf /etc/nginx/sites-available/construction

# Создать symlink
sudo ln -s /etc/nginx/sites-available/construction /etc/nginx/sites-enabled/

# Удалить default конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default
```

### 3. Создание директорий для проектов

```bash
# Production
sudo mkdir -p /var/www/construction-prod
sudo chown -R $USER:$USER /var/www/construction-prod

# Staging
sudo mkdir -p /var/www/construction-dev
sudo chown -R $USER:$USER /var/www/construction-dev
```

### 4. SSL сертификаты (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификатов для production
sudo certbot --nginx -d site.com -d www.site.com

# Получение сертификатов для staging
sudo certbot --nginx -d dev.site.com

# Автоматическое обновление (уже настроено)
sudo certbot renew --dry-run
```

### 5. Проверка и запуск

```bash
# Проверка синтаксиса конфигурации
sudo nginx -t

# Перезагрузка Nginx
sudo systemctl reload nginx

# Проверка статуса
sudo systemctl status nginx

# Включить автозапуск
sudo systemctl enable nginx
```

## Конфигурация для окружений

### Production (site.com)

- **Backend**: `127.0.0.1:8000`
- **Static files**: `/var/www/construction-prod/app/static`
- **Git branch**: `main`
- **Logs**:
  - `/var/log/nginx/construction-prod-access.log`
  - `/var/log/nginx/construction-prod-error.log`

### Staging (dev.site.com)

- **Backend**: `127.0.0.1:8001`
- **Static files**: `/var/www/construction-dev/app/static`
- **Git branch**: `staging`
- **Logs**:
  - `/var/log/nginx/construction-dev-access.log`
  - `/var/log/nginx/construction-dev-error.log`

## Security Features

### Включено в конфигурации:

✅ **HTTPS redirect** - Автоматический редирект HTTP → HTTPS
✅ **HSTS** - Force HTTPS (только production)
✅ **Security Headers** - X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
✅ **SSL/TLS** - TLS 1.2+ с современными шифрами
✅ **Gzip compression** - Сжатие статики
✅ **Static file caching** - Агрессивный кеш (30-90 дней)
✅ **Sensitive file blocking** - Блокировка .env, .git, и т.д.
✅ **File upload limits** - Максимум 20MB

## Troubleshooting

### Проверка логов

```bash
# Access logs
sudo tail -f /var/log/nginx/construction-prod-access.log
sudo tail -f /var/log/nginx/construction-dev-access.log

# Error logs
sudo tail -f /var/log/nginx/construction-prod-error.log
sudo tail -f /var/log/nginx/construction-dev-error.log

# Nginx error log
sudo tail -f /var/log/nginx/error.log
```

### Проверка портов

```bash
# Nginx должен слушать 80 и 443
sudo netstat -tlnp | grep nginx

# FastAPI должен слушать 8000 и 8001
sudo netstat -tlnp | grep python
```

### Перезапуск сервисов

```bash
# Nginx
sudo systemctl restart nginx

# FastAPI (production)
sudo systemctl restart construction-prod

# FastAPI (staging)
sudo systemctl restart construction-dev
```

### Типичные ошибки

#### 502 Bad Gateway
- FastAPI не запущен
- Неправильный порт в upstream
- Проверь: `sudo systemctl status construction-prod`

#### 404 Not Found для static файлов
- Неправильный путь в `location /static`
- Проверь: `ls /var/www/construction-prod/app/static`

#### SSL certificate error
- Сертификаты не установлены
- Неправильный путь к сертификатам
- Запусти: `sudo certbot --nginx -d site.com`

## Тестирование локально (без SSL)

Если хочешь протестировать nginx локально без SSL:

```nginx
# Упрощенная версия для localhost
server {
    listen 8080;
    server_name localhost;

    location /static {
        alias /home/bauka45/myprojects/construction/app/static;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Запуск:
```bash
# Тест конфигурации
nginx -t -c /home/bauka45/myprojects/construction/etc/nginx/nginx-local.conf

# Запуск (если есть права)
nginx -c /home/bauka45/myprojects/construction/etc/nginx/nginx-local.conf
```

## Performance Tuning

Для высоконагруженных сайтов добавь в `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;
worker_connections 1024;

http {
    # Кеширование
    open_file_cache max=2000 inactive=20s;
    open_file_cache_valid 60s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;

    # Таймауты
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
}
```

## Мониторинг

### Nginx Status Page (опционально)

Добавь в конфигурацию:

```nginx
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

Просмотр:
```bash
curl http://localhost/nginx_status
```

## Обновление конфигурации

```bash
# 1. Обнови файл в репозитории
git pull origin main  # или staging

# 2. Скопируй новую конфигурацию
sudo cp /var/www/construction-prod/etc/nginx/nginx.conf /etc/nginx/sites-available/construction

# 3. Проверь синтаксис
sudo nginx -t

# 4. Если ОК - перезагрузи
sudo systemctl reload nginx
```

## Дополнительная безопасность

### Rate Limiting (опционально)

Раскомментируй в конфигурации:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://construction_prod;
}
```

### Fail2Ban (защита от brute-force)

```bash
sudo apt install fail2ban

# Создать фильтр для nginx
sudo nano /etc/fail2ban/filter.d/nginx-limit-req.conf
```

## Полезные ссылки

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [Security Headers Check](https://securityheaders.com/)
