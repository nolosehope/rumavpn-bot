"""Все тексты сообщений бота — правьте свободно, на логику не влияет."""

from html import escape

import config


def start_text(name: str) -> str:
    lines = [
        f"👋 Привет, <b>{name}</b>!",
        "",
        f"Добро пожаловать в бот <b>{config.SERVICE_NAME}</b> — быстрый и безопасный VPN.",
        "",
    ]
    if config.WEBAPP_URL:
        lines.append("🛍 <b>Магазин</b> — оформить подписку в один клик")
    lines += [
        "🛒 <b>Купить VPN</b> — выбрать тариф и оформить доступ",
        "🔑 <b>Мои ключи</b> — ваши выданные ключи",
        "📞 <b>Поддержка</b> — мы всегда на связи",
        "",
        "Выберите действие кнопкой ниже 👇",
    ]
    return "\n".join(lines)


CHOOSE_TARIFF = "🛒 <b>Выберите тариф:</b>"


def choose_devices_text(tariff_name: str) -> str:
    return (
        f"📦 Тариф: <b>{escape(tariff_name)}</b>\n\n"
        "Теперь выберите, на сколько устройств нужен доступ:"
    )


def payment_text(order_id: int, tariff_name: str, devices: int, amount: int) -> str:
    return (
        f"🧾 <b>Заказ №{order_id}</b>\n\n"
        f"📦 Тариф: <b>{escape(tariff_name)}</b>\n"
        f"📱 Устройств: <b>{devices}</b>\n"
        f"💰 К оплате: <b>{amount} ₽</b>\n\n"
        f"{config.PAYMENT_REQUISITES}\n\n"
        f"📌 В комментарии к переводу укажите номер заказа: <b>#{order_id}</b>\n\n"
        "После перевода нажмите кнопку ниже 👇"
    )


ORDER_SENT = (
    "📋 <b>Ваша заявка отправлена!</b>\n\n"
    "Администратор проверит оплату, свяжется с вами и выдаст доступ 🙌"
)

ORDER_CANCELLED = "❌ Заказ отменён. Если что — оформите новый через «🛒 Купить VPN»."

NO_KEYS = "У вас пока нет ключей 🙈\nОформите подписку через «🛒 Купить VPN»."


def my_keys_text(rows) -> str:
    lines = ["🔑 <b>Ваши ключи:</b>\n"]
    for r in rows:
        lines.append(
            f"🗓 {r['issued_at']} • {escape(r['tariff'])}, {r['devices']} устр.\n"
            f"<code>{escape(r['key'])}</code>\n"
        )
    return "\n".join(lines)


UNKNOWN = "Не понял 🙈 Используйте кнопки меню ниже."


def admin_order_text(order) -> str:
    uname = f"@{order['username']}" if order["username"] else "нет username"
    return (
        f"🆕 <b>Новая заявка №{order['id']}</b>\n\n"
        f"👤 Клиент: {uname} (ID <code>{order['user_id']}</code>)\n"
        f"📦 Тариф: <b>{escape(order['tariff'])}</b>\n"
        f"📱 Устройств: <b>{order['devices']}</b>\n"
        f"💰 Сумма: <b>{order['amount']} ₽</b>\n"
        f"🕒 {order['created_at']}\n\n"
        "Проверьте оплату и выберите действие 👇"
    )


def access_granted_text(order, key: str) -> str:
    return (
        "🎉 <b>Доступ выдан!</b>\n\n"
        f"🔑 Ваш ключ:\n<code>{escape(key)}</code>\n\n"
        f"📥 <b>Как подключить:</b>\n{config.INSTRUCTION}\n\n"
        f"🙏 Спасибо за заказ в {config.SERVICE_NAME}!\n"
        "Будем рады, если оставите нам отзыв ❤️"
    )


def reject_text(order) -> str:
    return (
        f"❌ Заявка №{order['id']}: оплата не найдена.\n\n"
        "Если вы оплачивали — напишите в поддержку, разберёмся 🙏"
    )
