from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..keyboards import city_skip_keyboard, gender_keyboard, main_menu, my_profile_keyboard, photo_done_keyboard, search_gender_keyboard
from ..presentation import send_profile_card
from ..services import MogaemService
from ..states import ProfileForm

router = Router(name="profile")


async def begin_profile(target: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProfileForm.name)
    await target.answer("Как тебя зовут? Введи имя для анкеты.")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if not message.from_user:
        return
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.ensure_user(message.from_user.id, message.from_user.username)
        if await service.profile_complete(user.id):
            await state.clear()
            await message.answer("Mogaem готов. Выбирай 👇", reply_markup=main_menu())
            return
    await begin_profile(message, state)


@router.callback_query(F.data == "profile:recreate")
async def recreate_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await begin_profile(callback.message, state)


@router.message(ProfileForm.name, F.text)
async def profile_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 40:
        await message.answer("Имя должно быть от 2 до 40 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(ProfileForm.age)
    await message.answer("Сколько тебе лет? Только 18+.")


@router.message(ProfileForm.age, F.text)
async def profile_age(message: Message, state: FSMContext) -> None:
    try:
        age = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введи возраст числом.")
        return
    if not 18 <= age <= 99:
        await message.answer("Сервис сейчас только для 18+. Введи возраст от 18 до 99.")
        return
    await state.update_data(age=age)
    await state.set_state(ProfileForm.gender)
    await message.answer("Твой пол?", reply_markup=gender_keyboard("onb:gender"))


@router.callback_query(ProfileForm.gender, F.data.startswith("onb:gender:"))
async def profile_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.rsplit(":", 1)[-1] if callback.data else ""
    if gender not in {"male", "female"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    await state.update_data(gender=gender)
    await state.set_state(ProfileForm.city)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Город? Можно пропустить.", reply_markup=city_skip_keyboard())


@router.message(ProfileForm.city, F.text)
async def profile_city(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if len(city) > 80:
        await message.answer("Слишком длинное название города.")
        return
    await state.update_data(city=city or None)
    await state.set_state(ProfileForm.bio)
    await message.answer("Коротко о себе (до 500 символов). Можно написать «-», если без описания.")


@router.callback_query(ProfileForm.city, F.data == "onb:city:skip")
async def profile_city_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(city=None)
    await state.set_state(ProfileForm.bio)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Коротко о себе (до 500 символов). Можно написать «-», если без описания.")


@router.message(ProfileForm.bio, F.text)
async def profile_bio(message: Message, state: FSMContext) -> None:
    bio = (message.text or "").strip()
    if len(bio) > 500:
        await message.answer("Описание максимум 500 символов.")
        return
    if bio == "-":
        bio = ""
    await state.update_data(bio=bio, photos=[])
    await state.set_state(ProfileForm.photos)
    await message.answer("Отправь 1–3 фотографии. После первой появится кнопка «Готово».")


@router.message(ProfileForm.photos, F.photo)
async def profile_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = list(data.get("photos", []))
    if len(photos) >= 3:
        await message.answer("Уже 3 фото. Нажми «Готово».", reply_markup=photo_done_keyboard())
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) == 3:
        await state.set_state(ProfileForm.search_gender)
        await message.answer("Кого показывать в поиске?", reply_markup=search_gender_keyboard("onb:search"))
    else:
        await message.answer(f"Фото {len(photos)}/3 добавлено. Можешь отправить ещё или закончить.", reply_markup=photo_done_keyboard())


@router.callback_query(ProfileForm.photos, F.data == "onb:photos:done")
async def profile_photos_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("photos"):
        await callback.answer("Нужно хотя бы одно фото", show_alert=True)
        return
    await state.set_state(ProfileForm.search_gender)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Кого показывать в поиске?", reply_markup=search_gender_keyboard("onb:search"))


@router.callback_query(ProfileForm.search_gender, F.data.startswith("onb:search:"))
async def profile_search_gender(callback: CallbackQuery, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]) -> None:
    search_gender = callback.data.rsplit(":", 1)[-1] if callback.data else ""
    if search_gender not in {"male", "female", "any"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    data = await state.get_data()
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.ensure_user(callback.from_user.id, callback.from_user.username)
        await service.save_profile(
            user.id,
            name=data["name"],
            age=int(data["age"]),
            gender=data["gender"],
            search_gender=search_gender,
            city=data.get("city"),
            bio=data.get("bio", ""),
            photos=list(data["photos"]),
        )
    await state.clear()
    await callback.answer("Анкета создана")
    if callback.message:
        await callback.message.answer("Готово. Теперь можно могать 👇", reply_markup=main_menu())


@router.callback_query(F.data == "profile:me")
async def my_profile(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.user_by_telegram(callback.from_user.id)
        if user is None or not await service.profile_complete(user.id):
            await callback.answer("Сначала создай анкету через /start", show_alert=True)
            return
        view = await service.profile_view(user.id)
    await callback.answer()
    await send_profile_card(callback.bot, callback.from_user.id, view, reply_markup=my_profile_keyboard(), prefix="<b>Твоя анкета</b>\n\n")


@router.callback_query(F.data == "search:menu")
async def search_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer("Кого показывать?", reply_markup=search_gender_keyboard())


@router.callback_query(F.data.startswith("search:set:"))
async def search_set(callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]) -> None:
    value = callback.data.rsplit(":", 1)[-1] if callback.data else ""
    if value not in {"male", "female", "any"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.user_by_telegram(callback.from_user.id)
        if user is None:
            await callback.answer("Сначала /start", show_alert=True)
            return
        await service.set_search_gender(user.id, value)
    await callback.answer("Настройка сохранена")
    if callback.message:
        await callback.message.answer("Пол поиска обновлён.", reply_markup=main_menu())
