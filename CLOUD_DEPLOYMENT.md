# ☁️ Развертывание бота в облаке

Несколько вариантов бесплатного запуска бота в облаке, чтобы он работал 24/7.

---

## 🚀 Вариант 1: GitHub Actions (Рекомендуется - Бесплатно)

**Плюсы**: Полностью бесплатно, автоматический запуск по расписанию
**Минусы**: Запускается периодически, а не непрерывно

### Настройка:

1. **Создайте GitHub Secrets** (для безопасности):
   - Откройте ваш репозиторий на GitHub
   - Settings → Secrets and variables → Actions → New repository secret
   - Добавьте секреты:
     - `TELEGRAM_BOT_TOKEN`: `8080110045:AAGK01_8PByIWA-F9o4wJnlGRdQtWu89Uyo`
     - `TELEGRAM_CHAT_ID`: ваш chat_id (узнать можно через @userinfobot)

2. **Файл `.github/workflows/flight-bot.yml`** уже создан в проекте

3. **Пуш в GitHub**:
   ```bash
   git push origin claude/cheap-flights-moscow-ufa-019sn6X5EcQrtysQxyofq1eg
   ```

4. **Активация**:
   - Перейдите в Actions на GitHub
   - Включите workflows если они отключены
   - Бот будет запускаться каждый час автоматически

---

## 🌐 Вариант 2: Railway.app (Бесплатно с ограничениями)

**Плюсы**: Простой деплой, непрерывная работа
**Минусы**: ~500 часов бесплатно в месяц (потом нужна карта)

### Настройка:

1. **Зарегистрируйтесь на [Railway.app](https://railway.app/)**

2. **Создайте новый проект**:
   - New Project → Deploy from GitHub repo
   - Выберите ваш репозиторий

3. **Настройте переменные окружения**:
   ```
   TELEGRAM_BOT_TOKEN=8080110045:AAGK01_8PByIWA-F9o4wJnlGRdQtWu89Uyo
   TELEGRAM_CHAT_ID=ваш_chat_id
   ```

4. **Настройте Start Command**:
   ```
   python3 cheap_flights_bot.py
   ```

5. **Deploy** - Railway автоматически развернет бота

---

## 🎨 Вариант 3: Render.com (Бесплатно навсегда)

**Плюсы**: Полностью бесплатно навсегда
**Минусы**: Засыпает после 15 минут неактивности (но для бота это не проблема)

### Настройка:

1. **Зарегистрируйтесь на [Render.com](https://render.com/)**

2. **Создайте Web Service**:
   - New → Background Worker
   - Connect your GitHub repository

3. **Настройки**:
   - **Name**: flight-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements_flight_bot.txt`
   - **Start Command**: `python cheap_flights_bot.py`

4. **Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=8080110045:AAGK01_8PByIWA-F9o4wJnlGRdQtWu89Uyo
   TELEGRAM_CHAT_ID=ваш_chat_id
   ```

5. **Deploy** - Render развернет бота автоматически

---

## 🐳 Вариант 4: Google Cloud Run (Бесплатный уровень)

**Плюсы**: Щедрый бесплатный уровень от Google
**Минусы**: Требует настройки Docker и GCP

### Настройка:

1. **Установите Google Cloud SDK**:
   ```bash
   curl https://sdk.cloud.google.com | bash
   gcloud init
   ```

2. **Создайте проект в GCP**:
   ```bash
   gcloud projects create flight-bot-project
   gcloud config set project flight-bot-project
   ```

3. **Соберите Docker образ**:
   ```bash
   docker build -t gcr.io/flight-bot-project/flight-bot .
   docker push gcr.io/flight-bot-project/flight-bot
   ```

4. **Разверните на Cloud Run**:
   ```bash
   gcloud run deploy flight-bot \
     --image gcr.io/flight-bot-project/flight-bot \
     --platform managed \
     --region us-central1 \
     --set-env-vars TELEGRAM_BOT_TOKEN=8080110045:AAGK01_8PByIWA-F9o4wJnlGRdQtWu89Uyo,TELEGRAM_CHAT_ID=ваш_chat_id
   ```

---

## 💻 Вариант 5: VPS (Oracle Cloud - Бесплатно навсегда)

**Плюсы**: Полный контроль, бесплатно навсегда
**Минусы**: Требует настройки сервера

### Настройка:

1. **Создайте аккаунт на [Oracle Cloud](https://www.oracle.com/cloud/free/)**

2. **Создайте VM instance** (Always Free tier):
   - Ubuntu 22.04
   - 1 GB RAM
   - 1 CPU

3. **Подключитесь по SSH**:
   ```bash
   ssh ubuntu@your-vm-ip
   ```

4. **Установите Python и зависимости**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git
   ```

5. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/d1x3/lalalala.git
   cd lalalala
   git checkout claude/cheap-flights-moscow-ufa-019sn6X5EcQrtysQxyofq1eg
   ```

6. **Установите зависимости**:
   ```bash
   pip3 install requests
   ```

7. **Создайте systemd сервис** `/etc/systemd/system/flight-bot.service`:
   ```ini
   [Unit]
   Description=Cheap Flights Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/lalalala
   ExecStart=/usr/bin/python3 /home/ubuntu/lalalala/cheap_flights_bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

8. **Запустите сервис**:
   ```bash
   sudo systemctl enable flight-bot
   sudo systemctl start flight-bot
   sudo systemctl status flight-bot
   ```

9. **Просмотр логов**:
   ```bash
   sudo journalctl -u flight-bot -f
   ```

---

## 🔧 Вариант 6: PythonAnywhere (Ограниченно бесплатно)

**Плюсы**: Простая настройка
**Минусы**: Бесплатный план ограничивает outbound connections (может не работать с некоторыми API)

### Настройка:

1. **Зарегистрируйтесь на [PythonAnywhere.com](https://www.pythonanywhere.com/)**

2. **Откройте Bash консоль**:
   ```bash
   git clone https://github.com/d1x3/lalalala.git
   cd lalalala
   git checkout claude/cheap-flights-moscow-ufa-019sn6X5EcQrtysQxyofq1eg
   pip3 install --user requests
   ```

3. **Настройте Always-on task** (требует платный план) или **Scheduled task**:
   - Tasks → Add a new scheduled task
   - Command: `/home/yourusername/lalalala/cheap_flights_bot.py --once`
   - Frequency: Hourly

---

## 🎯 Рекомендации по выбору

| Платформа | Бесплатно | Сложность | Рекомендация |
|-----------|-----------|-----------|--------------|
| **GitHub Actions** | ✅ Да | 🟢 Легко | ⭐⭐⭐⭐⭐ Лучший для начала |
| **Railway** | ⚠️ Ограничено | 🟢 Легко | ⭐⭐⭐⭐ Хорошо |
| **Render** | ✅ Да | 🟢 Легко | ⭐⭐⭐⭐⭐ Отлично |
| **Google Cloud Run** | ⚠️ Лимиты | 🟡 Средне | ⭐⭐⭐ Для продвинутых |
| **Oracle Cloud VPS** | ✅ Да | 🔴 Сложно | ⭐⭐⭐⭐⭐ Максимум контроля |
| **PythonAnywhere** | ⚠️ Ограничено | 🟢 Легко | ⭐⭐ Есть ограничения |

---

## 📋 Получение Chat ID для Telegram

Если вы не знаете свой Chat ID:

1. **Вариант 1**: Через бота @userinfobot
   - Отправьте `/start` боту @userinfobot
   - Он покажет ваш Chat ID

2. **Вариант 2**: Автоматически (бот определит сам)
   - Оставьте `TELEGRAM_CHAT_ID` пустым
   - Отправьте `/start` вашему боту @umartaufabot
   - Бот автоматически определит ваш Chat ID при первом запуске

---

## 🔒 Безопасность

**ВАЖНО**: Не коммитьте токены и Chat ID в Git!

1. Используйте переменные окружения
2. Добавьте `flight_config.py` в `.gitignore` (если храните там секреты)
3. На платформах используйте Environment Variables вместо хардкода

---

## 🆘 Помощь

Если возникли проблемы:

1. Проверьте логи на платформе
2. Убедитесь, что отправили `/start` боту в Telegram
3. Проверьте переменные окружения
4. Попробуйте локальный запуск с `--once` для отладки

---

**Рекомендую начать с GitHub Actions или Render.com - это самые простые и бесплатные варианты!**
