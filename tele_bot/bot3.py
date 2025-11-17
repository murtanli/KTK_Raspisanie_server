from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN, API_URL
import asyncio
import requests




class UserStates(StatesGroup):
	waiting_for_role = State()
	waiting_for_group = State()
	waiting_for_teacher_name = State()


class Bot:
	def __init__(self):
		self.bot_token = BOT_TOKEN
		self.bot = TgBot(token=self.bot_token)
		self.dp = Dispatcher(storage=MemoryStorage())
		self.register_handlers()

	def register_handlers(self):
		@self.dp.message(Command("start"))
		async def start_handler(message: Message, state: FSMContext):
			# Создаем клавиатуру для выбора роли
			keyboard = ReplyKeyboardMarkup(
				keyboard=[
					[KeyboardButton(text="🎓 Студент"), KeyboardButton(text="👨‍🏫 Преподаватель")]
				],
				resize_keyboard=True,
				one_time_keyboard=True
			)

			await message.answer(
				f"👋 Добро пожаловать! Выберите вашу роль: {message.from_user.id}  {message.from_user.username}",
				reply_markup=keyboard
			)
			await state.set_state(UserStates.waiting_for_role)

		@self.dp.message(UserStates.waiting_for_role)
		async def role_handler(message: Message, state: FSMContext):
			role_text = message.text.strip()

			if role_text == "🎓 Студент":
				await state.update_data(role='student')
				await message.answer(
					"📚 Вы выбрали роль студента. Теперь введите номер вашей группы:",
					reply_markup=types.ReplyKeyboardRemove()
				)
				await state.set_state(UserStates.waiting_for_group)

			elif role_text == "👨‍🏫 Преподаватель":
				await state.update_data(role='teacher')
				await message.answer(
					"👨‍🏫 Вы выбрали роль преподавателя. Теперь введите вашу фамилию и имя:",
					reply_markup=types.ReplyKeyboardRemove()
				)
				await state.set_state(UserStates.waiting_for_teacher_name)

			else:
				await message.answer("❌ Пожалуйста, выберите роль из предложенных вариантов.")

		@self.dp.message(UserStates.waiting_for_group)
		async def group_handler(message: Message, state: FSMContext):
			group_name = message.text.strip()
			user_data = await state.get_data()

			group_exists = await self.check_group_exists(group_name)

			if not group_exists:
				await message.answer(f"❌ Группа '{group_name}' не найдена. Проверьте правильность ввода.")
				return

			await message.delete()

			# Регистрируем пользователя через API
			success = await self.register_user(
				telegram_id=message.from_user.id,
				username=message.from_user.username,
				first_name=message.from_user.first_name,
				user_type=user_data['role'],
				group_name=group_name
			)

			if success:
				await message.answer(
					f"✅ Регистрация завершена!\n"
					f"🎓 Роль: Студент\n"
					f"📚 Группа: {group_name}\n\n"
					f"Теперь вы будете получать уведомления о расписании."
				)
			else:
				await message.answer("❌ Ошибка при регистрации. Попробуйте позже.")

			await state.clear()

		@self.dp.message(UserStates.waiting_for_teacher_name)
		async def teacher_name_handler(message: Message, state: FSMContext):
			teacher_name = message.text.strip()
			user_data = await state.get_data()
			# Проверяем существование преподавателя через API
			teacher_exists = await self.check_teacher_exists(teacher_name)
			if not teacher_exists:
				await message.answer(f"❌ Преподаватель '{teacher_name}' не найден. Проверьте правильность ввода.")
				return

			# Регистрируем пользователя через API
			success = await self.register_user(
				telegram_id=message.from_user.id,
				username=message.from_user.username,
				first_name=message.from_user.first_name,
				user_type=user_data['role'],
				teacher_name=teacher_name
			)

			if success:
				await message.answer(
					f"✅ Регистрация завершена!\n"
					f"👨‍🏫 Роль: Преподаватель\n"
					f"📝 ФИО: {teacher_name}\n\n"
					f"Теперь вы будете получать уведомления о расписании."
				)
			else:
				await message.answer("❌ Ошибка при регистрации. Попробуйте позже.")

			await state.clear()

	async def check_group_exists(self, group_name: str) -> bool:
		"""Проверяет существование группы через API"""
		try:
			response = requests.get(f"{API_URL}/schedule/group/{group_name}/")
			return response.status_code == 200
		except Exception as e:
			print(f"Error checking group: {e}")
			return False

	async def check_teacher_exists(self, teacher_name: str) -> bool:
		"""Проверяет существование преподавателя через API"""
		try:
			response = requests.get(f"{API_URL}/api/users/teacher/{teacher_name}/")
			return response.text
			# return response.status_code == 200
		except Exception as e:
			print(f"Error checking teacher: {e}")
			return False

	async def register_user(self, telegram_id: int, username: str, first_name: str,
							user_type: str, group_name: str = None, teacher_name: str = None) -> bool:
		"""Регистрирует пользователя через API"""
		try:
			data = {
				'telegram_id': telegram_id,
				'username': username,
				'first_name': first_name,
				'user_type': user_type,
			}

			# Добавляем специфичные данные в зависимости от роли
			if user_type == 'student' and group_name:
				data['group_name'] = group_name
			elif user_type == 'teacher' and teacher_name:
				data['teacher_name'] = teacher_name

			response = requests.post(f"{API_URL}/users/register/", json=data)
			return response.status_code == 200 or response.status_code == 201

		except Exception as e:
			print(f"Error registering user: {e}")
			return False

	async def start_bot(self):
		await self.dp.start_polling(self.bot)


if __name__ == "__main__":
	print("Запуск бота")
	bot = Bot()
	asyncio.run(bot.start_bot())