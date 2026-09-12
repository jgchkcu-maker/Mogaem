from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..domain import DuplicateChatRequestError, ReciprocalRatingRequired
from ..keyboards import main_menu, request_decision_keyboard
from ..presentation import send_profile_card
from ..render import contact_html, rating_summary
from ..services import MogaemService, RequestStateError

router = Router(name="requests")


@router.callback_query(F.data.startswith("chatreq:"))
async def create_request(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    try:
        recipient_id = int((callback.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Некорректный запрос", show_alert=True)
        return
    async with session_factory() as session:
        service = MogaemService(session)
        requester = await service.user_by_telegram(callback.from_user.id)
        if requester is None:
            await callback.answer("Сначала /start", show_alert=True)
            return
        try:
            request = await service.create_chat_request(requester.id, recipient_id)
        except ReciprocalRatingRequired:
            await callback.answer("Сначала вы должны оценить друг друга", show_alert=True)
            return
        except DuplicateChatRequestError:
            await callback.answer("Между вами уже есть активный запрос", show_alert=True)
            return
        requester_view = await service.profile_view(requester.id)
        recipient_view = await service.profile_view(recipient_id)
        requester_to_recipient, recipient_to_requester = await service.pair_ratings(requester.id, recipient_id)

    await callback.answer("Запрос отправлен")
    if callback.message:
        await callback.message.answer("Запрос на переписку отправлен ✅", reply_markup=main_menu())
    summary = rating_summary(
        other_name=requester_view.name,
        they_gave=requester_to_recipient.label,
        you_gave=recipient_to_requester.label,
    )
    await send_profile_card(
        callback.bot,
        recipient_view.telegram_id,
        requester_view,
        reply_markup=request_decision_keyboard(request.id),
        prefix=f"💬 <b>Запрос на переписку</b>\n{summary}\n\n",
    )


@router.callback_query(F.data.startswith("req:accept:") | F.data.startswith("req:decline:"))
async def resolve_request(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Некорректный запрос", show_alert=True)
        return
    accept = parts[1] == "accept"
    try:
        request_id = int(parts[2])
    except ValueError:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    async with session_factory() as session:
        service = MogaemService(session)
        actor = await service.user_by_telegram(callback.from_user.id)
        if actor is None:
            await callback.answer("Сначала /start", show_alert=True)
            return
        try:
            request, _ = await service.resolve_chat_request(request_id, actor.id, accept=accept)
        except RequestStateError as exc:
            await callback.answer(str(exc), show_alert=True)
            return
        requester_user = await service.user_by_id(request.requester_id)
        recipient_user = await service.user_by_id(request.recipient_id)
        requester_view = await service.profile_view(request.requester_id)
        recipient_view = await service.profile_view(request.recipient_id)

    if not requester_user or not recipient_user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    if not accept:
        await callback.answer("Запрос отклонён")
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer("Запрос отклонён.", reply_markup=main_menu())
        await callback.bot.send_message(requester_user.telegram_id, "Запрос на переписку отклонён.", reply_markup=main_menu())
        return

    await callback.answer("Мэтч!")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    requester_contact = contact_html(recipient_view.name, recipient_user.username, recipient_user.telegram_id)
    recipient_contact = contact_html(requester_view.name, requester_user.username, requester_user.telegram_id)
    await callback.bot.send_message(requester_user.telegram_id, f"🎉 <b>Запрос принят!</b>\nМожно написать: {requester_contact}", reply_markup=main_menu())
    await callback.bot.send_message(recipient_user.telegram_id, f"🎉 <b>Мэтч!</b>\nМожно написать: {recipient_contact}", reply_markup=main_menu())
