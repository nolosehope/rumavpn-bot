"""Клавиатуры и данные callback-кнопок."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

import config


class TariffCB(CallbackData, prefix="tariff"):
    tariff_id: str


class DeviceCB(CallbackData, prefix="dev"):
    tariff_id: str
    devices: int


class PaidCB(CallbackData, prefix="paid"):
    order_id: int
    action: str  # ok / cancel


class AdminCB(CallbackData, prefix="adm"):
    action: str  # issue / auto / reject
    order_id: int


# ---------- Пользовательские ----------

def main_menu() -> ReplyKeyboardMarkup:
    rows = []
    if config.WEBAPP_URL:
        rows.append([KeyboardButton(
            text="🛍 Магазин",
            web_app=WebAppInfo(url=config.WEBAPP_URL),
        )])
    rows.append([KeyboardButton(text="🛒 Купить VPN")])
    rows.append([KeyboardButton(text="🔑 Мои ключи"), KeyboardButton(text="📞 Поддержка")])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )


def tariffs_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{t['name']} — {t['price']} ₽ (1 устройство)",
            callback_data=TariffCB(tariff_id=t["id"]).pack(),
        )]
        for t in config.TARIFFS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def devices_kb(tariff_id: str) -> InlineKeyboardMarkup:
    tariff = next(t for t in config.TARIFFS if t["id"] == tariff_id)
    rows = []
    for opt in config.DEVICE_OPTIONS:
        total = tariff["price"] + opt["extra"]
        word = "устройство" if opt["count"] == 1 else "устройства"
        rows.append([InlineKeyboardButton(
            text=f"{opt['count']} {word} — {total} ₽",
            callback_data=DeviceCB(tariff_id=tariff_id, devices=opt["count"]).pack(),
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад к тарифам", callback_data="back:tariffs")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def paid_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Я оплатил", callback_data=PaidCB(order_id=order_id, action="ok").pack()),
        InlineKeyboardButton(text="❌ Отмена", callback_data=PaidCB(order_id=order_id, action="cancel").pack()),
    ]])


def support_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💬 Написать в поддержку", url=config.SUPPORT_URL),
    ]])


def review_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❤️ Оставить отзыв", url=config.REVIEW_URL),
    ]])


# ---------- Админские ----------

def admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выдать ключ", callback_data=AdminCB(action="issue", order_id=order_id).pack()),
            InlineKeyboardButton(text="⚡ Авто", callback_data=AdminCB(action="auto", order_id=order_id).pack()),
        ],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=AdminCB(action="reject", order_id=order_id).pack())],
    ])
