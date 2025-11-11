# PostgreSQL Docker Configuration

PostgreSQL работает в Docker контейнере и используется обоими окружениями (production и staging).

## Структура

```
etc/postgres/
├── init.sql        # SQL скрипт для автосоздания баз
└── README.md       # Эта инструкция
```

## Как это работает

### Docker Compose

Один контейнер PostgreSQL содержит ДВЕ базы данных:
- `standart_prod_db` - для production
- `standart_dev_db` - для staging

```
┌─────────────────────────────────┐
│   Docker Container (postgres)   │
│                                  │
│  ├─ standart_prod_db (site.com) │
│  └─ standart_dev_db (dev.site)  │
└─────────────────────────────────┘
          ↑
   Port 5432 (localhost)
          ↑
    ┌─────┴──────┐
    │            │
FastAPI prod  FastAPI dev
```

## Установка на сервере

### 1. Установка Docker и Docker Compose

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавь пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка
docker --version
docker compose version
```

### 2. Создание .env файла

```bash
# Создай .env для docker-compose
nano /var/www/construction-prod/.env
```

Содержимое:
```env
DB_USER=standart_admin
DB_PASSWORD=STRONG_PASSWORD_HERE
```

### 3. Запуск PostgreSQL

```bash
cd /var/www/construction-prod
docker compose up -d postgres

# Проверка
docker ps
docker logs standart_db
```

### 4. Проверка баз данных

```bash
# Подключись к PostgreSQL
docker exec -it standart_db psql -U standart_admin -d postgres

# Список баз
\l

# Должны быть:
# standart_prod_db
# standart_dev_db

# Выход
\q
```

## Управление

### Запуск/остановка

```bash
# Запуск
docker compose up -d postgres

# Остановка
docker compose stop postgres

# Остановка и удаление (ДАННЫЕ СОХРАНЯЮТСЯ в volume)
docker compose down

# Перезапуск
docker compose restart postgres

# Логи
docker compose logs -f postgres
```

### Подключение к PostgreSQL

```bash
# Из контейнера
docker exec -it standart_db psql -U standart_admin -d standart_prod_db

# С хоста (если установлен psql)
psql -h localhost -p 5432 -U standart_admin -d standart_prod_db
```

## Миграции

### Production

```bash
cd /var/www/construction-prod
source venv/bin/activate
export DATABASE_URL="postgresql://standart_admin:password@localhost:5432/standart_prod_db"
alembic upgrade head
```

### Staging

```bash
cd /var/www/construction-dev
source venv/bin/activate
export DATABASE_URL="postgresql://standart_admin:password@localhost:5432/standart_dev_db"
alembic upgrade head
```

## Backup

### Создание backup

```bash
# Production DB
docker exec standart_db pg_dump -U standart_admin standart_prod_db > backup_prod_$(date +%Y%m%d).sql

# Staging DB
docker exec standart_db pg_dump -U standart_admin standart_dev_db > backup_dev_$(date +%Y%m%d).sql

# Все базы
docker exec standart_db pg_dumpall -U standart_admin > backup_all_$(date +%Y%m%d).sql
```

### Восстановление backup

```bash
# Production
cat backup_prod_20251111.sql | docker exec -i standart_db psql -U standart_admin -d standart_prod_db

# Staging
cat backup_dev_20251111.sql | docker exec -i standart_db psql -U standart_admin -d standart_dev_db
```

### Автоматический backup (cron)

```bash
# Создай скрипт
sudo nano /usr/local/bin/backup-postgres.sh
```

Содержимое:
```bash
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup production
docker exec standart_db pg_dump -U standart_admin standart_prod_db | gzip > $BACKUP_DIR/prod_$DATE.sql.gz

# Backup staging
docker exec standart_db pg_dump -U standart_admin standart_dev_db | gzip > $BACKUP_DIR/dev_$DATE.sql.gz

# Удалить старые backup (старше 30 дней)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Права и cron:
```bash
sudo chmod +x /usr/local/bin/backup-postgres.sh

# Добавь в crontab
sudo crontab -e

# Backup каждый день в 2:00
0 2 * * * /usr/local/bin/backup-postgres.sh
```

## Мониторинг

### Проверка статуса

```bash
# Статус контейнера
docker ps | grep standart_db

# Логи
docker logs standart_db --tail 100

# Статистика
docker stats standart_db

# Использование места
docker exec standart_db du -sh /var/lib/postgresql/data
```

### Проверка подключений

```bash
# Количество активных подключений
docker exec standart_db psql -U standart_admin -d postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Список активных подключений
docker exec standart_db psql -U standart_admin -d postgres -c "SELECT pid, usename, application_name, client_addr, state FROM pg_stat_activity WHERE state = 'active';"
```

## Troubleshooting

### Контейнер не запускается

```bash
# Проверь логи
docker logs standart_db

# Проверь порт
sudo netstat -tlnp | grep 5432

# Если порт занят - останови другой PostgreSQL
sudo systemctl stop postgresql
```

### "Connection refused"

```bash
# Проверь, что контейнер работает
docker ps | grep standart_db

# Проверь порт
docker port standart_db

# Должно быть: 5432/tcp -> 0.0.0.0:5432
```

### База не создалась автоматически

```bash
# Создай вручную
docker exec -it standart_db psql -U standart_admin -d postgres

CREATE DATABASE standart_prod_db;
CREATE DATABASE standart_dev_db;
GRANT ALL PRIVILEGES ON DATABASE standart_prod_db TO standart_admin;
GRANT ALL PRIVILEGES ON DATABASE standart_dev_db TO standart_admin;
\q
```

### Забыл пароль

```bash
# Пароль хранится в .env
cat /var/www/construction-prod/.env | grep DB_PASSWORD
```

### Нужно сбросить всё

```bash
# ВНИМАНИЕ: Удалит все данные!
docker compose down -v
docker volume rm construction_postgres_data

# Запусти заново
docker compose up -d postgres
```

## Обновление PostgreSQL

### До новой версии

```bash
# 1. Backup
docker exec standart_db pg_dumpall -U standart_admin > backup_before_upgrade.sql

# 2. Останови и удали контейнер (volume сохранится)
docker compose down

# 3. Измени версию в docker-compose.yml
# image: postgres:16 → postgres:17

# 4. Запусти
docker compose up -d postgres

# 5. Проверь
docker logs standart_db
```

## Безопасность

### Изменение пароля

```bash
# Подключись
docker exec -it standart_db psql -U standart_admin -d postgres

# Смени пароль
ALTER USER standart_admin WITH PASSWORD 'new_strong_password';
\q

# Обнови .env
nano /var/www/construction-prod/.env
```

### Настройка pg_hba.conf (опционально)

Если нужен доступ с других IP:

```bash
docker exec -it standart_db bash
nano /var/lib/postgresql/data/pg_hba.conf

# Добавь
host    all    all    10.0.0.0/24    md5

# Перезапусти
exit
docker compose restart postgres
```

## Production Checklist

- [ ] Docker и Docker Compose установлены
- [ ] .env файл создан с сильным паролем
- [ ] PostgreSQL контейнер запущен
- [ ] Обе базы созданы (prod и dev)
- [ ] Миграции применены
- [ ] Backup скрипт настроен (cron)
- [ ] Мониторинг настроен
- [ ] Firewall: порт 5432 закрыт извне (доступен только localhost)

## Полезные команды

```bash
# Размер баз данных
docker exec standart_db psql -U standart_admin -d postgres -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database;"

# Версия PostgreSQL
docker exec standart_db psql -U standart_admin -d postgres -c "SELECT version();"

# Список таблиц в prod DB
docker exec standart_db psql -U standart_admin -d standart_prod_db -c "\dt"

# SQL запрос
docker exec standart_db psql -U standart_admin -d standart_prod_db -c "SELECT * FROM users LIMIT 5;"
```
