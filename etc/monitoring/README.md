# Health Check & Monitoring

Инструменты для мониторинга здоровья приложения.

## Health Check Endpoints

### `/health` - Базовый health check

Проверяет, запущено ли приложение.

**Ответ:**
```json
{
  "status": "healthy",
  "service": "construction",
  "environment": "production"
}
```

**HTTP коды:**
- `200` - Приложение работает

**Пример:**
```bash
curl https://site.com/health
```

---

### `/health/db` - Проверка базы данных

Проверяет подключение к PostgreSQL.

**Ответ (успех):**
```json
{
  "status": "healthy",
  "service": "construction",
  "database": "connected"
}
```

**Ответ (ошибка):**
```json
{
  "status": "unhealthy",
  "database": "disconnected"
}
```

**HTTP коды:**
- `200` - База данных доступна
- `503` - База данных недоступна

**Пример:**
```bash
curl https://site.com/health/db
```

---

## Health Check Script

### Использование

```bash
cd /var/www/construction-prod/etc/monitoring

# Проверить production
./health-check.sh prod

# Проверить staging
./health-check.sh dev

# Проверить оба (по умолчанию)
./health-check.sh both
./health-check.sh
```

### Пример вывода

```
===== Production Environment =====
Checking Production /health... ✓ OK (HTTP 200)
Checking Production /health/db... ✓ OK (HTTP 200)
Overall: Healthy

===== Staging Environment =====
Checking Staging /health... ✓ OK (HTTP 200)
Checking Staging /health/db... ✓ OK (HTTP 200)
Overall: Healthy

All services are healthy!
```

---

## Автоматический мониторинг

### Cron job для проверки

```bash
# Редактируй crontab
crontab -e

# Проверка каждые 5 минут
*/5 * * * * /var/www/construction-prod/etc/monitoring/health-check.sh prod || echo "Production is down!" | mail -s "Alert: Construction Down" admin@site.com
```

### Скрипт с автоматическим перезапуском

Создай `/usr/local/bin/monitor-construction.sh`:

```bash
#!/bin/bash

# Проверка production
if ! /var/www/construction-prod/etc/monitoring/health-check.sh prod > /dev/null 2>&1; then
    echo "$(date): Production unhealthy, restarting..." >> /var/log/construction-monitor.log

    # Попытка перезапуска
    systemctl restart construction-prod

    # Подожди 10 секунд
    sleep 10

    # Проверь снова
    if /var/www/construction-prod/etc/monitoring/health-check.sh prod > /dev/null 2>&1; then
        echo "$(date): Production restarted successfully" >> /var/log/construction-monitor.log
    else
        echo "$(date): Production restart failed!" >> /var/log/construction-monitor.log
        echo "Construction Production failed to restart!" | mail -s "CRITICAL: Construction Down" admin@site.com
    fi
fi
```

Права и cron:
```bash
sudo chmod +x /usr/local/bin/monitor-construction.sh
sudo crontab -e

# Каждые 5 минут
*/5 * * * * /usr/local/bin/monitor-construction.sh
```

---

## Внешний мониторинг

### Uptime Robot (бесплатно)

1. Зарегистрируйся на https://uptimerobot.com
2. Добавь мониторы:
   - `https://site.com/health` (каждые 5 минут)
   - `https://dev.site.com/health` (каждые 5 минут)
3. Настрой уведомления (email, Telegram, Slack)

### Pingdom

1. Зарегистрируйся на https://www.pingdom.com
2. Добавь HTTP(S) check для `https://site.com/health`
3. Настрой alerts

### Healthchecks.io

```bash
# Создай аккаунт на https://healthchecks.io
# Получи URL для ping

# Добавь в cron
*/5 * * * * /var/www/construction-prod/etc/monitoring/health-check.sh prod && curl -fsS https://hc-ping.com/your-uuid-here > /dev/null
```

---

## Prometheus & Grafana (расширенный мониторинг)

### Установка Prometheus Node Exporter

```bash
# Скачай и установи
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
sudo mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

# Создай systemd сервис
sudo nano /etc/systemd/system/node_exporter.service
```

Содержимое:
```ini
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter

# Проверка
curl http://localhost:9100/metrics
```

---

## Логирование мониторинга

### Создай лог-файл

```bash
sudo touch /var/log/construction-monitor.log
sudo chown $USER:$USER /var/log/construction-monitor.log
```

### Ротация логов

```bash
sudo nano /etc/logrotate.d/construction-monitor
```

Содержимое:
```
/var/log/construction-monitor.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
}
```

---

## Telegram уведомления

### Скрипт для отправки в Telegram

Создай `/usr/local/bin/notify-telegram.sh`:

```bash
#!/bin/bash

BOT_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"
MESSAGE="$1"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    -d text="${MESSAGE}" \
    -d parse_mode="Markdown" > /dev/null
```

Использование:
```bash
chmod +x /usr/local/bin/notify-telegram.sh

# Отправить уведомление
/usr/local/bin/notify-telegram.sh "🚨 Construction Production is down!"
```

Интеграция с мониторингом:
```bash
# В monitor-construction.sh замени mail на:
/usr/local/bin/notify-telegram.sh "🚨 Construction Production is down!"
```

---

## Мониторинг метрик

### Простой мониторинг через systemd

```bash
# CPU и Memory usage
systemctl status construction-prod

# Детальная статистика
systemd-cgtop

# Конкретный сервис
systemctl show construction-prod --property=CPUUsageNSec
systemctl show construction-prod --property=MemoryCurrent
```

### Мониторинг логов в реальном времени

```bash
# Приложение
tail -f /var/www/construction-prod/logs/app.log | grep -E "ERROR|CRITICAL"

# Gunicorn
tail -f /var/www/construction-prod/logs/gunicorn-error.log

# Systemd
journalctl -u construction-prod -f

# Nginx
tail -f /var/log/nginx/construction-prod-error.log
```

---

## Dashboard (опционально)

### Простой HTML dashboard

Создай `monitoring-dashboard.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Construction Monitoring</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: monospace; padding: 20px; }
        .healthy { color: green; }
        .unhealthy { color: red; }
        .service { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>Construction Monitoring Dashboard</h1>
    <div id="status"></div>

    <script>
        async function checkHealth() {
            const services = [
                { name: 'Production', url: 'https://site.com' },
                { name: 'Staging', url: 'https://dev.site.com' }
            ];

            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '';

            for (const service of services) {
                try {
                    const resp = await fetch(`${service.url}/health`);
                    const data = await resp.json();

                    statusDiv.innerHTML += `
                        <div class="service healthy">
                            <h2>✓ ${service.name}</h2>
                            <p>Status: ${data.status}</p>
                            <p>Environment: ${data.environment}</p>
                        </div>
                    `;
                } catch (e) {
                    statusDiv.innerHTML += `
                        <div class="service unhealthy">
                            <h2>✗ ${service.name}</h2>
                            <p>Status: Down</p>
                        </div>
                    `;
                }
            }
        }

        checkHealth();
        setInterval(checkHealth, 30000);
    </script>
</body>
</html>
```

Размести на сервере:
```bash
cp monitoring-dashboard.html /var/www/html/monitoring.html

# Доступ через
https://site.com/monitoring.html
```

---

## Checklist

- [ ] Health endpoints добавлены в main.py
- [ ] Nginx пробрасывает /health
- [ ] Health check скрипт работает
- [ ] Cron job настроен для мониторинга
- [ ] Уведомления настроены (email/Telegram)
- [ ] Внешний мониторинг настроен (Uptime Robot)
- [ ] Логи мониторинга настроены
- [ ] Dashboard создан (опционально)

---

## Полезные ссылки

- [FastAPI Health Checks](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Uptime Robot](https://uptimerobot.com)
- [Healthchecks.io](https://healthchecks.io)
- [Prometheus](https://prometheus.io)
