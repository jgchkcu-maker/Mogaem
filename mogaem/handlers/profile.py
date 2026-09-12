from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..keyboards import main_menu, my_profile_keyboard, reply_keyboard, search_gender_keyboard
from ..onboarding import (
    BIO_PROMPT,
    CITY_PROMPT,
    CONFIRM_BUTTON,
    CONFIRM_ROWS,
    EDIT_BUTTON,
    FEMALE_BUTTON,
    GENDER_BY_BUTTON,
    GENDER_PROMPT,
    GENDER_ROWS,
    INTRO_TEXT,
    MALE_BUTTON,
    NAME_PROMPT,
    PHOTO_DONE_BUTTON,
    PHOTO_DONE_ROWS,
    PHOTO_PROMPT,
    PREVIEW_PROMPT,
    PREVIEW_QUESTION,
    SEARCH_GENDER_BY_BUTTON,
    SEARCH_GENDER_PROMPT,
    SEARCH_GENDER_ROWS,
    SKIP_BUTTON,
    SKIP_ROWS,
    START_BUTTON,
    START_ROWS,
    START_WARNING,
)
from ..presentation import send_profile_card
from ..render import profile_caption
from ..services import MogaemService
from ..states import ProfileForm

router = Router(name="profile")


async def begin_profile(target: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProfileForm.ready)
    await target.answer(INTRO_TEXT, reply_markup=reply_keyboard(START_ROWS))


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if not message.from_user:
        return
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.ensure_user(message.from_user.id, message.from_user.username)
        if await service.profile_complete(user.id):
            await state.clear()
            await message.answer("С возвращением 👋", reply_markup=ReplyKeyboardRemove())
            await message.answer("Выбирай, что делаем 👇", reply_markup=main_menu())
            return
    await begin_profile(message, state)


@router.callback_query(F.data == "profile:recreate")
async def recreate_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await begin_profile(callback.message, state)


@router.message(ProfileForm.ready, F.text == START_BUTTON)
async def profile_ready(message: Message, state: FSMContext) -> None:
    await state.set_state(ProfileForm.age)
    await message.answer(START_WARNING, reply_markup=ReplyKeyboardRemove())


@router.message(ProfileForm.ready)
async def profile_ready_other(message: Message) -> None:
    await message.answer("Нажми «👌 Давай начнем» 👇", reply_markup=reply_keyboard(START_ROWS))


@router.message(ProfileForm.age, F.text)
async def profile_age(message: Message, state: FSMContext) -> None:
    try:
        age = int((message.text or "").strip())
    except ValueError:
        await message.answer("Напиши возраст числом 🙂")
        return
    if not 18 <= age <= 99:
        await message.answer("Сейчас Mogaem доступен только с 18 лет. Введи возраст от 18 до 99.")
        return
    await state.update_data(age=age)
    await state.set_state(ProfileForm.gender)
    await message.answer(GENDER_PROMPT, reply_markup=reply_keyboard(GENDER_ROWS))


@router.message(ProfileForm.gender, F.text)
async def profile_gender(message: Message, state: FSMContext) -> None:
    gender = GENDER_BY_BUTTON.get((message.text or "").strip())
    if gender is None:
        await message.answer(
            f"Выбери «{MALE_BUTTON}» или «{FEMALE_BUTTON}» 👇",
            reply_markup=reply_keyboard(GENDER_ROWS),
        )
        return
    await state.update_data(gender=gender)
    await state.set_state(ProfileForm.search_gender)
    await message.answer(SEARCH_GENDER_PROMPT, reply_markup=reply_keyboard(SEARCH_GENDER_ROWS))


@router.message(ProfileForm.search_gender, F.text)
async def profile_search_gender_onboarding(message: Message, state: FSMContext) -> None:
    search_gender = SEARCH_GENDER_BY_BUTTON.get((message.text or "").strip())
    if search_gender is None:
        await message.answer("Выбери один из вариантов кнопками 👇", reply_markup=reply_keyboard(SEARCH_GENDER_ROWS))
        return
    await state.update_data(search_gender=search_gender)
    await state.set_state(ProfileForm.city)
    await message.answer(CITY_PROMPT, reply_markup=reply_keyboard(SKIP_ROWS))


@router.message(ProfileForm.city, F.text)
async def profile_city(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    city = None if raw == SKIP_BUTTON else raw
    if city and len(city) > 80:
        await message.answer("Название города слишком длинное. Напиши покороче или нажми «Пропустить».")
        return
    await state.update_data(city=city)
    await state.set_state(ProfileForm.name)
    await message.answer(NAME_PROMPT, reply_markup=ReplyKeyboardRemove())


@router.message(ProfileForm.name, F.text)
async def profile_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 40:
        await message.answer("Имя должно быть от 2 до 40 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(ProfileForm.bio)
    await message.answer(BIO_PROMPT, reply_markup=reply_keyboard(SKIP_ROWS))


@router.message(ProfileForm.bio, F.text)
async def profile_bio(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    bio = "" if raw == SKIP_BUTTON else raw
    if len(bio) > 500:
        await message.answer("Описание максимум 500 символов.")
        return
    await state.update_data(bio=bio, photos=[])
    await state.set_state(ProfileForm.photos)
    await message.answer(PHOTO_PROMPT, reply_markup=ReplyKeyboardRemove())


async def show_preview(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = list(data.get("photos", []))
    if not photos:
        await message.answer("Сначала добавь хотя бы одно фото.")
        return

    caption = profile_caption(
        name=str(data["name"]),
        age=int(data["age"]),
        city=data.get("city"),
        bio=str(data.get("bio", "")),
        gender=str(data["gender"]),
    )
    await state.set_state(ProfileForm.preview)
    await message.answer(PREVIEW_PROMPT, reply_markup=ReplyKeyboardRemove())
    if len(photos) == 1:
        await message.answer_photo(photo=photos[0], caption=caption)
    else:
        media = [
            InputMediaPhoto(media=file_id, caption=caption if index == 0 else None)
            for index, file_id in enumerate(photos)
        ]
        await message.answer_media_group(media)
    await message.answer(PREVIEW_QUESTION, reply_markup=reply_keyboard(CONFIRM_ROWS))


@router.message(ProfileForm.photos, F.photo)
async def profile_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = list(data.get("photos", []))
    if len(photos) >= 3:
        await message.answer("Уже добавлено 3 фото. Нажми «✅ Готово».", reply_markup=reply_keyboard(PHOTO_DONE_ROWS))
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) == 3:
        await show_preview(message, state)
        return
    await message.answer(
        f"Фото {len(photos)}/3 добавлено. Можешь отправить ещё или закончить.",
        reply_markup=reply_keyboard(PHOTO_DONE_ROWS),
    )


@router.message(ProfileForm.photos, F.text == PHOTO_DONE_BUTTON)
async def profile_photos_done(message: Message, state: FSMContext) -> None:
    await show_preview(message, state)


@router.message(ProfileForm.photos)
async def profile_photos_other(message: Message) -> None:
    await message.answer("Пришли фотографию. После первого фото можно будет нажать «✅ Готово».")


@router.message(ProfileForm.preview, F.text == EDIT_BUTTON)
async def profile_preview_edit(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProfileForm.age)
    await message.answer("Хорошо, заполним заново.\n\nСколько тебе лет?", reply_markup=ReplyKeyboardRemove())


@router.message(ProfileForm.preview, F.text == CONFIRM_BUTTON)
async def profile_preview_confirm(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user:
        return
    data = await state.get_data()
    async with session_factory() as session:
        service = MogaemService(session)
        user = await service.ensure_user(message.from_user.id, message.from_user.username)
        await service.save_profile(
            user.id,
            name=str(data["name"]),
            age=int(data["age"]),
            gender=str(data["gender"]),
            search_gender=str(data["search_gender"]),
            city=data.get("city"),
            bio=str(data.get("bio", "")),
            photos=list(data["photos"]),
        )
    await state.clear()
    await message.answer("Готово ✅ Анкета сохранена.", reply_markup=ReplyKeyboardRemove())
    await message.answer("Теперь можно смотреть и оценивать анкеты 👇", reply_markup=main_menu())


@router.message(ProfileForm.preview)
async def profile_preview_other(message: Message) -> None:
    await message.answer("Всё верно? Выбери кнопку снизу 👇", reply_markup=reply_keyboard(CONFIRM_ROWS))


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
