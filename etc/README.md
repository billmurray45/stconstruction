# Deployment Configuration

Эта папка содержит все конфигурационные файлы для деплоя Construction проекта на сервер.

## Структура

```
etc/
├── nginx/                          # Nginx конфигурация
│   ├── nginx.conf                  # Конфигурация для dev и prod
│   └── README.md
│
├── systemd/                        # Systemd сервисы
│   ├── construction-dev.service    # Сервис для staging
│   ├── construction-prod.service   # Сервис для production
│   └── README.md
│
├── gunicorn/                       # Gunicorn конфигурация
│   ├── gunicorn.conf.py           # Конфигурация для production
│   ├── gunicorn-dev.conf.py       # Конфигурация для staging
│   └── README.md
│
└── README.md                       # Этот файл
```

## Быстрый старт

### 1. Установка зависимостей на сервере

```bash
# Обнови систему
sudo apt update && sudo apt upgrade -y

# Установи необходимые пакеты
sudo apt install -y nginx postgresql redis-server python3-pip python3-venv git certbot python3-certbot-nginx

# Создай пользователя для веб-сервера (если нужно)
sudo useradd -m -s /bin/bash www-data
```

### 2. Клонирование проекта

```bash
# Production
sudo mkdir -p /var/www/construction-prod
sudo chown $USER:$USER /var/www/construction-prod
cd /var/www/construction-prod
git clone https://github.com/yourusername/construction.git .
git checkout main

# Staging
sudo mkdir -p /var/www/construction-dev
sudo chown $USER:$USER /var/www/construction-dev
cd /var/www/construction-dev
git clone https://github.com/yourusername/construction.git .
git checkout staging
```

### 3. Настройка виртуального окружения

```bash
# Production
cd /var/www/construction-prod
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Staging
cd /var/www/construction-dev
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### 4. Создание .env файлов

```bash
# Production
cd /var/www/construction-prod
cp .env.example .env
nano .env  # Отредактируй для production

# Staging
cd /var/www/construction-dev
cp .env.example .env
nano .env  # Отредактируй для staging
```

**.env для production:**
```env
ENVIRONMENT=production
DB_NAME=standart_prod_db
DB_USER=standart_admin
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=GENERATE_SECURE_KEY_HERE
REDIS_URL=redis://localhost:6379
```

**.env для staging:**
```env
ENVIRONMENT=development
DB_NAME=standart_dev_db
DB_USER=standart_admin
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=GENERATE_SECURE_KEY_HERE
REDIS_URL=redis://localhost:6379
```

### 5. База данных

```bash
# Подключись к PostgreSQL
sudo -u postgres psql

# Создай базы
CREATE DATABASE standart_prod_db;
CREATE DATABASE standart_dev_db;
CREATE USER standart_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE standart_prod_db TO standart_admin;
GRANT ALL PRIVILEGES ON DATABASE standart_dev_db TO standart_admin;
\q

# Примени миграции
cd /var/www/construction-prod
source venv/bin/activate
alembic upgrade head

cd /var/www/construction-dev
source venv/bin/activate
alembic upgrade head
```

### 6. Nginx

```bash
# Скопируй конфигурацию
sudo cp /var/www/construction-prod/etc/nginx/nginx.conf /etc/nginx/sites-available/construction

# Создай symlink
sudo ln -s /etc/nginx/sites-available/construction /etc/nginx/sites-enabled/

# Удали default конфиг (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверь конфигурацию
sudo nginx -t

# Если ОК - перезагрузи
sudo systemctl reload nginx
```

### 7. SSL Сертификаты

```bash
# Production
sudo certbot --nginx -d site.com -d www.site.com

# Staging
sudo certbot --nginx -d dev.site.com

# Автообновление (уже настроено автоматически)
sudo certbot renew --dry-run
```

### 8. Systemd сервисы

```bash
# Скопируй сервисы
sudo cp /var/www/construction-prod/etc/systemd/*.service /etc/systemd/system/

# Перезагрузи systemd
sudo systemctl daemon-reload

# Включи автозапуск
sudo systemctl enable construction-prod
sudo systemctl enable construction-dev

# Запусти сервисы
sudo systemctl start construction-prod
sudo systemctl start construction-dev

# Проверь статус
sudo systemctl status construction-prod
sudo systemctl status construction-dev
```

### 9. Проверка работы

```bash
# Проверь порты
sudo netstat -tlnp | grep 8000  # production
sudo netstat -tlnp | grep 8001  # staging

# Проверь через curl
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8001/

# Проверь через nginx
curl https://site.com/
curl https://dev.site.com/
```

## Workflow деплоя

### Staging (dev.site.com)

```bash
# 1. На сервере
cd /var/www/construction-dev
git pull origin staging

# 2. Установи новые зависимости (если есть)
source venv/bin/activate
pip install -r requirements.txt

# 3. Примени миграции (если есть)
alembic upgrade head

# 4. Перезапусти сервис
sudo systemctl restart construction-dev

# 5. Проверь
curl https://dev.site.com/health
```

### Production (site.com)

```bash
# 1. На сервере
cd /var/www/construction-prod
git pull origin main

# 2. Установи новые зависимости (если есть)
source venv/bin/activate
pip install -r requirements.txt

# 3. Примени миграции (если есть)
alembic upgrade head

# 4. Graceful restart (без потери запросов)
sudo systemctl reload construction-prod

# 5. Проверь
curl https://site.com/health
```

## Автоматизация деплоя

Создай скрипты для автоматизации:

### deploy-dev.sh

```bash
#!/bin/bash
cd /var/www/construction-dev
git pull origin staging
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart construction-dev
echo "Dev deployed successfully!"
```

### deploy-prod.sh

```bash
#!/bin/bash
cd /var/www/construction-prod
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl reload construction-prod
echo "Production deployed successfully!"
```

Использование:
```bash
chmod +x deploy-dev.sh deploy-prod.sh
./deploy-dev.sh
./deploy-prod.sh
```

## Мониторинг

### Логи

```bash
# Nginx
sudo tail -f /var/log/nginx/construction-prod-access.log
sudo tail -f /var/log/nginx/construction-prod-error.log

# Systemd
sudo journalctl -u construction-prod -f
sudo journalctl -u construction-dev -f

# Gunicorn
tail -f /var/www/construction-prod/logs/gunicorn-access.log
tail -f /var/www/construction-prod/logs/gunicorn-error.log

# Приложение
tail -f /var/www/construction-prod/logs/app.log
tail -f /var/www/construction-prod/logs/errors.log
```

### Статус сервисов

```bash
# Все сервисы
systemctl list-units "construction-*" --all

# Nginx
sudo systemctl status nginx

# PostgreSQL
sudo systemctl status postgresql

# Redis
sudo systemctl status redis
```

### Health checks

```bash
# Production
curl https://site.com/health

# Staging
curl https://dev.site.com/health

# Локально
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8001/health
```

## Backup

### База данных

```bash
# Backup production DB
sudo -u postgres pg_dump standart_prod_db > backup_$(date +%Y%m%d).sql

# Restore
sudo -u postgres psql standart_prod_db < backup_20251111.sql
```

### Uploaded files

```bash
# Backup uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /var/www/construction-prod/app/static/uploads/

# Restore
tar -xzf uploads_backup_20251111.tar.gz -C /
```

### Автоматический backup

Создай cron job:
```bash
sudo crontab -e
```

Добавь:
```cron
# Backup DB каждый день в 2:00
0 2 * * * sudo -u postgres pg_dump standart_prod_db > /backups/db_$(date +\%Y\%m\%d).sql

# Backup uploads каждую неделю
0 3 * * 0 tar -czf /backups/uploads_$(date +\%Y\%m\%d).tar.gz /var/www/construction-prod/app/static/uploads/
```

## Security Checklist

- [ ] Firewall настроен (ufw или iptables)
- [ ] SSH доступ только по ключу
- [ ] Fail2Ban установлен и настроен
- [ ] SSL сертификаты установлены
- [ ] .env файлы защищены (chmod 600)
- [ ] PostgreSQL слушает только localhost
- [ ] Redis защищён паролем (опционально)
- [ ] Nginx security headers настроены
- [ ] Регулярные backup настроены
- [ ] Мониторинг настроен

## Troubleshooting

См. детальные инструкции в:
- `nginx/README.md`
- `systemd/README.md`
- `gunicorn/README.md`

## Полезные команды

```bash
# Перезапуск всех сервисов
sudo systemctl restart construction-prod nginx postgresql redis

# Проверка всех портов
sudo netstat -tlnp | grep -E ":(80|443|8000|8001|5432|6379)"

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Проверка load average
uptime

# Top процессы
htop
```

## Контакты

- Документация: См. README.md файлы в каждой папке
- GitHub: https://github.com/yourusername/construction
