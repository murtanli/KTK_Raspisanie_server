from aiogram import types
from aiogram.fsm.context import FSMContext
from core.states import RegisterStates
from keyboards.main import choose_of_action_user
from datetime import date
class RegistrationHandler:
	def __init__(self, dp, states, api_client):
		self.dp = dp
		self.states = states
		self.api_client = api_client


	def register_handler(self):
		@self.dp.message(self.states.waiting_for_role)
		async def role_handler(message: types.Message, state: FSMContext):
			role_text = message.text.strip()

			if role_text == "🎓 Студент":
				await state.update_data(role='student')
				await message.answer(
					"📚 Вы выбрали роль студента. Теперь введите номер вашей группы:",
					reply_markup=types.ReplyKeyboardRemove()
				)
				await state.set_state(RegisterStates.waiting_for_group)

			elif role_text == "👨‍🏫 Преподаватель":
				await state.update_data(role='teacher')
				await message.answer(
					"👨‍🏫 Вы выбрали роль преподавателя. Теперь введите вашу фамилию и имя:",
					reply_markup=types.ReplyKeyboardRemove()
				)
				await state.set_state(RegisterStates.waiting_for_teacher_name)

			else:
				await message.answer("❌ Пожалуйста, выберите роль из предложенных вариантов.")

		@self.dp.message(RegisterStates.waiting_for_group)
		async def group_handler(message: types.Message, state: FSMContext):
			group_name = message.text.strip()
			user_data = await state.get_data()

			api_response = await self.api_client.register_user(
				telegram_id=message.from_user.id,
				username=message.from_user.username,
				user_type=user_data['role'],
				group_name=group_name
			)
			if api_response:
				await message.answer(
					f"✅ Регистрация завершена!\n"
					f"👨‍🏫 Роль: Студент\n"
					f"📝 ФИО: {group_name}\n\n"
					f"Теперь вы будете получать уведомления о расписании.",
					reply_markup=choose_of_action_user()
				)
				await state.clear()
			else:
				await message.answer(f"❌ Группа '{group_name}' не найдена. Проверьте правильность ввода.")
				return


		@self.dp.message(RegisterStates.waiting_for_teacher_name)
		async def teacher_name_handler(message: types.Message, state: FSMContext):
			teacher_name = message.text.strip()
			user_data = await state.get_data()

			# Регистрируем пользователя через API
			api_response = await self.api_client.register_user(
				telegram_id=message.from_user.id,
				username = message.from_user.username,
				user_type=user_data['role'],
				teacher_name=teacher_name
			)

			if api_response:
				await message.answer(
					f"✅ Регистрация завершена!\n"
					f"👨‍🏫 Роль: Преподаватель\n"
					f"📝 ФИО: {teacher_name}\n\n"
					f"Теперь вы будете получать уведомления о расписании.",
					reply_markup=choose_of_action_user()
				)
				await state.clear()
			else:
				await message.answer(f"❌ Фио '{teacher_name}' не найден. Проверьте правильность ввода.")

			await state.clear()
