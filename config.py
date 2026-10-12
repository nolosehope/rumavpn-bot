"""Настройки бота. Всё, что помечено «.env», редактируется в файле .env,
остальное — прямо здесь."""

import os

from dotenv import load_dotenv

load_dotenv()

# ==================== Из файла .env ====================

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# ID чата админов: группа или ваш личный чат с ботом (узнать: /id)
ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0") or 0)

# Реквизиты для оплаты (в .env перенос строки задаётся как \n)
PAYMENT_REQUISITES: str = os.getenv(
    "PAYMENT_REQUISITES",
    "💳 Карта: 0000 0000 0000 0000",
).replace("\\n", "\n")

# Куда ведут кнопки «Оставить отзыв» и «Поддержка»
REVIEW_URL: str = os.getenv("REVIEW_URL", "https://t.me/ваш_канал")
SUPPORT_URL: str = os.getenv("SUPPORT_URL", "https://t.me/ваш_юзернейм")

# Ссылка на мини-приложение (после размещения на хостинге, см. README).
# Пусто — кнопка «🛍 Магазин» не показывается
WEBAPP_URL: str = os.getenv("WEBAPP_URL", "").strip()

# Прокси для доступа к Telegram API, если провайдер блокирует Telegram.
# Примеры: socks5://127.0.0.1:10808  или  http://127.0.0.1:10809
# Пусто — подключаться напрямую
PROXY_URL: str = os.getenv("PROXY_URL", "").strip()

# ==================== Общие настройки ====================

SERVICE_NAME = "РумаВПН"

# Тарифы: цена за 1 устройство за весь период
TARIFFS = [
    {"id": "m1", "name": "1 месяц", "price": 150},
    {"id": "m3", "name": "3 месяца", "price": 400},
    {"id": "m6", "name": "6 месяцев", "price": 700},
]

# Количество устройств и доплата к цене тарифа
DEVICE_OPTIONS = [
    {"count": 1, "extra": 0},
    {"count": 2, "extra": 100},
    {"count": 3, "extra": 180},
]

# Инструкция клиенту — куда вводить ключ
INSTRUCTION = (
    "1️⃣ Скачайте приложение V2rayTun (Android / iOS) или Happ\n"
    "2️⃣ Скопируйте ключ выше целиком\n"
    "3️⃣ В приложении: «+» → «Импорт из буфера обмена»\n"
    "4️⃣ Выберите сервер и нажмите «Подключить» ✅"
)
