"""Пользовательский флоу: меню → тариф → устройства → оплата → «Я оплатил»."""

import json
import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

import config
import db
import keyboards as kb
import texts
from handlers_admin import notify_admin

router = Router()

# Пользовательский флоу работает только в личке (в админ-группе бот молчит)
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        texts.start_text(escape(message.from_user.full_name)),
        reply_markup=kb.main_menu(),
    )


@router.message(F.text == "🛒 Купить VPN")
async def show_tariffs(message: Message) -> None:
    await message.answer(texts.CHOOSE_TARIFF, reply_markup=kb.tariffs_kb())


@router.message(F.text == "🔑 Мои ключи")
async def my_keys(message: Message) -> None:
    rows = db.get_user_keys(message.from_user.id)
    if not rows:
        await message.answer(texts.NO_KEYS)
        return
    await message.answer(texts.my_keys_text(rows))


@router.message(F.text == "📞 Поддержка")
async def support(message: Message) -> None:
    await message.answer("💬 Есть вопрос или проблема? Напишите нам 👇", reply_markup=kb.support_kb())


# ---------- Выбор тарифа и устройств ----------

@router.callback_query(kb.TariffCB.filter())
async def tariff_chosen(cb: CallbackQuery, callback_data: kb.TariffCB) -> None:
    tariff = next((t for t in config.TARIFFS if t["id"] == callback_data.tariff_id), None)
    if tariff is None or cb.message is None:
        await cb.answer("Тариф не найден", show_alert=True)
        return
    await cb.message.edit_text(texts.choose_devices_text(tariff["name"]), reply_markup=kb.devices_kb(tariff["id"]))
    await cb.answer()


@router.callback_query(F.data == "back:tariffs")
async def back_to_tariffs(cb: CallbackQuery) -> None:
    if cb.message is None:
        await cb.answer()
        return
    await cb.message.edit_text(texts.CHOOSE_TARIFF, reply_markup=kb.tariffs_kb())
    await cb.answer()


def _tariff_and_option(tariff_id: str, devices: int):
    tariff = next((t for t in config.TARIFFS if t["id"] == tariff_id), None)
    opt = next((o for o in config.DEVICE_OPTIONS if o["count"] == devices), None)
    return tariff, opt


@router.callback_query(kb.DeviceCB.filter())
async def device_chosen(cb: CallbackQuery, callback_data: kb.DeviceCB) -> None:
    tariff, opt = _tariff_and_option(callback_data.tariff_id, callback_data.devices)
    if tariff is None or opt is None or cb.message is None:
        await cb.answer("Ошибка, попробуйте заново", show_alert=True)
        return
    amount = tariff["price"] + opt["extra"]
    order_id = db.create_order(
        user_id=cb.from_user.id,
        username=cb.from_user.username,
        full_name=cb.from_user.full_name,
        tariff=tariff["name"],
        devices=opt["count"],
        amount=amount,
    )
    await cb.message.edit_text(
        texts.payment_text(order_id, tariff["name"], opt["count"], amount),
        reply_markup=kb.paid_kb(order_id),
    )
    await cb.answer()


# ---------- Заказ из мини-приложения ----------

@router.message(F.web_app_data)
async def webapp_order(message: Message) -> None:
    """Мини-апп прислал выбор: {"t": tariff_id, "d": devices}."""
    try:
        data = json.loads(message.web_app_data.data)
        tariff, opt = _tariff_and_option(str(data.get("t", "")), int(data.get("d", 0)))
    except (ValueError, TypeError):
        tariff, opt = None, None
    if tariff is None or opt is None or message.from_user is None:
        await message.answer("Не удалось оформить заказ 🙈 Попробуйте ещё раз в магазине.")
        return
    amount = tariff["price"] + opt["extra"]
    order_id = db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        tariff=tariff["name"],
        devices=opt["count"],
        amount=amount,
    )
    await message.answer(
        texts.payment_text(order_id, tariff["name"], opt["count"], amount),
        reply_markup=kb.paid_kb(order_id),
    )


# ---------- «Я оплатил» / отмена ----------

@router.callback_query(kb.PaidCB.filter(F.action == "ok"))
async def paid_pressed(cb: CallbackQuery, callback_data: kb.PaidCB) -> None:
    order = db.get_order(callback_data.order_id)
    if not order or order["user_id"] != cb.from_user.id or cb.message is None:
        await cb.answer("Заявка не найдена", show_alert=True)
        return
    if order["status"] != "created":
        await cb.answer("Эта заявка уже отправлена ✅", show_alert=True)
        return

    db.set_order_status(order["id"], "paid")

    # Экран оплаты остаётся с реквизитами, но кнопки убираем и ставим отметку
    try:
        await cb.message.edit_text(
            cb.message.html_text + "\n\n✅ <b>Заявка отправлена</b>",
            reply_markup=None,
        )
    except Exception:
        logging.exception("Не удалось обновить экран оплаты")

    await cb.message.answer(texts.ORDER_SENT)

    sent = await notify_admin(cb.bot, order)
    if not sent:
        await cb.answer("⚠️ Админы не настроены (ADMIN_CHAT_ID)", show_alert=True)
    else:
        await cb.answer("Заявка отправлена ✅")


@router.callback_query(kb.PaidCB.filter(F.action == "cancel"))
async def cancel_pressed(cb: CallbackQuery, callback_data: kb.PaidCB) -> None:
    order = db.get_order(callback_data.order_id)
    if order and order["user_id"] == cb.from_user.id and order["status"] == "created" and cb.message:
        db.set_order_status(order["id"], "cancelled")
        await cb.message.edit_text(texts.ORDER_CANCELLED, reply_markup=None)
    await cb.answer()


# ---------- Фолбэк ----------

@router.message(F.text)
async def unknown(message: Message) -> None:
    await message.answer(texts.UNKNOWN)
