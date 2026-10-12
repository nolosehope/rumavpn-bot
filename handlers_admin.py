"""Админский флоу: карточки заявок в админ-чате и выдача ключей.

Ключи можно выдавать двумя способами:
  ✅ «Выдать ключ» — админ присылает ключ текстом, бот доставит клиенту;
  ⚡ «Авто» — бот берёт первый ключ из файла keys.txt (по одному в строке).
"""

import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import config
import db
import keyboards as kb
import texts

router = Router()

KEYS_FILE = Path("keys.txt")


class AdminFSM(StatesGroup):
    waiting_key = State()


# ---------- Пул ключей для автовыдачи ----------

def peek_key() -> str | None:
    if not KEYS_FILE.exists():
        return None
    lines = [ln.strip() for ln in KEYS_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return lines[0] if lines else None


def drop_first_key() -> None:
    lines = [ln.strip() for ln in KEYS_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rest = lines[1:]
    KEYS_FILE.write_text("\n".join(rest) + ("\n" if rest else ""), encoding="utf-8")


# ---------- Уведомление админов о новой заявке ----------

async def notify_admin(bot: Bot, order) -> bool:
    if not config.ADMIN_CHAT_ID:
        logging.error("ADMIN_CHAT_ID не задан — заявка №%s не доставлена админам", order["id"])
        return False
    try:
        await bot.send_message(
            config.ADMIN_CHAT_ID,
            texts.admin_order_text(order),
            reply_markup=kb.admin_order_kb(order["id"]),
        )
        return True
    except Exception:
        logging.exception("Не удалось отправить заявку №%s админам", order["id"])
        return False


async def deliver_key(bot: Bot, order, key: str) -> bool:
    """Отправить клиенту ключ + инструкцию + благодарность. True — если доставлено."""
    try:
        await bot.send_message(
            order["user_id"],
            texts.access_granted_text(order, key),
            reply_markup=kb.review_kb(),
        )
    except Exception:
        logging.exception("Ключ клиенту %s не доставлен", order["user_id"])
        return False
    db.set_order_status(order["id"], "issued")
    db.add_issued_key(order["user_id"], key, order["tariff"], order["devices"])
    return True


async def finish_card(message: Message, status_line: str) -> None:
    """Пометить карточку заявки обработанной (убрать кнопки, дописать статус)."""
    try:
        await message.edit_text(message.html_text + f"\n\n{status_line}", reply_markup=None)
    except Exception:
        logging.exception("Не удалось обновить карточку заявки")


# ---------- /id — узнать chat_id для настройки ----------

@router.message(Command("id"))
async def chat_id(message: Message) -> None:
    await message.answer(f"ID этого чата: <code>{message.chat.id}</code>")


# ---------- Кнопки на карточке заявки ----------

@router.callback_query(kb.AdminCB.filter(F.action == "issue"))
async def issue_start(cb: CallbackQuery, callback_data: kb.AdminCB, state: FSMContext) -> None:
    order = db.get_order(callback_data.order_id)
    if not order or order["status"] != "paid" or cb.message is None:
        await cb.answer("Заявка уже обработана", show_alert=True)
        return
    await state.set_state(AdminFSM.waiting_key)
    await state.update_data(
        order_id=order["id"],
        card_chat=cb.message.chat.id,
        card_msg=cb.message.message_id,
    )
    await cb.message.answer(
        f"🔑 Пришлите ключ для заявки №{order['id']} следующим сообщением —\n"
        "я отправлю его клиенту вместе с инструкцией."
    )
    await cb.answer()


@router.message(AdminFSM.waiting_key, F.text)
async def key_received(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()

    order = db.get_order(data.get("order_id", 0))
    if not order:
        await message.answer("Заявка не найдена 🤷")
        return
    if order["status"] != "paid":
        await message.answer("Заявка уже обработана.")
        return

    key = message.text.strip()
    delivered = await deliver_key(bot, order, key)
    if delivered:
        await message.answer(f"✅ Ключ отправлен клиенту (заявка №{order['id']}).")
        try:
            await bot.edit_message_reply_markup(data["card_chat"], data["card_msg"], reply_markup=None)
        except Exception:
            logging.exception("Не удалось убрать кнопки с карточки")
    else:
        await message.answer("⚠️ Не удалось доставить клиенту (возможно, заблокировал бота) — свяжитесь с ним сами.")


@router.message(AdminFSM.waiting_key)
async def key_not_text(message: Message) -> None:
    await message.answer("Пришлите ключ текстовым сообщением 🙏")


@router.callback_query(kb.AdminCB.filter(F.action == "auto"))
async def auto_issue(cb: CallbackQuery, callback_data: kb.AdminCB) -> None:
    order = db.get_order(callback_data.order_id)
    if not order or order["status"] != "paid" or cb.message is None:
        await cb.answer("Заявка уже обработана", show_alert=True)
        return

    key = peek_key()
    if not key:
        await cb.answer(f"Пул пуст — добавьте ключи в файл {KEYS_FILE}", show_alert=True)
        return

    delivered = await deliver_key(cb.bot, order, key)
    if delivered:
        drop_first_key()
        await finish_card(cb.message, "⚡ Выдан автоключ")
        await cb.answer("Готово ✅")
    else:
        await cb.answer("Не удалось доставить клиенту", show_alert=True)


@router.callback_query(kb.AdminCB.filter(F.action == "reject"))
async def reject_order(cb: CallbackQuery, callback_data: kb.AdminCB) -> None:
    order = db.get_order(callback_data.order_id)
    if not order or order["status"] != "paid" or cb.message is None:
        await cb.answer("Заявка уже обработана", show_alert=True)
        return

    db.set_order_status(order["id"], "rejected")
    try:
        await cb.bot.send_message(order["user_id"], texts.reject_text(order))
    except Exception:
        logging.exception("Отказ не доставлен клиенту %s", order["user_id"])
    await finish_card(cb.message, "❌ Отклонена")
    await cb.answer("Отклонено")
