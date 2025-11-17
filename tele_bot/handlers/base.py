from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.main import get_role_keyboard, choose_of_action_admin
from core.states import RegisterStates, DownloadSchedule
from services.api_client import APIClient
class BaseHandlers:
	def __init__(self, dp, states, api_client):
		self.dp = dp
		self.states = states
		self.api_client = api_client

	def register_user(self):
		@self.dp.message(Command("start"))
		async def start_handler(message: types.Message, state: FSMContext):
			keyboard_user = get_role_keyboard()
			keyboard_admin = choose_of_action_admin()

			response = await self.api_client.check_admin(message.from_user.id)
			print(response)
			if response:
				await message.answer(
					f"👋 Добро пожаловать! Ваша роль администратор !"
					f"\nВыберите действие для работы",
					reply_markup=keyboard_admin
				)
				await state.set_state(DownloadSchedule.waitind_for_action)
			else:
				await message.answer(
					f"👋 Добро пожаловать! Выберите вашу роль",
					reply_markup=keyboard_user
				)
				await state.set_state(RegisterStates.waiting_for_role)
