from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..domain import DuplicateRatingError
from ..keyboards import RATING_CODES, after_rating_keyboard, main_menu, rating_keyboard
from ..presentation import send_profile_card
from ..render import RATING_DISPLAY, RATING_SCALE_TEXT
from ..services import MogaemService

router = Router(name="browse")


@router.callback_query(F.data == "browse")
async def browse(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.user_by_telegram(callback.from_user.id)
        if user is None or not await service.profile_complete(user.id):
            await callback.answer("Сначала создай анкету через /start", show_alert=True)
            return
        candidate = await service.next_candidate(user.id)
    await callback.answer()
    if candidate is None:
        if callback.message:
            await callback.message.answer("Пока подходящие анкеты закончились. Загляни позже.", reply_markup=main_menu())
        return
    await send_profile_card(callback.bot, callback.from_user.id, candidate, reply_markup=rating_keyboard(candidate.user_id))


@router.callback_query(F.data == "rating:scale")
async def rating_scale(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(RATING_SCALE_TEXT)


@router.callback_query(F.data.startswith("rate:"))
async def rate_profile(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if not callback.data:
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некорректная кнопка", show_alert=True)
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        await callback.answer("Некорректная анкета", show_alert=True)
        return
    label = RATING_CODES.get(parts[2])
    if label is None:
        await callback.answer("Некорректная оценка", show_alert=True)
        return

    async with session_factory() as session:
        service = MogaemService(session)
        current = await service.user_by_telegram(callback.from_user.id)
        if current is None or not await service.profile_complete(current.id):
            await callback.answer("Сначала создай анкету через /start", show_alert=True)
            return
        try:
            await service.rate(current.id, target_id, label)
        except DuplicateRatingError:
            await callback.answer("Ты уже оценивал эту анкету", show_alert=True)
            return
        target_user = await service.user_by_id(target_id)
        current_view = await service.profile_view(current.id)
        reverse = await service.rating(target_id, current.id)
        reciprocal = reverse is not None

    await callback.answer(f"Оценка: {RATING_DISPLAY[label]}")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=after_rating_keyboard(target_id, reciprocal))
        except Exception:
            pass
    if target_user:
        if reciprocal:
            prefix = f"🔥 <b>{current_view.name} оценил(а) тебя: {RATING_DISPLAY[label]}</b>\nОценки теперь взаимные. Можно отправить запрос на переписку.\n\n"
            notify_markup = after_rating_keyboard(current.id, True)
        else:
            prefix = f"🔥 <b>{current_view.name} оценил(а) тебя: {RATING_DISPLAY[label]}</b>\nОцени в ответ:\n\n"
            notify_markup = rating_keyboard(current.id)
        await send_profile_card(callback.bot, target_user.telegram_id, current_view, reply_markup=notify_markup, prefix=prefix)
